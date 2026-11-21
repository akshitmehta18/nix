"""Nix Web Application and Live Support Server.

Provides a local REST API and serves the interactive developer web app and live support platform.
"""

import os
import sys
import json
import time
import socket
import threading
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any

from config import get_project_root, set_project_root, load_config, get_default_config
from core import detector
from llm.client import (
    DEFAULT_PROVIDERS, get_active_provider, set_active_provider,
    get_api_key, save_api_key, get_active_model
)


class NixRequestHandler(SimpleHTTPRequestHandler):
    """Handles API requests and serves static web assets."""

    def __init__(self, *args, **kwargs):
        self.web_dir = os.path.join(os.path.dirname(__file__), "web")
        super().__init__(*args, directory=self.web_dir, **kwargs)

    def log_message(self, format, *args):
        """Suppress standard HTTP server access logs to keep terminal clean."""
        pass

    def end_headers(self):
        """Add anti-caching and CORS headers to all responses."""
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def _send_json(self, data: Any, status: int = 200):
        """Send JSON response."""
        resp_bytes = json.dumps(data, indent=2, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(resp_bytes)

    def _read_json_body(self) -> dict:
        """Parse JSON request body."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.wfile.raw.read(content_length) if hasattr(self.wfile, 'raw') else self.rfile.read(content_length)
                return json.loads(body.decode('utf-8'))
        except Exception:
            pass
        return {}

    def do_OPTIONS(self):
        """Handle CORS pre-flight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            self._handle_api_get(path, parsed)
        else:
            # Fallback to index.html for root or SPA paths
            if path in ("", "/", "/index.html") or not os.path.exists(os.path.join(self.web_dir, path.lstrip('/'))):
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            self._handle_api_post(path)
        else:
            self._send_json({"error": "Not Found"}, 404)

    def _handle_api_get(self, path: str, parsed):
        """Route API GET endpoints."""
        try:
            if path == "/api/status":
                self._get_status()
            elif path == "/api/overview":
                self._get_overview()
            elif path == "/api/endpoints":
                self._get_endpoints()
            elif path == "/api/beans":
                self._get_beans()
            elif path == "/api/issues":
                self._get_issues()
            elif path == "/api/dependencies":
                self._get_dependencies()
            elif path == "/api/entities":
                self._get_entities()
            elif path == "/api/config":
                self._get_config()
            else:
                self._send_json({"error": f"API endpoint '{path}' not found"}, 404)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_api_post(self, path: str):
        """Route API POST endpoints."""
        try:
            body = self._read_json_body()

            if path == "/api/chat":
                self._post_chat(body)
            elif path == "/api/diagnose":
                self._post_diagnose(body)
            elif path == "/api/fix":
                self._post_fix(body)
            elif path == "/api/test-api":
                self._post_test_api(body)
            elif path == "/api/starter":
                self._post_starter(body)
            elif path == "/api/config":
                self._post_config(body)
            elif path == "/api/switch-project":
                self._post_switch_project(body)
            elif path == "/api/load-demo":
                self._post_load_demo()
            else:
                self._send_json({"error": f"API endpoint '{path}' not found"}, 404)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    # API Handlers

    def _get_status(self):
        """Return system, project, and provider status."""
        root = get_project_root()
        is_sb, version = False, None
        try:
            is_sb, version = detector.is_springboot_project()
        except Exception:
            pass

        build_file, build_type = detector.find_build_file()
        java_count = detector.count_java_files()
        active_provider = get_active_provider()
        api_key = get_api_key(active_provider)

        data = {
            "project_name": os.path.basename(root) or "Spring Boot Project",
            "project_path": root,
            "is_springboot": is_sb,
            "springboot_version": version or "Detected via AST",
            "build_type": build_type or "Unknown",
            "build_file": os.path.basename(build_file) if build_file else None,
            "total_java_files": java_count,
            "provider": active_provider,
            "model": get_active_model(active_provider),
            "has_api_key": bool(api_key),
            "python_version": sys.version.split()[0]
        }
        self._send_json(data)

    def _get_overview(self):
        """Return quick metric overview and calculated health score."""
        from tools.endpoint_analyzer import analyze_endpoints
        from tools.bean_analyzer import analyze_beans
        from tools.entity_analyzer import analyze_entities
        from tools.null_safety_checker import check_null_safety
        from tools.security_checker import check_security

        endpoints_data = analyze_endpoints()
        beans_data = analyze_beans()
        entities_data = analyze_entities()
        npe_data = check_null_safety()
        sec_data = check_security()

        ep_count = endpoints_data.get('endpoint_count', 0) if isinstance(endpoints_data, dict) else 0
        controllers_count = endpoints_data.get('controller_count', 0) if isinstance(endpoints_data, dict) else 0
        beans_count = len(beans_data.get('beans', [])) if isinstance(beans_data, dict) else 0
        entities_count = len(entities_data.get('entities', [])) if isinstance(entities_data, dict) else 0
        npe_count = len(npe_data.get('issues', [])) if isinstance(npe_data, dict) else 0
        sec_count = len(sec_data.get('issues', [])) if isinstance(sec_data, dict) else 0

        # Health score calculation (100 base)
        score = 100
        score -= min(30, npe_count * 5)
        score -= min(40, sec_count * 10)
        score = max(35, score)

        grade = "A+" if score >= 95 else "A" if score >= 85 else "B" if score >= 70 else "C"

        self._send_json({
            "health_score": score,
            "health_grade": grade,
            "endpoints_count": ep_count,
            "controllers_count": controllers_count,
            "beans_count": beans_count,
            "entities_count": entities_count,
            "null_safety_issues": npe_count,
            "security_issues": sec_count,
            "total_issues": npe_count + sec_count
        })

    def _get_endpoints(self):
        """Return REST API endpoints."""
        from tools.endpoint_analyzer import analyze_endpoints
        res = analyze_endpoints()
        self._send_json(res)

    def _get_beans(self):
        """Return Spring Beans and Wiring."""
        from tools.bean_analyzer import analyze_beans
        from tools.bean_wiring_checker import check_bean_wiring
        beans = analyze_beans()
        wiring = check_bean_wiring()
        self._send_json({
            "beans": beans,
            "wiring": wiring
        })

    def _get_issues(self):
        """Return issues from all static checkers."""
        from tools.issue_finder import find_issues
        from tools.null_safety_checker import check_null_safety
        from tools.security_checker import check_security
        from tools.annotation_checker import check_annotations

        all_issues = []

        try:
            i_res = find_issues()
            if isinstance(i_res, dict) and "issues" in i_res:
                all_issues.extend(i_res["issues"])
        except Exception:
            pass

        try:
            n_res = check_null_safety()
            if isinstance(n_res, dict) and "issues" in n_res:
                for iss in n_res["issues"]:
                    iss["type"] = "Null Safety Risk"
                    all_issues.append(iss)
        except Exception:
            pass

        try:
            s_res = check_security()
            if isinstance(s_res, dict) and "issues" in s_res:
                for iss in s_res["issues"]:
                    iss["type"] = "Security Vulnerability"
                    all_issues.append(iss)
        except Exception:
            pass

        try:
            a_res = check_annotations()
            if isinstance(a_res, dict) and "issues" in a_res:
                for iss in a_res["issues"]:
                    iss["type"] = "Annotation Warning"
                    all_issues.append(iss)
        except Exception:
            pass

        self._send_json({
            "count": len(all_issues),
            "issues": all_issues
        })

    def _get_dependencies(self):
        """Return dependencies analysis."""
        from tools.dependency_analyzer import analyze_dependencies
        res = analyze_dependencies()
        self._send_json(res)

    def _get_entities(self):
        """Return JPA entities and relationships."""
        from tools.entity_analyzer import analyze_entities
        res = analyze_entities()
        self._send_json(res)

    def _get_config(self):
        """Return configuration settings."""
        active_prov = get_active_provider()
        providers_list = []
        for key, p in DEFAULT_PROVIDERS.items():
            providers_list.append({
                "id": key,
                "name": p["name"],
                "description": p["description"],
                "requires_key": p["requires_key"],
                "default_model": p["default_model"],
                "key_url": p.get("key_url", ""),
                "has_key": bool(get_api_key(key))
            })

        self._send_json({
            "active_provider": active_prov,
            "active_model": get_active_model(active_prov),
            "providers": providers_list,
            "current_project": get_project_root()
        })

    def _post_chat(self, body: dict):
        """Process conversational query."""
        message = body.get("message", "").strip()
        if not message:
            self._send_json({"error": "Empty message"}, 400)
            return

        from core.agent import Agent
        from tools import register_all_tools
        register_all_tools()

        agent = Agent()
        response_text = agent.run(message)

        self._send_json({
            "response": response_text,
            "history_length": len(agent.conversation_history)
        })

    def _post_diagnose(self, body: dict):
        """Diagnose stack trace or error log."""
        stack_trace = body.get("stack_trace", "").strip()
        if not stack_trace:
            self._send_json({"error": "Stack trace is required"}, 400)
            return

        from tools.error_diagnostics import diagnose_error
        res = diagnose_error(stack_trace)
        self._send_json(res)

    def _post_fix(self, body: dict):
        """Generate code fix suggestion."""
        file_path = body.get("file_path", "")
        issue_type = body.get("issue_type", "")
        line = body.get("line", 1)

        from tools.fix_suggester import suggest_fix
        res = suggest_fix(file_path=file_path, issue_type=issue_type, line=line)
        self._send_json(res)

    def _post_test_api(self, body: dict):
        """Live HTTP Endpoint Tester - sends test request to running Spring Boot app."""
        method = body.get("method", "GET").upper()
        url = body.get("url", "").strip()
        headers = body.get("headers", {})
        data = body.get("body", None)

        if not url:
            self._send_json({"error": "URL is required"}, 400)
            return

        import urllib.request
        import urllib.error

        req_data = None
        if data and method in ("POST", "PUT", "PATCH"):
            if isinstance(data, (dict, list)):
                req_data = json.dumps(data).encode('utf-8')
                headers["Content-Type"] = "application/json"
            else:
                req_data = str(data).encode('utf-8')

        start_time = time.time()
        try:
            req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=10) as resp:
                elapsed_ms = round((time.time() - start_time) * 1000, 1)
                resp_body = resp.read().decode('utf-8', errors='ignore')
                resp_headers = dict(resp.getheaders())

                try:
                    parsed_body = json.loads(resp_body)
                except Exception:
                    parsed_body = resp_body

                self._send_json({
                    "status": resp.status,
                    "elapsed_ms": elapsed_ms,
                    "headers": resp_headers,
                    "body": parsed_body
                })
        except urllib.error.HTTPError as e:
            elapsed_ms = round((time.time() - start_time) * 1000, 1)
            err_body = e.read().decode('utf-8', errors='ignore')
            try:
                parsed_body = json.loads(err_body)
            except Exception:
                parsed_body = err_body
            self._send_json({
                "status": e.code,
                "elapsed_ms": elapsed_ms,
                "headers": dict(e.headers),
                "body": parsed_body
            })
        except Exception as e:
            self._send_json({
                "status": 0,
                "error": f"Failed to connect to {url}: {str(e)}",
                "hint": "Make sure your Spring Boot application is running locally (e.g. on port 8080)"
            })

    def _post_starter(self, body: dict):
        """Generate ready-to-run Spring Boot starter project."""
        name = body.get("name", "my-spring-app").strip()
        group = body.get("group", "com.example").strip()
        artifact = body.get("artifact", name).strip()
        boot_version = body.get("version", "3.2.4").strip()
        dependencies = body.get("dependencies", ["web", "jpa", "h2"])
        target_dir = body.get("target_dir", os.path.join(get_project_root(), name))

        os.makedirs(os.path.join(target_dir, "src/main/java"), exist_ok=True)
        os.makedirs(os.path.join(target_dir, "src/main/resources"), exist_ok=True)

        # Generate pom.xml
        dep_xml = ""
        if "web" in dependencies:
            dep_xml += '        <dependency>\n            <groupId>org.springframework.boot</groupId>\n            <artifactId>spring-boot-starter-web</artifactId>\n        </dependency>\n'
        if "jpa" in dependencies:
            dep_xml += '        <dependency>\n            <groupId>org.springframework.boot</groupId>\n            <artifactId>spring-boot-starter-data-jpa</artifactId>\n        </dependency>\n'
        if "security" in dependencies:
            dep_xml += '        <dependency>\n            <groupId>org.springframework.boot</groupId>\n            <artifactId>spring-boot-starter-security</artifactId>\n        </dependency>\n'
        if "h2" in dependencies:
            dep_xml += '        <dependency>\n            <groupId>com.h2database</groupId>\n            <artifactId>h2</artifactId>\n            <scope>runtime</scope>\n        </dependency>\n'

        pom_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>{boot_version}</version>
        <relativePath/>
    </parent>
    <groupId>{group}</groupId>
    <artifactId>{artifact}</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>{name}</name>
    <properties>
        <java.version>17</java.version>
    </properties>
    <dependencies>
{dep_xml}
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
"""
        with open(os.path.join(target_dir, "pom.xml"), 'w', encoding='utf-8') as f:
            f.write(pom_content)

        # Generate main class
        package_dir = os.path.join(target_dir, "src/main/java", *group.split('.'), *name.replace('-', '_').split('.'))
        os.makedirs(package_dir, exist_ok=True)
        class_name = "".join(word.capitalize() for word in name.replace('-', ' ').replace('_', ' ').split()) + "Application"
        pkg_name = f"{group}.{name.replace('-', '_')}"

        main_class_content = f"""package {pkg_name};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class {class_name} {{
    public static void main(String[] args) {{
        SpringApplication.run({class_name}.class, args);
    }}
}}
"""
        with open(os.path.join(package_dir, f"{class_name}.java"), 'w', encoding='utf-8') as f:
            f.write(main_class_content)

        # Generate application.properties
        props_content = f"spring.application.name={name}\nserver.port=8080\n"
        with open(os.path.join(target_dir, "src/main/resources/application.properties"), 'w', encoding='utf-8') as f:
            f.write(props_content)

        self._send_json({
            "success": True,
            "message": f"Spring Boot project '{name}' successfully created!",
            "path": target_dir
        })

    def _post_config(self, body: dict):
        """Update provider and API key."""
        provider = body.get("provider", "groq").lower()
        api_key = body.get("api_key", "").strip()
        model = body.get("model", "").strip()

        if api_key:
            save_api_key(api_key, provider)
        if provider:
            set_active_provider(provider, model if model else None)

        self._send_json({
            "success": True,
            "active_provider": get_active_provider(),
            "active_model": get_active_model(provider)
        })

    def _post_switch_project(self, body: dict):
        """Switch active project directory."""
        path = body.get("path", "").strip()
        if not path or not os.path.exists(path):
            self._send_json({"error": "Invalid directory path"}, 400)
            return

        set_project_root(path)
        self._get_status()

    def _post_load_demo(self):
        """Load bundled sample Spring Boot project."""
        demo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "samples", "demo_store"))
        if os.path.exists(demo_path):
            set_project_root(demo_path)
            self._get_status()
        else:
            self._send_json({"error": "Demo store not found"}, 404)


def find_available_port(start_port: int = 8765, max_attempts: int = 20) -> int:
    """Find available port for web server."""
    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return start_port


def start_app_server(port: Optional[int] = None, open_browser: bool = True, project_path: Optional[str] = None):
    """Start Nix Web App and Live Support server."""
    if project_path:
        set_project_root(project_path)

    chosen_port = port or find_available_port(8765)
    server_address = ("127.0.0.1", chosen_port)
    httpd = ThreadingHTTPServer(server_address, NixRequestHandler)

    url = f"http://127.0.0.1:{chosen_port}"

    from utils.output import Colors, bold, color

    print()
    print(f"{Colors.CYAN}  ┌────────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.CYAN}  │                                                            │{Colors.RESET}")
    print(f"{Colors.CYAN}  │  {Colors.BOLD}{Colors.GREEN}🚀 Nix - AI Spring Boot Assistant & Live Support Platform{Colors.RESET}{Colors.CYAN} │{Colors.RESET}")
    print(f"{Colors.CYAN}  │                                                            │{Colors.RESET}")
    print(f"{Colors.CYAN}  │  {Colors.YELLOW}Local App:{Colors.RESET}   {Colors.BOLD}{url}{Colors.RESET}{Colors.CYAN}                             │{Colors.RESET}")
    print(f"{Colors.CYAN}  │  {Colors.YELLOW}Project:{Colors.RESET}     {os.path.basename(get_project_root())[:35]:<35}{Colors.CYAN}       │{Colors.RESET}")
    print(f"{Colors.CYAN}  │                                                            │{Colors.RESET}")
    print(f"{Colors.CYAN}  │  {Colors.MAGENTA}Live Support Hub | Endpoints Tester | Beans Graph | Fixes{Colors.RESET}{Colors.CYAN} │{Colors.RESET}")
    print(f"{Colors.CYAN}  │                                                            │{Colors.RESET}")
    print(f"{Colors.CYAN}  │  Press {Colors.BOLD}Ctrl+C{Colors.RESET}{Colors.CYAN} to stop the server                          │{Colors.RESET}")
    print(f"{Colors.CYAN}  └────────────────────────────────────────────────────────────┘{Colors.RESET}")
    print()

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Stopping Nix App server... Goodbye!{Colors.RESET}")
        httpd.server_close()
