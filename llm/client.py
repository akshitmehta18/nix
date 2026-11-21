"""Modern multi-provider LLM client for Nix.

Supports Groq, Google Gemini, OpenAI, Anthropic Claude, Ollama (local offline), and custom endpoints.
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from config import load_global_config, save_global_config

# Provider configurations
DEFAULT_PROVIDERS = {
    "groq": {
        "name": "Groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "default_model": "llama-3.3-70b-versatile",
        "fallback_model": "llama-3.1-8b-instant",
        "env_var": "GROQ_API_KEY",
        "requires_key": True,
        "description": "Ultra-fast inference (Llama 3.3 70B & 8B)",
        "key_url": "https://console.groq.com/keys"
    },
    "gemini": {
        "name": "Google Gemini",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "default_model": "gemini-2.5-flash",
        "fallback_model": "gemini-1.5-flash",
        "env_var": "GEMINI_API_KEY",
        "requires_key": True,
        "description": "Google Gemini 2.5/1.5 Flash (high context & accuracy)",
        "key_url": "https://aistudio.google.com/app/apikey"
    },
    "gemini_local": {
        "name": "Gemini Web2API (Local / Free)",
        "url": os.getenv("GEMINI_LOCAL_URL", "http://127.0.0.1:8081/v1/chat/completions"),
        "default_model": "gemini-2.5-flash",
        "fallback_model": "gemini-1.5-flash",
        "env_var": "GEMINI_LOCAL_API_KEY",
        "requires_key": False,
        "description": "Local Gemini Web2API endpoint (/Users/akshitmehta/gemini)",
        "key_url": "http://127.0.0.1:8081"
    },
    "openai": {
        "name": "OpenAI",
        "url": "https://api.openai.com/v1/chat/completions",
        "default_model": "gpt-4o-mini",
        "fallback_model": "gpt-4o",
        "env_var": "OPENAI_API_KEY",
        "requires_key": True,
        "description": "OpenAI GPT-4o & GPT-4o-mini",
        "key_url": "https://platform.openai.com/api-keys"
    },
    "ollama": {
        "name": "Ollama (Local / Free)",
        "url": os.getenv("OLLAMA_HOST", "http://localhost:11434/v1/chat/completions"),
        "default_model": "llama3.2",
        "fallback_model": "llama3",
        "env_var": "OLLAMA_API_KEY",
        "requires_key": False,
        "description": "100% Private, offline, free local AI (Llama 3.2, DeepSeek, etc.)",
        "key_url": "https://ollama.com"
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "url": "https://api.anthropic.com/v1/messages",
        "default_model": "claude-3-5-sonnet-20241022",
        "fallback_model": "claude-3-5-haiku-20241022",
        "env_var": "ANTHROPIC_API_KEY",
        "requires_key": True,
        "description": "Claude 3.5 Sonnet / Haiku",
        "key_url": "https://console.anthropic.com"
    }
}

CREDENTIALS_FILE = os.path.expanduser("~/.nix/credentials")
MAX_CONTEXT_TOKENS = 6000
CHARS_PER_TOKEN = 4

# Backwards compatibility constants
GROQ_API_URL = DEFAULT_PROVIDERS["groq"]["url"]
MODEL = DEFAULT_PROVIDERS["groq"]["fallback_model"]
AGENT_MODEL = DEFAULT_PROVIDERS["groq"]["default_model"]
FALLBACK_MODEL = DEFAULT_PROVIDERS["groq"]["fallback_model"]


class RateLimitExhaustedError(Exception):
    """Raised when LLM API quota or rate limit is exhausted."""
    pass


class ContextTooLargeError(Exception):
    """Raised when context exceeds model limits."""
    pass


def get_stored_config() -> dict:
    """Load global nix configuration."""
    cfg = load_global_config()
    if not isinstance(cfg, dict):
        cfg = {}
    return cfg


def get_active_provider() -> str:
    """Determine the active LLM provider."""
    # Check explicit env var
    env_provider = os.getenv("NIX_PROVIDER")
    if env_provider and env_provider.lower() in DEFAULT_PROVIDERS:
        return env_provider.lower()

    # Check stored config
    cfg = get_stored_config()
    if "provider" in cfg and cfg["provider"] in DEFAULT_PROVIDERS:
        return cfg["provider"]

    # Auto-detect from available API keys
    for prov_name, prov in DEFAULT_PROVIDERS.items():
        if prov["requires_key"] and os.getenv(prov["env_var"]):
            return prov_name

    # Auto-detect active local services (Gemini Web2API on 8081 or Ollama on 11434)
    import socket
    def _is_local_port_open(port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.15)
                return s.connect_ex(("127.0.0.1", port)) == 0
        except Exception:
            return False

    if _is_local_port_open(8081):
        return "gemini_local"

    if _is_local_port_open(11434):
        return "ollama"

    # Check legacy credentials file -> defaults to groq
    if os.path.exists(CREDENTIALS_FILE):
        return "groq"

    # Default to groq
    return "groq"


def set_active_provider(provider: str, model: Optional[str] = None):
    """Set active LLM provider and optional default model."""
    if provider not in DEFAULT_PROVIDERS:
        raise ValueError(f"Unknown provider '{provider}'. Available: {list(DEFAULT_PROVIDERS.keys())}")
    cfg = get_stored_config()
    cfg["provider"] = provider
    if model:
        cfg[f"{provider}_model"] = model
    save_global_config(cfg)


def get_api_key(provider: Optional[str] = None) -> Optional[str]:
    """Get API key for specified provider or active provider."""
    prov_name = provider or get_active_provider()
    prov_info = DEFAULT_PROVIDERS.get(prov_name, DEFAULT_PROVIDERS["groq"])

    # 1. Check environment variable
    env_key = os.getenv(prov_info.get("env_var", ""))
    if env_key:
        return env_key.strip()

    # 2. Check stored config in ~/.nix/config.json
    cfg = get_stored_config()
    keys_map = cfg.get("api_keys", {})
    if prov_name in keys_map and keys_map[prov_name]:
        return keys_map[prov_name].strip()

    # 3. For Groq, check legacy ~/.nix/credentials
    if prov_name == "groq" and os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                key = f.read().strip()
                if key:
                    return key
        except Exception:
            pass

    # 4. Ollama doesn't require a key
    if prov_name == "ollama":
        return "ollama-local"

    return None


def save_api_key(api_key: str, provider: str = "groq"):
    """Save API key for a provider."""
    provider = provider.lower()
    cfg = get_stored_config()
    if "api_keys" not in cfg:
        cfg["api_keys"] = {}
    cfg["api_keys"][provider] = api_key.strip()
    cfg["provider"] = provider
    save_global_config(cfg)

    # Legacy file sync for groq
    if provider == "groq":
        try:
            os.makedirs(os.path.dirname(CREDENTIALS_FILE), exist_ok=True)
            with open(CREDENTIALS_FILE, 'w') as f:
                f.write(api_key.strip())
            os.chmod(CREDENTIALS_FILE, 0o600)
        except Exception:
            pass


def get_active_model(provider: Optional[str] = None, use_fallback: bool = False) -> str:
    """Get active model for provider."""
    prov_name = provider or get_active_provider()
    prov_info = DEFAULT_PROVIDERS.get(prov_name, DEFAULT_PROVIDERS["groq"])

    if use_fallback:
        return prov_info.get("fallback_model", prov_info["default_model"])

    cfg = get_stored_config()
    custom_model = cfg.get(f"{prov_name}_model")
    if custom_model:
        return custom_model

    return prov_info["default_model"]


def _make_http_request(url: str, headers: dict, payload: dict, timeout: int = 60) -> dict:
    """Make HTTP POST request using requests, falling back to httpx or urllib."""
    json_data = json.dumps(payload).encode('utf-8')

    # Try requests
    try:
        import requests
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if resp.status_code == 429:
            raise RateLimitExhaustedError("Rate limit / quota exceeded (HTTP 429).")
        if resp.status_code >= 400:
            try:
                err_json = resp.json()
                msg = err_json.get("error", {}).get("message", resp.text)
            except Exception:
                msg = resp.text
            raise Exception(f"API Error ({resp.status_code}): {msg}")
        return resp.json()
    except ImportError:
        pass

    # Try httpx
    try:
        import httpx
        resp = httpx.post(url, json=payload, headers=headers, timeout=timeout)
        if resp.status_code == 429:
            raise RateLimitExhaustedError("Rate limit / quota exceeded (HTTP 429).")
        if resp.status_code >= 400:
            raise Exception(f"API Error ({resp.status_code}): {resp.text}")
        return resp.json()
    except ImportError:
        pass

    # Fallback to standard library urllib.request
    import urllib.request
    import urllib.error

    req = urllib.request.Request(url, data=json_data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise RateLimitExhaustedError("Rate limit / quota exceeded (HTTP 429).")
        err_body = e.read().decode('utf-8', errors='ignore')
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("error", {}).get("message", err_body)
        except Exception:
            msg = err_body
        raise Exception(f"API Error ({e.code}): {msg}")
    except urllib.error.URLError as e:
        raise Exception(f"Network error: {str(e.reason)}")


def estimate_tokens(text: Any) -> int:
    """Estimate token count from text."""
    if not text:
        return 0
    return len(str(text)) // CHARS_PER_TOKEN


def estimate_messages_tokens(messages: List[dict]) -> int:
    """Estimate total tokens in messages."""
    total = 0
    for msg in messages:
        total += estimate_tokens(msg.get("content", ""))
        if msg.get("tool_calls"):
            total += estimate_tokens(json.dumps(msg["tool_calls"]))
    return total


def estimate_tools_tokens(tools: Optional[List[dict]]) -> int:
    """Estimate tokens in tool definitions."""
    if not tools:
        return 0
    return estimate_tokens(json.dumps(tools))


def trim_messages_to_fit(messages: List[dict], tools: Optional[List[dict]], max_tokens: int = MAX_CONTEXT_TOKENS) -> List[dict]:
    """Trim messages to fit within token limits while preserving system instructions."""
    tools_tokens = estimate_tools_tokens(tools)
    available = max_tokens - tools_tokens - 600

    if available < 1200:
        available = 1200

    if not messages:
        return messages

    system_prompt = messages[0] if messages[0].get("role") == "system" else None
    other_messages = messages[1:] if system_prompt else messages[:]

    system_tokens = estimate_tokens(system_prompt.get("content", "")) if system_prompt else 0
    remaining = available - system_tokens

    trimmed = []
    current_tokens = 0

    for msg in reversed(other_messages):
        msg_tokens = estimate_tokens(msg.get("content", ""))
        if msg.get("tool_calls"):
            msg_tokens += estimate_tokens(json.dumps(msg["tool_calls"]))

        if current_tokens + msg_tokens <= remaining:
            trimmed.insert(0, msg)
            current_tokens += msg_tokens
        else:
            if msg.get("role") == "tool" and msg_tokens > 400:
                content = str(msg.get("content", ""))
                max_chars = int((remaining - current_tokens) * CHARS_PER_TOKEN)
                if max_chars > 200:
                    truncated = msg.copy()
                    truncated["content"] = content[:max_chars] + "...[truncated]"
                    trimmed.insert(0, truncated)
            break

    if system_prompt:
        return [system_prompt] + trimmed
    return trimmed


def call_llm(prompt: str, provider: Optional[str] = None) -> str:
    """Execute single prompt call to active or specified LLM."""
    prov_name = provider or get_active_provider()
    api_key = get_api_key(prov_name)

    prov_info = DEFAULT_PROVIDERS.get(prov_name, DEFAULT_PROVIDERS["groq"])
    if prov_info["requires_key"] and not api_key:
        raise Exception(f"No API key configured for {prov_info['name']}. Run: nix config <key> or nix config --provider {prov_name} <key>")

    url = prov_info["url"]
    model = get_active_model(prov_name)

    headers = {
        "Content-Type": "application/json"
    }
    if api_key and prov_name != "ollama":
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 1000
    }

    data = _make_http_request(url, headers, payload, timeout=45)
    return data["choices"][0]["message"]["content"]


def call_groq(prompt: str) -> str:
    """Backwards-compatible alias for call_llm."""
    return call_llm(prompt)


def call_llm_with_tools(
    messages: List[dict],
    tools: Optional[List[dict]] = None,
    retry_count: int = 0,
    use_fallback: bool = False,
    provider: Optional[str] = None
) -> dict:
    """Execute chat completion with function calling across supported LLM providers."""
    prov_name = provider or get_active_provider()
    prov_info = DEFAULT_PROVIDERS.get(prov_name, DEFAULT_PROVIDERS["groq"])
    api_key = get_api_key(prov_name)

    if prov_info["requires_key"] and not api_key:
        raise Exception(
            f"API key not configured for {prov_info['name']}.\n"
            f"Run: nix config <key> or visit {prov_info['key_url']} for a free key."
        )

    current_model = get_active_model(prov_name, use_fallback=use_fallback)
    url = prov_info["url"]

    # Pre-flight context trimming
    estimated = estimate_messages_tokens(messages) + estimate_tools_tokens(tools)
    if estimated > MAX_CONTEXT_TOKENS:
        messages = trim_messages_to_fit(messages, tools, MAX_CONTEXT_TOKENS)

    headers = {"Content-Type": "application/json"}
    if api_key and prov_name != "ollama":
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": current_model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1500
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    try:
        data = _make_http_request(url, headers, payload, timeout=60)
        choice = data["choices"][0]
        message = choice["message"]

        result = {
            "content": message.get("content"),
            "tool_calls": None,
            "finish_reason": choice.get("finish_reason")
        }

        if message.get("tool_calls"):
            result["tool_calls"] = []
            for tc in message["tool_calls"]:
                try:
                    args = json.loads(tc["function"]["arguments"])
                except Exception:
                    args = {}
                result["tool_calls"].append({
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "arguments": args
                })

        return result

    except RateLimitExhaustedError:
        if retry_count < 2:
            time.sleep(1.0 * (retry_count + 1))
            return call_llm_with_tools(messages, tools, retry_count + 1, use_fallback, provider)
        if not use_fallback:
            return call_llm_with_tools(messages, tools, 0, use_fallback=True, provider=provider)
        raise RateLimitExhaustedError(
            f"Quota or rate limit reached for {prov_info['name']} ({current_model}).\n"
            f"Check your quota or switch provider with: nix config --provider <gemini|openai|ollama>"
        )

    except Exception as e:
        err_msg = str(e)
        if "context" in err_msg.lower() or "token" in err_msg.lower():
            if retry_count < 1:
                trimmed = trim_messages_to_fit(messages, tools, MAX_CONTEXT_TOKENS // 2)
                return call_llm_with_tools(trimmed, tools, retry_count + 1, use_fallback, provider)
            raise ContextTooLargeError("Context too large. Please start a fresh conversation with 'new'.")
        raise


def call_groq_with_tools(messages, tools=None, retry_count=0, use_fallback=False):
    """Backwards-compatible wrapper for call_llm_with_tools."""
    return call_llm_with_tools(messages, tools, retry_count, use_fallback)


def check_springboot(build_file_content: str, build_type: str) -> Tuple[bool, Optional[str]]:
    """Determine if build file belongs to a Spring Boot project."""
    from llm import prompts
    prompt = prompts.get_springboot_detection_prompt(build_file_content, build_type)

    try:
        response = call_llm(prompt)
        return parse_springboot_response(response)
    except Exception as e:
        raise Exception(f"Failed to check Spring Boot: {str(e)}")


def parse_springboot_response(response: str) -> Tuple[bool, Optional[str]]:
    """Parse LLM response to extract Spring Boot detection and version."""
    import re
    resp_lower = response.lower()
    is_sb = ("yes" in resp_lower and "spring" in resp_lower) or "spring-boot" in resp_lower

    if not is_sb:
        return False, None

    version_pattern = r'\b\d+\.\d+\.\d+\b'
    matches = re.findall(version_pattern, response)
    version = matches[0] if matches else "Unknown"

    return True, version
