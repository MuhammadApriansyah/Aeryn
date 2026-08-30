# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with multi-model support, team workspaces, enterprise features, Rust-powered performance, Hermes integration, security-first architecture, MCP protocol, multi-agent orchestration, integration SDK, native sandbox, fullstack AI engineer mode, beginner-friendly UI, and **expert automation features**.

![Version](https://img.shields.io/badge/version-54.0-blue)
![Tests](https://img.shields.io/badge/tests-648%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-layered-success)
![Fullstack](https://img.shields.io/badge/fullstack-engineer-success)
![Dashboard](https://img.shields.io/badge/dashboard-web-success)
![Templates](https://img.shields.io/badge/templates-custom-success)
![Debug](https://img.shields.io/badge/debug-mode-success)
![Headless](https://img.shields.io/badge/headless-mode-success)
![Batch](https://img.shields.io/badge/batch-generate-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Rust](https://img.shields.io/badge/rust-1.75+-orange)
![Hermes](https://img.shields.io/badge/hermes-integrated-purple)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

### Expert Automation (NEW in V54)
- **Headless Mode**: `--non-interactive` flag for fully automated CI/CD
- **Config File**: `.aerynrc` for project defaults and reproducibility
- **Batch Generate**: Generate multiple projects from JSON config
- **Deployment Dashboard**: Monitor deployment status
- **Visual API Designer**: Design APIs with JSON/YAML export
- **Performance Monitor**: Track API metrics (avg, p50, p95, p99, error rate)

### Beginner-Friendly UI (V47-V50)
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

### Adaptive Rule Engine (V42)
- **Hot-reloadable rules** — Change behavior without restart
- **Priority-based evaluation** — Higher priority rules execute first

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
│   ├── plugin_system/       ← Plugin architecture
│   ├── plugin_marketplace/  ← Plugin sharing
│   ├── plugin_docs/         ← Plugin documentation
│   ├── ci_cd/               ← CI/CD templates
│   ├── multi_db/            ← Multi-database support
│   ├── working_tests/       ← Working test generation
│   ├── websocket_template/  ← WebSocket/SSE templates
│   ├── api_versioning/      ← API versioning
│   ├── env_management/      ← Environment management
│   ├── auto_rollback/       ← Auto rollback migration
│   ├── deploy_dashboard/    ← Deployment monitoring
│   ├── api_designer/        ← Visual API designer
│   ├── performance_monitor/ ← Performance monitoring
│   ├── headless_mode/       ← Headless/automated mode
│   ├── config_file/         ← .aerynrc config
│   ├── batch_generate/      ← Batch generation
│   └── ...
├── aeryn-engine/            ← Rust (6 modules)
├── plugins/aeryn-core/      ← Hermes plugin entry
├── tests/                   ← 648 tests
├── .github/workflows/       ← CI/CD Pipeline
├── Dockerfile + compose     ← Docker support
└── monitoring/              ← Metrics collector
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

### Option 1: Setup Wizard (Recommended for beginners)

```bash
aeryn start
```

### Option 2: One-Click Generate

```bash
aeryn new my-app --template react
cd my-app
aeryn dev
```

### Option 3: Visual Dashboard

```bash
aeryn dashboard
# Open http://localhost:3020
```

### Option 4: Headless Mode (For CI/CD)

```bash
aeryn new my-app --non-interactive --template react
```

### Option 5: Batch Generate

```bash
aeryn batch projects.json
```

---

## 📚 Commands

| Command | Description |
|---------|-------------|
| `aeryn start` | Interactive setup wizard |
| `aeryn dashboard` | Launch visual dashboard |
| `aeryn new <name> [--template react\|vue\|api\|bot]` | Create new project |
| `aeryn new <name> --non-interactive` | Headless generation |
| `aeryn batch <config.json>` | Batch generate projects |
| `aeryn dev [--port 3010]` | Start development server |
| `aeryn db:migrate` | Run migrations |
| `aeryn db:seed` | Seed database |
| `aeryn test [--watch] [--coverage]` | Run tests |
| `aeryn build [--target node\|static]` | Build production |
| `aeryn deploy [--target pm2\|docker\|vercel]` | Deploy |
| `aeryn debug` | Enable debug mode |
| `aeryn templates` | List available templates |
| `aeryn plugins` | List installed plugins |
| `aeryn config` | Show current config |

---

## 📋 .aerynrc Config File

```json
{
  "version": "1.0",
  "defaults": {
    "template": "react",
    "database": "sqlite",
    "auth": true,
    "testing": true,
    "ci_cd": true
  },
  "plugins": [],
  "environments": {
    "development": {"port": 3010},
    "staging": {"port": 3011},
    "production": {"port": 3012}
  }
}
```

---

## 🔧 Headless Mode Example

```python
from aeryn_core.headless_mode import headless_runner

result = headless_runner.generate({
    "name": "my-app",
    "template": "react",
    "plugins": ["auth"],
    "post_generate": ["install_deps", "run_tests"]
})

print(result)
# {"success": true, "result": {...}}
```

---

## 📦 Batch Generate Example

```json
{
  "projects": [
    {"name": "app-1", "template": "react"},
    {"name": "app-2", "template": "api"},
    {"name": "app-3", "template": "bot"}
  ]
}
```

```bash
aeryn batch projects.json
```

---

## 🧪 Testing

```bash
# All tests
./venv-proot/bin/python -m pytest tests/ -v

# Load testing
locust -f tests/load/locustfile.py --host=http://localhost:3010
```

---

## 📊 Test Coverage

```
648 tests pass
0 failures
1 warning
```

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*
