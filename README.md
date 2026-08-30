# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with multi-model support, team workspaces, enterprise features, Rust-powered performance, Hermes integration, security-first architecture, MCP protocol, multi-agent orchestration, integration SDK, native sandbox, fullstack AI engineer mode, beginner-friendly UI, expert automation features, enterprise workspace management, advanced workflow automation, production-grade observability, and **Next.js 16 + Turbopack** frontend.

![Version](https://img.shields.io/badge/version-58.0-blue)
![Tests](https://img.shields.io/badge/tests-661%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-layered-success)
![Fullstack](https://img.shields.io/badge/fullstack-engineer-success)
![Dashboard](https://img.shields.io/badge/dashboard-next.js%2016-success)
![Templates](https://img.shields.io/badge/templates-custom-success)
![Debug](https://img.shields.io/badge/debug-mode-success)
![Headless](https://img.shields.io/badge/headless-mode-success)
![Batch](https://img.shields.io/badge/batch-generate-success)
![Workspace](https://img.shields.io/badge/workspace-multi--tenant-success)
![Audit](https://img.shields.io/badge/audit-trail-success)
![Cache](https://img.shields.io/badge/cache-redis-success)
![Queue](https://img.shields.io/badge/job-queue-success)
![Workflow](https://img.shields.io/badge/workflow-dsl-success)
![MultiRegion](https://img.shields.io/badge/multi--region-deploy-success)
![Tracing](https://img.shields.io/badge/distributed--tracing-success)
![APM](https://img.shields.io/badge/apm-monitoring-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Rust](https://img.shields.io/badge/rust-1.75+-orange)
![Hermes](https://img.shields.io/badge/hermes-integrated-purple)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

### Modern Frontend (NEW in V58)
- **Next.js 16 + Turbopack**: Modern React frontend with Turbopack bundler
- **API Proxy**: Next.js API routes proxy to FastAPI backend
- **Real-time Health Check**: Dashboard polls backend every 5 seconds
- **PM2 Integration**: Both frontend and backend managed by PM2

### Production-Grade Observability (V57)
- **Multi-Region Deploy**: Deploy to multiple AWS regions with Terraform
- **Distributed Tracing**: OpenTelemetry + Jaeger integration
- **Advanced Monitoring APM**: Prometheus metrics + Grafana dashboards

### Advanced Workflow Automation (V56)
- **Workflow DSL**: Define custom generation workflows with YAML/JSON
- **Headless Mode**: `--non-interactive` for fully automated CI/CD
- **Config File**: `.aerynrc` for project defaults with dot notation
- **Batch Generate**: Generate multiple projects from JSON config
- **Template Inheritance**: Extend templates from other templates
- **Custom Generators**: Replace default generators with custom logic

### Enterprise Features (V55)
- **Workspace Management**: Multi-tenant workspaces with RBAC
- **Audit Trail**: Track all actions for compliance
- **Rate Limiting**: Built-in API rate limiter
- **Cache Layer**: Redis caching template
- **Job Queue**: Background job processing (Bull)

### Beginner-Friendly UI (V47-V50)
- **Setup Wizard**: `aeryn start`
- **Visual Dashboard**: Web UI at port 3020
- **One-Click Generate**: Minimal questions
- **Error Solver**: Friendly error messages

### Fullstack AI Engineer (V46)
- **Fullstack CLI**: `new`, `dev`, `db:migrate`, `db:seed`, `test`, `build`, `deploy`
- **Realistic Templates**: React + Fastify + SQLite
- **Migration System**: Database migrations with rollback

### Native Sandbox (V45)
- **Conditional Security**: Auto-detect → best isolation level
- **4 Isolation Levels**: Basic → Namespace → Bubblewrap → Full

### MCP Protocol (V43)
- **MCP Server/Client**: Standard compliance

### Security-First (V42)
- **Prompt Injection Defense**: Input sanitization, output validation
- **Memory Injection Defense**: Integrity verification
- **Tool Permission Limits**: Risk-based access
- **Model Routing**: Tiered selection (60-70% cost reduction)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16 + Turbopack, React 19, CSS3 |
| **Backend** | Python 3.11+, FastAPI |
| **Engine** | Rust 1.75+ (PyO3) |
| **Database** | SQLite (local) + PostgreSQL/Neon (cloud) |
| **Authentication** | JWT + API Keys |
| **AI/LLM** | Gemini, OpenRouter, DeepSeek (fallback) |
| **Protocol** | MCP (Model Context Protocol) |
| **Build System** | uv + Maturin (PyO3), npm |
| **CI/CD** | GitHub Actions |
| **Deployment** | PM2, Docker |

---

## 🚀 Quick Start

```bash
# Clone repo
git clone https://github.com/MuhammadApriysyah/Aeryn.git
cd Aeryn

# Setup backend (Python)
python3 -m venv venv-proot
source venv-proot/bin/activate
pip install -r requirements.txt

# Setup frontend (Next.js)
cd aeryn-web
npm install

# Build frontend
NODE_OPTIONS="--max-old-space-size=512" npm run build

# Start both with PM2
cd ..
pm2 start ecosystem.config.cjs    # Backend
pm2 start ecosystem-web.config.cjs # Frontend

# Access dashboard
open http://localhost:3020
```

---

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `POST /chat` | Chat with Aeryn |
| `GET /search` | Hybrid search |
| `POST /run` | Run agent task |
| `GET /dashboard/stream` | SSE stream |
| `WS /ws/dashboard` | WebSocket |

---

## 📋 PM2 Commands

```bash
pm2 list              # List all processes
pm2 logs aeryn-api    # Backend logs
pm2 logs aeryn-web    # Frontend logs
pm2 restart aeryn-api # Restart backend
pm2 restart aeryn-web # Restart frontend
pm2 save              # Save config
```

---

## 📚 Architecture

```
Aeryn/
├── aeryn-web/               ← Next.js 16 Frontend (NEW)
│   ├── src/
│   │   ├── app/
│   │   │   ├── api/         ← API routes (proxy)
│   │   │   ├── page.jsx     ← Dashboard
│   │   │   └── layout.jsx
│   │   └── components/
│   └── package.json
├── apps/
│   └── api/
│       └── aeryn_api.py     ← FastAPI Backend
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
│   ├── workflow_dsl/        ← Workflow DSL
│   ├── config_file_v2/      ← Enhanced config file
│   ├── template_inheritance/← Template inheritance
│   ├── custom_generators/   ← Custom generators
│   └── ...
├── aeryn-engine/            ← Rust (6 modules)
├── plugins/aeryn-core/      ← Hermes plugin entry
├── tests/                   ← 658+ tests
├── .github/workflows/       ← CI/CD Pipeline
├── Dockerfile + compose     ← Docker support
├── ecosystem.config.cjs     ← PM2 backend config
├── ecosystem-web.config.cjs ← PM2 frontend config
└── monitoring/              ← Metrics collector
```

---

## 📊 Test Coverage

```
661 tests pass
0 failures
1 warning
```

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*
