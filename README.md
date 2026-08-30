# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with multi-model support, team workspaces, enterprise features, Rust-powered performance, Hermes integration, security-first architecture, MCP protocol, multi-agent orchestration, integration SDK, native sandbox, fullstack AI engineer mode, beginner-friendly UI, and **advanced user features**.

![Version](https://img.shields.io/badge/version-50.0-blue)
![Tests](https://img.shields.io/badge/tests-643%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-layered-success)
![Fullstack](https://img.shields.io/badge/fullstack-engineer-success)
![Dashboard](https://img.shields.io/badge/dashboard-web-success)
![Templates](https://img.shields.io/badge/templates-custom-success)
![Debug](https://img.shields.io/badge/debug-mode-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Rust](https://img.shields.io/badge/rust-1.75+-orange)
![Hermes](https://img.shields.io/badge/hermes-integrated-purple)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

### Advanced User Features (NEW in V50)
- **Template Preview**: Visual thumbnails with feature highlights
- **Success Animation**: Celebration on project completion
- **Debug Mode**: Verbose logging for troubleshooting
- **Custom Templates**: Create and share your own templates
- **Diff Preview**: Before/after comparison before apply

### Beginner-Friendly UI (V47-V49)
- **Setup Wizard**: `aeryn start` — interactive project setup
- **Visual Dashboard**: Web-based UI at `http://localhost:3020`
- **One-Click Generate**: Minimal questions, instant project creation
- **Post-Generate Guide**: Clear next steps after project creation
- **Progress Indicator**: Visual feedback during generation
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
│   ├── oneclick/            ← One-click generate
│   ├── postguide/           ← Post-generate guide
│   ├── progress/            ← Progress indicator
│   ├── error_solver/        ← Error analysis & solutions
│   ├── preview/             ← Project preview
│   ├── help/                ← Contextual help
│   ├── gallery/             ← Example gallery
│   ├── undo/                ← Undo changes
│   ├── proactive/           ← Proactive warnings
│   ├── template_preview/    ← Visual template preview
│   ├── success_anim/        ← Success animation
│   ├── debug_mode/          ← Debug mode
│   ├── custom_template/     ← Custom template editor
│   ├── diff_preview/        ← Diff preview
│   └── ...
├── aeryn-engine/            ← Rust (6 modules)
├── tests/                   ← 643 tests
└── ...
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+, Rust 1.75+ |
| API Framework | FastAPI |
| Database | SQLite (local) + PostgreSQL/Neon (cloud) |
| Authentication | JWT + API Keys |
| AI/LLM | Gemini, OpenRouter, DeepSeek (fallback) |
| Protocol | MCP (Model Context Protocol) |
| Build System | uv + Maturin (PyO3) |
| CI/CD | GitHub Actions |
| Deployment | PM2, Docker |

---

## 🚀 Quick Start

```bash
# Option 1: Setup Wizard
aeryn start

# Option 2: One-Click Generate
aeryn new my-app --template react

# Option 3: Visual Dashboard
aeryn dashboard

# Option 4: One-Click Installer
./aeryn-installer.sh
```

---

## 📚 Commands

| Command | Description |
|---------|-------------|
| `aeryn start` | Interactive setup wizard |
| `aeryn new <name> [--template react\|vue\|api\|bot]` | Create new project |
| `aeryn dev [--port 3010]` | Start development server |
| `aeryn db:migrate` | Run migrations |
| `aeryn db:seed` | Seed database |
| `aeryn test [--watch] [--coverage]` | Run tests |
| `aeryn build [--target node\|static]` | Build production |
| `aeryn deploy [--target pm2\|docker\|vercel]` | Deploy |
| `aeryn debug` | Enable debug mode |
| `aeryn templates` | List available templates |

---

## 🧪 Testing

```bash
./venv-proot/bin/python -m pytest tests/ -v
```

---

## 📊 Test Coverage

```
643 tests pass
0 failures
1 warning
```

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*
