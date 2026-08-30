# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with multi-model support, team workspaces, enterprise features, Rust-powered performance, Hermes integration, security-first architecture, MCP protocol, multi-agent orchestration, integration SDK, native sandbox, fullstack AI engineer mode, beginner-friendly UI, expert automation features, and **enterprise workspace management**.

![Version](https://img.shields.io/badge/version-55.0-blue)
![Tests](https://img.shields.io/badge/tests-653%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-layered-success)
![Fullstack](https://img.shields.io/badge/fullstack-engineer-success)
![Dashboard](https://img.shields.io/badge/dashboard-web-success)
![Templates](https://img.shields.io/badge/templates-custom-success)
![Debug](https://img.shields.io/badge/debug-mode-success)
![Headless](https://img.shields.io/badge/headless-mode-success)
![Batch](https://img.shields.io/badge/batch-generate-success)
![Workspace](https://img.shields.io/badge/workspace-multi--tenant-success)
![Audit](https://img.shields.io/badge/audit-trail-success)
![Cache](https://img.shields.io/badge/cache-redis-success)
![Queue](https://img.shields.io/badge/job-queue-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Rust](https://img.shields.io/badge/rust-1.75+-orange)
![Hermes](https://img.shields.io/badge/hermes-integrated-purple)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

### Enterprise Features (NEW in V55)
- **Workspace Management**: Multi-tenant workspaces with RBAC
- **Audit Trail**: Track all actions for compliance
- **Rate Limiting**: Built-in API rate limiter
- **Cache Layer**: Redis caching template
- **Job Queue**: Background job processing (Bull)

### Expert Automation (V54)
- **Headless Mode**: `--non-interactive` for CI/CD
- **Config File**: `.aerynrc` for project defaults
- **Batch Generate**: Multiple projects from JSON

### Beginner-Friendly UI (V47-V50)
- **Setup Wizard**: `aeryn start`
- **Visual Dashboard**: Web UI at port 3020
- **One-Click Generate**: Minimal questions
- **Post-Generate Guide**: Clear next steps
- **Progress Indicator**: Visual feedback
- **Error Solver**: Friendly error messages
- **One-Click Installer**: `./aeryn-installer.sh`

### Fullstack AI Engineer (V46)
- **Fullstack CLI**: `new`, `dev`, `db:migrate`, `db:seed`, `test`, `build`, `deploy`
- **Realistic Templates**: React + Fastify + SQLite
- **Migration System**: Database migrations with rollback

### Native Sandbox (V45)
- **Conditional Security**: Auto-detect → best isolation level
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
│   ├── workspace/           ← Multi-tenant workspace management
│   ├── audit_trail/         ← Audit trail for compliance
│   ├── rate_limiting/       ← Built-in API rate limiter
│   ├── cache_layer/         ← Redis caching template
│   ├── job_queue/           ← Background job processing
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
├── tests/                   ← 653 tests
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

```bash
# Option 1: Setup Wizard
aeryn start

# Option 2: One-Click Generate
aeryn new my-app --template react

# Option 3: Visual Dashboard
aeryn dashboard

# Option 4: Headless Mode
aeryn new my-app --non-interactive --template react

# Option 5: Batch Generate
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
| `aeryn workspace list` | List workspaces |
| `aeryn audit` | View audit trail |

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
    "ci_cd": true,
    "rate_limiting": true,
    "caching": true,
    "job_queue": false
  },
  "plugins": ["auth"],
  "environments": {
    "development": {"port": 3010},
    "staging": {"port": 3011},
    "production": {"port": 3012}
  }
}
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
653 tests pass
0 failures
1 warning
```

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*
