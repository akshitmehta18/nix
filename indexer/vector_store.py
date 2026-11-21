"""Vector store for semantic code search with ChromaDB and built-in lightweight fallback."""

import os
import re
import json
from typing import Dict, List, Optional, Any
from config import get_index_path


class VectorStore:
    """Vector store for code embeddings with ChromaDB or smart keyword/token fallback."""

    COLLECTION_NAME = "code_methods"

    def __init__(self):
        """Initialize the vector store."""
        self.index_path = get_index_path()
        self.vectors_path = os.path.join(self.index_path, "vectors")
        self.fallback_file = os.path.join(self.index_path, "methods_fallback.json")
        self._client = None
        self._collection = None
        self._fallback_methods: List[Dict[str, Any]] = []
        self._load_fallback()

    def _load_fallback(self):
        """Load fallback methods if file exists."""
        if os.path.exists(self.fallback_file):
            try:
                with open(self.fallback_file, 'r', encoding='utf-8') as f:
                    self._fallback_methods = json.load(f)
            except Exception:
                self._fallback_methods = []

    def _save_fallback(self):
        """Save fallback methods to file."""
        try:
            os.makedirs(self.index_path, exist_ok=True)
            with open(self.fallback_file, 'w', encoding='utf-8') as f:
                json.dump(self._fallback_methods, f, indent=2)
        except Exception:
            pass

    def _ensure_initialized(self) -> bool:
        """Lazy initialization of ChromaDB client."""
        if self._client is not None:
            return True

        try:
            import chromadb
            from chromadb.config import Settings

            os.makedirs(self.vectors_path, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.vectors_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Code method summaries for semantic search"}
            )
            return True
        except Exception:
            return False

    def is_available(self) -> bool:
        """Check if store is available (always True because of built-in fallback)."""
        return True

    def add_methods(self, methods: List[Dict[str, Any]]) -> bool:
        """Add method summaries to the vector store or fallback index."""
        if not methods:
            return True

        # First, update fallback storage
        existing_ids = {m.get('id') for m in self._fallback_methods}
        for method in methods:
            m_id = method.get('id', f"{method.get('class_name', 'Unknown')}.{method.get('method_name', 'unknown')}")
            method_copy = method.copy()
            method_copy['id'] = m_id
            if m_id in existing_ids:
                self._fallback_methods = [m for m in self._fallback_methods if m.get('id') != m_id]
            self._fallback_methods.append(method_copy)
        self._save_fallback()

        # Then try ChromaDB if available
        if self._ensure_initialized():
            try:
                ids = []
                documents = []
                metadatas = []

                for method in methods:
                    method_id = method.get('id', f"{method.get('class_name', 'Unknown')}.{method.get('method_name', 'unknown')}")
                    ids.append(method_id)
                    documents.append(method.get('summary', ''))
                    code = method.get('code', '')
                    if len(code) > 500:
                        code = code[:500] + '\n// ... (truncated)'

                    metadatas.append({
                        'file_path': method.get('file_path', ''),
                        'line': method.get('line', 0),
                        'class_name': method.get('class_name', ''),
                        'method_name': method.get('method_name', ''),
                        'annotations': ','.join(method.get('annotations', [])),
                        'code': code
                    })

                self._collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
            except Exception:
                pass

        return True

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for methods semantically similar to the query."""
        # Try ChromaDB first
        if self._ensure_initialized():
            try:
                results = self._collection.query(
                    query_texts=[query],
                    n_results=top_k,
                    include=['documents', 'metadatas', 'distances']
                )
                matches = []
                if results and results.get('ids') and results['ids'][0]:
                    for i, method_id in enumerate(results['ids'][0]):
                        dist = results['distances'][0][i] if results.get('distances') else 0
                        match = {
                            'id': method_id,
                            'summary': results['documents'][0][i] if results.get('documents') else '',
                            'distance': dist,
                            'relevance': max(0.0, min(1.0, 1.0 - dist)),
                        }
                        if results.get('metadatas') and results['metadatas'][0]:
                            metadata = results['metadatas'][0][i]
                            match.update({
                                'file_path': metadata.get('file_path', ''),
                                'line': metadata.get('line', 0),
                                'class_name': metadata.get('class_name', ''),
                                'method_name': metadata.get('method_name', ''),
                                'annotations': metadata.get('annotations', '').split(',') if metadata.get('annotations') else [],
                                'code': metadata.get('code', '')
                            })
                        matches.append(match)
                    if matches:
                        return matches
            except Exception:
                pass

        # Smart fallback matching
        return self._search_fallback(query, top_k)

    def _search_fallback(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Token & keyword similarity search across indexed methods."""
        if not self._fallback_methods:
            return []

        query_tokens = set(re.findall(r'\w+', query.lower()))
        scored = []

        for m in self._fallback_methods:
            score = 0
            summary = (m.get('summary') or '').lower()
            name = (m.get('method_name') or '').lower()
            cls = (m.get('class_name') or '').lower()
            code = (m.get('code') or '').lower()
            annos = ' '.join(m.get('annotations') or []).lower()

            for tok in query_tokens:
                if tok in name:
                    score += 5
                if tok in cls:
                    score += 3
                if tok in summary:
                    score += 4
                if tok in annos:
                    score += 3
                if tok in code:
                    score += 1

            if score > 0:
                rel = min(0.95, score / (len(query_tokens) * 5 + 1))
                m_copy = m.copy()
                m_copy['relevance'] = rel
                scored.append(m_copy)

        scored.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        return scored[:top_k]

    def clear(self) -> bool:
        """Clear all stored methods."""
        self._fallback_methods = []
        if os.path.exists(self.fallback_file):
            try:
                os.remove(self.fallback_file)
            except Exception:
                pass

        if self._ensure_initialized():
            try:
                self._client.delete_collection(self.COLLECTION_NAME)
                self._collection = self._client.create_collection(
                    name=self.COLLECTION_NAME,
                    metadata={"description": "Code method summaries for semantic search"}
                )
            except Exception:
                pass
        return True

    def remove_by_file(self, file_path: str) -> bool:
        """Remove methods from a specific file."""
        self._fallback_methods = [m for m in self._fallback_methods if m.get('file_path') != file_path]
        self._save_fallback()

        if self._ensure_initialized():
            try:
                results = self._collection.get(where={"file_path": file_path}, include=[])
                if results and results.get('ids'):
                    self._collection.delete(ids=results['ids'])
            except Exception:
                pass
        return True

    def get_indexed_files(self) -> set:
        """Get set of indexed file paths."""
        files = {m.get('file_path') for m in self._fallback_methods if m.get('file_path')}
        if self._ensure_initialized():
            try:
                results = self._collection.get(include=['metadatas'])
                if results and results.get('metadatas'):
                    for meta in results['metadatas']:
                        if meta.get('file_path'):
                            files.add(meta['file_path'])
            except Exception:
                pass
        return files

    def get_count(self) -> int:
        """Get count of methods in store."""
        if self._ensure_initialized():
            try:
                c = self._collection.count()
                if c > 0:
                    return c
            except Exception:
                pass
        return len(self._fallback_methods)

    def has_index(self) -> bool:
        """Check if index exists and has data."""
        return self.get_count() > 0
