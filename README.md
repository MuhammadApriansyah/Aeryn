# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with multi-model support, team workspaces, enterprise features, Rust-powered performance, Hermes integration, security-first architecture, MCP protocol, multi-agent orchestration, integration SDK, native sandbox, fullstack AI engineer mode, and **beginner-friendly UI**.

![Version](https://img.shields.io/badge/version-47.0-blue)
![Tests](https://img.shields.io/badge/tests-630%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-layered-success)
![Fullstack](https://img.shields.io/badge/fullstack-engineer-success)
![Dashboard](https://img.shields.io/badge/dashboard-web-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Rust](https://img.shields.io/badge/rust-1.75+-orange)
![Hermes](https://img.shields.io/badge/hermes-integrated-purple)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

### Beginner-Friendly UI (NEW in V47)
- **Setup Wizard**: `aeryn start` — interactive project setup
- **Visual Dashboard**: Web-based UI at `http://localhost:3020`
- **Error Solver**: Friendly error messages with solutions
- **One-Click Installer**: `./aeryn-installer.sh`

### Fullstack AI Engineer (V46)
- **Fullstack CLI**: `new`, `dev`, `db:migrate`, `db:seed`, `test`, `build`, `deploy`
- **Realistic Templates**: React + Fastify + SQLite with auth, CRUD
- **Migration System**: Database migrations with rollback

### Native Sandbox (V45)
- **Conditional Security**: Auto-detect → best isolation level
- **Directed Fallback**: Graceful degradation
- **4 Isolation Levels**: Basic → Namespace → Bubblewrap → Full

### MCP Protocol (V43)
- **MCP Server**: Serve tools, resources, prompts
- **MCP Client**: Connect to external servers

### Security-First (V42)
- **Prompt Injection Defense**: Input sanitization, output validation
- **Memory Injection Defense**: Integrity verification
- **Tool Permission Limits**: Risk-based access
- **Model Routing**: Tiered selection (60-70% cost reduction)

---

## 🏗️ Architecture

```
Aeryn/
├── aeryn_core/
│   ├── fullstack/           ← Fullstack AI Engineer
│   ├── sandbox/             ← Native sandbox (4 levels)
│   ├── mcp/                 ← MCP server + client
│   ├── multi_agent/         ← Multi-Agent orchestrator
│   ├── dashboard/           ← Web-based UI
│   ├── wizard/              ← Interactive setup wizard
│   ├── error_solver/        ← Error analysis & solutions
│   ├── installer/           ← One-click installer
│   └── ...
├── aeryn-engine/            ← Rust (6 modules)
├── tests/                   ← 630 tests
└── ...
```

---

## 🚀 Quick Start

### Option 1: Setup Wizard (Recommended for beginners)

```bash
aeryn start
# Follow the interactive prompts
# That's it! Your project is ready.
```

### Option 2: Visual Dashboard

```bash
aeryn dashboard
# Open http://localhost:3020
# Create projects, manage servers, view logs — all from the browser.
```

### Option 3: CLI (For developers)

```bash
aeryn new my-app --template react
cd my-app
aeryn dev
```

### Option 4: One-Click Installer

```bash
./aeryn-installer.sh
# Automatically installs Python, Node.js, Rust, and all dependencies
```

---

## 📚 Commands

| Command | Description |
|---------|-------------|
| `aeryn start` | Interactive setup wizard |
| `aeryn dashboard` | Launch visual dashboard |
| `aeryn new <name>` | Create new project |
| `aeryn dev` | Start development server |
| `aeryn db:migrate` | Run migrations |
| `aeryn db:seed` | Seed database |
| `aeryn test` | Run tests |
| `aeryn build` | Build production |
| `aeryn deploy` | Deploy application |

---

## 🧪 Testing

```bash
./venv-proot/bin/python -m pytest tests/ -v
```

---

## 📊 Test Coverage

```
630 tests pass
0 failures
1 warning
```

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*
