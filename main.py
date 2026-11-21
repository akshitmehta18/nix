#!/usr/bin/env python3
"""Nix - Modern AI Assistant and Live Support Platform for Spring Boot projects.

Created by Akshit Mehta & Nikhil Saini (Chitkara University).
"""

import os
import sys

# Ensure nix directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import set_project_root, get_project_root, nix_exists
from llm.client import (
    get_api_key, save_api_key, get_active_provider,
    set_active_provider, get_active_model, DEFAULT_PROVIDERS
)


def main():
    """Main CLI entry point for nix."""
    try:
        raw_args = sys.argv[1:]

        # Handle global flags like --path <dir>
        args = []
        custom_path = None
        i = 0
        while i < len(raw_args):
            if raw_args[i] in ("--path", "-p") and i + 1 < len(raw_args):
                custom_path = raw_args[i + 1]
                i += 2
            else:
                args.append(raw_args[i])
                i += 1

        if custom_path:
            set_project_root(custom_path)

        command = args[0].lower() if args else None

        # Handle help
        if command in ("help", "--help", "-h"):
            print_help()
            return

        # Handle app / ui / web command
        if command in ("app", "ui", "web"):
            port = None
            no_browser = False
            for a in args[1:]:
                if a.isdigit():
                    port = int(a)
                elif a == "--no-browser":
                    no_browser = True
            from app.server import start_app_server
            start_app_server(port=port, open_browser=not no_browser)
            return

        # Handle doctor command
        if command == "doctor":
            run_doctor()
            return

        # Handle config command
        if command == "config":
            handle_config(args[1:])
            return

        # Handle endpoints command
        if command in ("endpoints", "apis", "routes"):
            run_endpoints_cli()
            return

        # Handle beans command
        if command == "beans":
            run_beans_cli()
            return

        # Handle issues command
        if command in ("issues", "bugs"):
            run_issues_cli()
            return

        # Handle scan command
        if command in ("scan", "audit"):
            run_scan_cli()
            return

        # Handle status command
        if command == "status":
            from commands import status
            status.run()
            return

        # Handle init command
        if command == "init":
            from commands import init
            init.run(show_banner=True)
            return

        # Check if project exists or can be detected
        from core import detector
        is_sb, version = False, None
        try:
            is_sb, version = detector.is_springboot_project()
        except Exception:
            pass

        # If not inside a Spring Boot project and no command, check if demo can be suggested
        if not is_sb and detector.count_java_files() == 0 and not args:
            demo_dir = os.path.join(os.path.dirname(__file__), "samples", "demo_store")
            if os.path.exists(demo_dir):
                print("Notice: No Spring Boot project found in current directory.")
                print(f"Tip: You can launch the web app with demo project: nix app")
                print(f"Or target a specific project: nix --path /path/to/project\n")

        # Handle single query execution: nix <question>
        if args:
            user_input = " ".join(args)
            run_natural_language(user_input)
            return

        # Start interactive REPL
        start_repl()

    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


def handle_config(config_args):
    """Handle nix config commands."""
    if not config_args or "--list" in config_args or "-l" in config_args:
        active = get_active_provider()
        model = get_active_model(active)
        print("Nix LLM Configuration:")
        print(f"  Active Provider: {active.upper()}")
        print(f"  Active Model:    {model}")
        print("\nSupported Providers:")
        for k, p in DEFAULT_PROVIDERS.items():
            has_key = "✓ Configured" if get_api_key(k) else ("No Key Required" if not p["requires_key"] else "Not Set")
            print(f"  - {k:<10} ({p['name']}): {has_key}")
        print("\nUsage:")
        print("  nix config <api_key>                     Set key for default provider")
        print("  nix config --provider <name> <api_key>   Set provider and key")
        print("  nix config --model <model_name>          Set custom model")
        return

    # Check for --provider
    if "--provider" in config_args:
        idx = config_args.index("--provider")
        if idx + 1 < len(config_args):
            prov = config_args[idx + 1].lower()
            key = config_args[idx + 2] if idx + 2 < len(config_args) else None
            if prov not in DEFAULT_PROVIDERS:
                print(f"Unknown provider '{prov}'. Available: {list(DEFAULT_PROVIDERS.keys())}")
                return
            set_active_provider(prov)
            if key:
                save_api_key(key, prov)
                print(f"Provider set to {prov.upper()} and API key saved!")
            else:
                print(f"Active provider switched to {prov.upper()}!")
            return

    # Check for --model
    if "--model" in config_args:
        idx = config_args.index("--model")
        if idx + 1 < len(config_args):
            model = config_args[idx + 1]
            prov = get_active_provider()
            set_active_provider(prov, model)
            print(f"Model for {prov.upper()} set to: {model}")
            return

    # Default: nix config <key>
    key = config_args[0]
    prov = get_active_provider()
    save_api_key(key, prov)
    print(f"API key for {prov.upper()} saved successfully!")


def run_doctor():
    """Environment and system diagnostician."""
    import subprocess
    from utils.output import Colors, bold, color

    print(f"\n{bold('🩺 Nix System & Environment Doctor')}\n")

    # 1. Python version
    py_ver = sys.version.split()[0]
    print(f"  {color('✓', Colors.GREEN)} Python Runtime:   {py_ver}")

    # 2. Tree-sitter Java
    try:
        from indexer.java_parser import JavaParser
        p = JavaParser()
        ts_ok = p.is_available()
        status = color("✓ Ready (AST Enabled)", Colors.GREEN) if ts_ok else color("⚠ Regex Fallback", Colors.YELLOW)
        print(f"  {status:<30} Tree-sitter Java Parser")
    except Exception as e:
        print(f"  {color('✗ Error', Colors.RED)} Tree-sitter: {str(e)}")

    # 3. Java Runtime
    try:
        j_res = subprocess.run(["java", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if j_res.returncode == 0:
            first_line = (j_res.stderr or j_res.stdout).splitlines()[0]
            print(f"  {color('✓', Colors.GREEN)} Java Runtime:     {first_line[:40]}")
        else:
            print(f"  {color('⚠', Colors.YELLOW)} Java Runtime:     Not detected in PATH (optional for static analysis)")
    except Exception:
        print(f"  {color('⚠', Colors.YELLOW)} Java Runtime:     Not detected in PATH (optional for static analysis)")

    # 4. Build tools
    has_mvn = subprocess.run(["which", "mvn"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
    has_gradle = subprocess.run(["which", "gradle"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
    build_tools = []
    if has_mvn: build_tools.append("Maven")
    if has_gradle: build_tools.append("Gradle")
    tools_str = ", ".join(build_tools) if build_tools else "None (static analysis active)"
    print(f"  {color('✓', Colors.GREEN)} Build Tools:      {tools_str}")

    # 5. LLM Provider
    prov = get_active_provider()
    key = get_api_key(prov)
    prov_str = f"{prov.upper()} ({'✓ Key Active' if key else '⚠ No Key - Local Fallback Mode'})"
    print(f"  {color('✓', Colors.GREEN)} AI Engine:        {prov_str}")

    # 6. Active Project
    from core import detector
    root = get_project_root()
    is_sb, ver = False, None
    try:
        is_sb, ver = detector.is_springboot_project()
    except Exception:
        pass
    j_files = detector.count_java_files()
    proj_str = f"{os.path.basename(root)} ({'Spring Boot ' + str(ver) if is_sb else 'Java/Spring'}, {j_files} Java files)"
    print(f"  {color('✓', Colors.GREEN)} Target Project:   {proj_str}\n")


def run_endpoints_cli():
    """Print REST endpoints in formatted CLI table."""
    from tools import register_all_tools
    register_all_tools()
    from tools.endpoint_analyzer import analyze_endpoints
    from utils.output import Colors, bold

    res = analyze_endpoints()
    endpoints = res.get("endpoints", [])
    if not endpoints:
        print("No REST endpoints discovered.")
        return

    print(f"\n{bold(f'Discovered {len(endpoints)} REST Endpoints:')}\n")
    print(f"  {'METHOD':<8} {'PATH':<35} {'HANDLER':<30}")
    print("  " + "─" * 75)
    for ep in endpoints:
        m = ep.get("method", "GET")
        p = ep.get("path", "/")[:34]
        h = f"{ep.get('controller', '')}.{ep.get('handler', '')}()"[:29]
        m_color = Colors.GREEN if m == "GET" else Colors.BLUE if m == "POST" else Colors.YELLOW if m == "PUT" else Colors.RED
        print(f"  {m_color}{m:<8}{Colors.RESET} {p:<35} {h:<30}")
    print()


def run_beans_cli():
    """Print Spring beans in CLI table."""
    from tools import register_all_tools
    register_all_tools()
    from tools.bean_analyzer import analyze_beans
    from utils.output import bold, Colors

    res = analyze_beans()
    beans = res.get("beans", [])
    if not beans:
        print("No Spring beans detected.")
        return

    print(f"\n{bold(f'Discovered {len(beans)} Spring Components & Beans:')}\n")
    print(f"  {'TYPE':<18} {'BEAN NAME':<35} {'FILE'}")
    print("  " + "─" * 75)
    for b in beans:
        t = f"@{b.get('type', 'Component')}"[:17]
        n = b.get("name", "")[:34]
        f = b.get("file", "")
        print(f"  {Colors.MAGENTA}{t:<18}{Colors.RESET} {n:<35} {f}")
    print()


def run_issues_cli():
    """Print static issues in CLI table."""
    from tools import register_all_tools
    register_all_tools()
    from tools.issue_finder import find_issues
    from utils.output import bold, Colors

    res = find_issues()
    issues = res.get("issues", [])
    if not issues:
        print(f"\n{Colors.GREEN}✓ No critical issues detected!{Colors.RESET}\n")
        return

    print(f"\n{bold(f'Found {len(issues)} Issues & Bug Risks:')}\n")
    for i, iss in enumerate(issues[:15], 1):
        sev = (iss.get("severity") or "MEDIUM").upper()
        col = Colors.RED if sev == "CRITICAL" else Colors.YELLOW if sev == "HIGH" else Colors.CYAN
        title = iss.get("issue") or iss.get("type") or "Issue"
        loc = f"{iss.get('file', 'Unknown')}:{iss.get('line', '?')}"
        fix = iss.get("fix")
        print(f"  {i}. {col}[{sev}]{Colors.RESET} {title}")
        print(f"     Location: {loc}")
        if fix:
            print(f"     Fix:      {fix}")
        print()
    if len(issues) > 15:
        print(f"  ... and {len(issues) - 15} more issues. Run 'nix app' for full interactive inspector.\n")


def run_scan_cli():
    """Run full static audit across all tools."""
    from tools import register_all_tools
    register_all_tools()
    from utils.output import bold, Colors

    print(f"\n{bold('⚡ Running Full Project Static Audit...')}\n")
    run_endpoints_cli()
    run_beans_cli()
    run_issues_cli()


def start_repl():
    """Interactive REPL mode."""
    from tools import register_all_tools
    register_all_tools()
    from core.agent import Agent
    from utils.output import bold, muted, print_banner

    print_banner()
    prov = get_active_provider()
    key = get_api_key(prov)

    print(bold("    Nix v2.0 • AI Terminal Coding Assistant & Live Support Platform"))
    print(muted(f"    Active Engine: {prov.upper()} • Target: {os.path.basename(get_project_root())}"))
    if not key:
        print(muted("    [Local Mode Active] Direct static AST analysis enabled."))
        print(muted("    To enable conversational LLM: 'nix config <key>' or 'nix app' for Web UI.\n"))
    else:
        print(muted("    Type your question, or 'help' for options. Ctrl+C to exit.\n"))

    agent = Agent()

    while True:
        try:
            user_input = input(f"{muted('>')} ").strip()
            if not user_input:
                continue

            low = user_input.lower()
            if low in ("exit", "quit", "q"):
                print("Goodbye!")
                break
            if low == "help":
                print_repl_help()
                continue
            if low in ("app", "web", "ui"):
                from app.server import start_app_server
                start_app_server()
                continue
            if low == "endpoints":
                run_endpoints_cli()
                continue
            if low == "beans":
                run_beans_cli()
                continue
            if low == "issues":
                run_issues_cli()
                continue
            if low == "clear":
                os.system("clear" if os.name == "posix" else "cls")
                continue
            if low == "new":
                agent.clear_history()
                print("Started fresh conversation.")
                continue

            response = agent.run(user_input)
            print(f"\n{response}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            break


def run_natural_language(user_input):
    """Run a single natural language query."""
    from tools import register_all_tools
    register_all_tools()
    from core.agent import Agent
    agent = Agent()
    resp = agent.run(user_input)
    print(resp)


def print_help():
    """Print CLI help information."""
    print("""nix - Modern AI Assistant and Live Support Platform for Spring Boot

USAGE:
  nix                               Start interactive terminal session
  nix app                           Launch the Modern Web App & Live Support Hub
  nix doctor                        Run environment and runtime health checks
  nix scan                          Run complete static audit (endpoints, beans, bugs)
  nix endpoints                     Discover and list all REST API endpoints
  nix beans                         List all Spring components, services & beans
  nix issues                        Find bugs, null safety risks & vulnerabilities
  nix config [key]                  Configure API keys or switch providers
  nix <question>                    Ask natural language question directly

OPTIONS:
  --path <dir>, -p <dir>            Target specific project folder
  --port <port>                     Custom port for web app (default: 8765)
  --no-browser                      Do not auto-open browser on 'nix app'

CONFIG EXAMPLES:
  nix config gsk_...                Set Groq API key (default)
  nix config --provider gemini ...  Configure Google Gemini
  nix config --provider ollama      Use 100% free local offline Ollama
  nix config --list                 Show configured providers and models

Created by Akshit Mehta & Nikhil Saini (Chitkara University).
""")


def print_repl_help():
    """Print help inside REPL."""
    print("""
Interactive Commands:
  endpoints       List discovered REST endpoints
  beans           List Spring beans and dependencies
  issues          Scan for bugs and null pointer risks
  app             Launch the Web Application & Live Support Hub
  new             Start a fresh conversation
  clear           Clear terminal screen
  exit            Exit nix

Natural Language Examples:
  > what endpoints do I have?
  > find issues in my code
  > check for null pointer problems
  > trace call chain from ProductController
  > analyze my dependencies
""")


if __name__ == "__main__":
    main()
