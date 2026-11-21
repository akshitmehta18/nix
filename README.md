# Nix v2.0 — AI Terminal Coding Assistant & Live Support Platform

<div align="center">

```
        ███╗   ██╗ ██╗ ██╗  ██╗
        ████╗  ██║ ██║ ╚██╗██╔╝
        ██╔██╗ ██║ ██║  ╚███╔╝
        ██║╚██╗██║ ██║  ██╔██╗
        ██║ ╚████║ ██║ ██╔╝ ██╗
        ╚═╝  ╚═══╝ ╚═╝ ╚═╝  ╚═╝
        ════════════════════════
```

**Next-Generation AI Assistant, Visual Dashboard & Live Support Platform for Spring Boot**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](#requirements)
[![Version 2.0.0](https://img.shields.io/badge/version-2.0.0-indigo.svg)](#features)
[![License MIT](https://img.shields.io/badge/license-MIT-green.svg)](#license)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-trycloudflare-blueviolet.svg)](https://spanking-dreams-recorded-amsterdam.trycloudflare.com)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Active-success.svg)](https://mehtaji2004.github.io/nix/)
[![Multi-Model](https://img.shields.io/badge/AI%20Providers-Groq%20%7C%20Gemini%20%7C%20OpenAI%20%7C%20Ollama%20%7C%20Claude-orange.svg)](#ai-providers)

</div>

---

### 🌐 Direct Access Links
* **Live Worldwide Cloud URL**: [https://spanking-dreams-recorded-amsterdam.trycloudflare.com](https://spanking-dreams-recorded-amsterdam.trycloudflare.com)
* **GitHub Repository**: [https://github.com/Mehtaji2004/nix](https://github.com/Mehtaji2004/nix)
* **GitHub Pages Web Showcase**: [https://mehtaji2004.github.io/nix/](https://mehtaji2004.github.io/nix/)

---

### 👨‍💻 Team & Contributors

| Name | Roll Number | University |
| :--- | :--- | :--- |
| **Akshit Mehta** | 2211981043 | Chitkara University |
| **Nikhil Saini** | 2211981245 | Chitkara University |

### 🎓 Mentors

| Name | Email |
| :--- | :--- |
| **Dr. Rajat Takkar** | [rajat.takkar@chitkara.edu.in](mailto:rajat.takkar@chitkara.edu.in) |
| **Isha Kansal** | [isha.kansal@chitkara.edu.in](mailto:isha.kansal@chitkara.edu.in) |

---

## 🌟 What is Nix v2.0?

**Nix** is a developer platform designed specifically for Spring Boot and Java engineering. It bridges deep static AST code analysis with conversational LLMs to provide real-time architectural insights, bug detection, automated fix suggestions, and live developer support.

With **Nix v2.0**, developers can interact via either the **Terminal CLI** or the **Modern Web Application & Live Support Hub (`nix app`)**.

---

## 🚀 Quick Start

### 1. Installation on macOS / Linux
```bash
git clone https://github.com/Mehtaji2004/nix.git
cd nix
pip install -e .
```

### 2. Verify System Installation
```bash
nix doctor
```

### 3. Launch the Web App & Live Support Hub
```bash
nix app
```
*Automatically starts the local server and opens your browser at `http://127.0.0.1:8765`!*

Or double-click `Launch Nix App.command` in macOS Finder!

---

## 🌐 The Nix Web App & Live Support Hub

Run `nix app` to access the full visual developer dashboard:

| Feature Tab | Description |
| :--- | :--- |
| **💬 Live Support & Chat** | Real-time AI chat with Nix, tool activity telemetry, code diffs, and prompt pills. |
| **📊 Health & Overview** | Codebase Health Score (0-100), metrics for endpoints, beans, entities, and risks. |
| **🌐 REST Endpoints** | Searchable list of all controllers, HTTP methods (GET, POST, PUT, DELETE), and paths. |
| **🚀 Live API Tester** | Built-in HTTP client to test requests to your running Spring Boot app (`http://localhost:8080`)! |
| **🧩 Beans & Architecture** | Component catalog (`@Service`, `@Repository`, `@Controller`, `@Component`) & dependency injection graph. |
| **⚠️ Issues & Security** | Critical, High, and Medium bug detection with one-click **Automated Code Fix** diffs. |
| **🔍 Stack Trace Diagnostician** | Paste any Java / Spring Boot stack trace for instant line-by-line diagnosis and resolution steps. |
| **✨ Spring Initializr** | Generate new Spring Boot starter projects with Maven, JPA, Web, and Security. |
| **⚙️ Multi-Model Settings** | Switch AI providers (Groq, Gemini, OpenAI, Claude, Ollama) and configure keys on the fly. |

---

## 🤖 Multi-Provider AI Engine

Nix v2.0 supports cloud providers and **100% free offline local AI**:

```bash
# 1. Groq (Default - Ultra-fast inference)
nix config gsk_YOUR_GROQ_KEY

# 2. Google Gemini (Gemini 2.5 Flash / Pro)
nix config --provider gemini AIzaSy_YOUR_GEMINI_KEY

# 3. OpenAI (GPT-4o / GPT-4o-mini)
nix config --provider openai sk_YOUR_OPENAI_KEY

# 4. Ollama (100% Free, Private, Offline Local AI - No Key Needed!)
nix config --provider ollama

# 5. List configured providers
nix config --list
```

> **Note**: Even with **zero API keys configured**, Nix runs in **Local AST Mode**, executing all 24 static analysis tools with complete functionality!

---

## 💻 CLI Commands

```bash
nix                          # Start interactive terminal session
nix app                      # Launch modern Web App & Live Support Hub
nix doctor                   # Run system & runtime diagnostics
nix scan                     # Run full project static audit
nix endpoints                # Discover and list all REST endpoints
nix beans                    # List all Spring components and wiring
nix issues                   # Find bugs, NPEs, and security risks
nix config [key]             # Configure AI keys or switch providers
nix <question>               # Ask a natural language question directly
```

### Target Any Project Folder
Use the `--path` flag to analyze any project on your computer:
```bash
nix endpoints --path /Users/username/my-spring-boot-project
nix app --path /Users/username/my-spring-boot-project
```

---

## 📦 Bundled Sample Project

Nix includes a realistic demo Spring Boot store located at `samples/demo_store`:
- Contains REST controllers (`ProductController`, `CustomerController`), JPA entities, services, and repositories.
- Test it immediately:
  ```bash
  nix endpoints --path samples/demo_store
  nix beans --path samples/demo_store
  nix issues --path samples/demo_store
  ```
- Or click **"Load Demo Store"** in the Web App top bar!

---

## 🏗️ Architecture

```
User Input (Terminal / Web App)
        ↓
    Intent & Heuristic Router
        ↓
   Multi-Model Engine (Groq / Gemini / OpenAI / Ollama / Local AST)
        ↓
    Tool Execution & Code Indexer (Tree-sitter AST Java Parser)
        ↓
    Static Analyzers (24+ Specialized Tools):
    ├── Endpoint Analyzer       ├── Bean Wiring Checker
    ├── Null Safety Checker     ├── Security Checker
    ├── Error Diagnostician     ├── Fix Suggester
    └── Dependency Analyzer     └── Call Chain Finder
        ↓
    Rich Terminal / Web UI with Live Support & API Tester
```

---

## 📄 License

MIT License — Copyright (c) 2026 Akshit Mehta & Nikhil Saini.
