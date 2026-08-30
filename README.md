# 🤖 Aeryn — Personal AI Assistant Platform

> **5,600+ files · 661 tests · 18 major versions · WCAG 2.1 AA · Self-improving**

Aeryn is a **fully adaptive, recursive self-improving AI personal assistant platform** with 5 cognitive divisions, a memory system that evolves with you, enterprise-grade security, and a SPA dashboard accessible to everyone.

---

## 🚀 Quick Start

```bash
# 1. Clone & enter
git clone https://github.com/MuhammadApriysyah/Aeryn.git && cd Aeryn

# 2. Backend setup
python3 -m venv venv-proot && source venv-proot/bin/activate
pip install -r requirements.txt

# 3. Start everything (backend + web UI)
pm2 start apps/api/aeryn_api.py --name aeryn-api --interpreter ./venv-proot/bin/python

# 4. Open Dashboard
open http://localhost:3010/web/
```

| Service | URL |
|---------|-----|
| Backend API | `http://localhost:3010` |
| Web UI | `http://localhost:3010/web/` |
| API Docs (Swagger) | `http://localhost:3010/docs` |
| API Docs (ReDoc) | `http://localhost:3010/redoc` |

---

## 📊 Stats

![Version](https://img.shields.io/badge/version-58-87CEEB)
![Tests](https://img.shields.io/badge/tests-661%20passed-87CEEB)
![Security](https://img.shields.io/badge/security-layered-87CEEB)
![Fullstack](https://img.shields.io/badge/fullstack-engineer-87CEEB)
![Dashboard](https://img.shields.io/badge/dashboard-SPA-87CEEB)
![Templates](https://img.shields.io/badge/templates-custom-87CEEB)
![Debug](https://img.shields.io/badge/debug-mode-87CEEB)
![Headless](https://img.shields.io/badge/headless-mode-87CEEB)
![Batch](https://img.shields.io/badge/batch-generate-87CEEB)
![Workspace](https://img.shields.io/badge/workspace-multi--tenant-87CEEB)
![Audit](https://img.shields.io/badge/audit-trail-87CEEB)
![Cache](https://img.shields.io/badge/cache-redis-87CEEB)
![Queue](https://img.shields.io/badge/job-queue-87CEEB)
![Workflow](https://img.shields.io/badge/workflow-dsl-87CEEB)
![MultiRegion](https://img.shields.io/badge/multi--region-deploy-87CEEB)
![Tracing](https://img.shields.io/badge/distributed--tracing-87CEEB)
![APM](https://img.shields.io/badge/apm-monitoring-87CEEB)
![Accessibility](https://img.shields.io/badge/accessibility-WCAG%202.1%20AA-87CEEB)
![Theme](https://img.shields.io/badge/theme-dark%2Flight-87CEEB)
![Python](https://img.shields.io/badge/python-3.11+-87CEEB)
![Rust](https://img.shields.io/badge/rust-1.75+-87CEEB)
![Hermes](https://img.shields.io/badge/hermes-integrated-87CEEB)
![License](https://img.shields.io/badge/license-MIT-87CEEB)

---

## 🎯 What is Aeryn?

Aeryn is an **AI personal assistant platform** built from the ground up with:

- **5 agent divisions** (Creative, Psychology, Reasoning, Governance, Infrastructure)
- **18 major versions** of continuous development (V40–V58)
- **661 automated tests** covering auth, billing, workspaces, plugins, security, and more
- **Fully adaptive system** with recursive self-improvement capabilities
- **SPA dashboard** with full WCAG 2.1 AA accessibility compliance

### Why Aeryn?

Aeryn is designed to be **self-improving** — it learns from every interaction, adapts to your workflow, and gets smarter over time. With 5 cognitive divisions, persistent multi-layer memory, and a 4-level security sandbox, Aeryn is built for both personal and enterprise use.

---

## 📁 Project Structure

```
aeryn-core-agent/
├── aeryn_core/                    # Core system (5,600+ files)
│   ├── agents/                    # 5 cognitive divisions
│   │   ├── division_1_creative/   # POV + Style agents
│   │   ├── division_2_psych/      # Psychology agents
│   │   ├── division_3_reasoning/  # MCTS + FOL + Critique + Graph
│   │   ├── division_4_gov/        # Governance agents
│   │   └── division_5_infra/      # Sync + Validator agents
│   ├── adaptive/                  # ✨ Fully adaptive + self-improvement
│   ├── auth/                      # Auth + billing + rate limiting
│   ├── cost/                      # Token monitor + model router
│   ├── database/                  # Neon PostgreSQL + Vector DB
│   ├── memory/                    # Core + Social + Temporal + Vault
│   ├── platform/                  # MCP + Webhooks + Cloud Sync
│   ├── reasoning/                 # Self-improvement + Meta-evolution
│   ├── safety/                    # 4-level sandbox + security hardening
│   └── utils/                     # Config + Logger + Adapters
├── apps/
│   ├── api/                       # FastAPI backend (port 3010)
│   └── web/                       # SPA Dashboard (HTML/CSS/JS)
├── tests/                         # 661 tests (auth, billing, features)
├── plugins/                       # Plugin system
├── scripts/                       # Monitoring + reflection
└── docs/                          # Documentation
```

---

## 🎨 Features (V58.0)

### ✨ Fully Adaptive System (NEW)

| Component | Description |
|-----------|-------------|
| **Error Detection** | 10+ recovery strategies for common failures (ConnectionError, TimeoutError, MemoryError, etc.) |
| **Fallback Chains** | Register ordered fallback actions per component — system degrades gracefully |
| **Health Monitoring** | Real-time API, memory, and disk health checks via `/api/adaptive/health` |
| **Recursive Self-Improvement** | Runs every 60 min: analyze patterns → identify issues → apply fixes → log results |
| **SQLite Logging** | All errors, adaptations, health metrics in `data/adaptive_system.db` |
| **Screen Reader** | `announceToScreenReader()` for all critical UI state changes |

### 🖥️ Modern Frontend (V58)

| Feature | Details |
|---------|---------|
| **SPA Dashboard** | Zero JavaScript dependencies — pure HTML/CSS/JS |
| **Accessibility** | WCAG 2.1 AA compliant — skip links, ARIA labels, focus management, keyboard nav |
| **Dark/Light Theme** | Toggle with `localStorage` persistence, respects `prefers-color-scheme` |
| **Keyboard Shortcuts** | `Ctrl+K` search · `Ctrl+T` theme · `Ctrl+/` help · `Escape` blur · `Tab` skip-to-content |
| **Toast Notifications** | Success/error/info/warning with auto-dismiss and close button |
| **Offline Detection** | Banner when backend API is unreachable (polling every 10s) |
| **Loading Skeleton** | Shimmer animation while data fetches |
| **Responsive** | Mobile-first design, works on all screen sizes |
| **Real-time Health** | Dashboard polls backend every 5 seconds |

### 🧬 5 Cognitive Divisions

| Division | Sub-agents | Purpose |
|----------|------------|---------|
| **Creative** | POV, Style, Master | Content generation, creative writing, stylistic adaptation |
| **Psychology** | Sub-agents, Master | Emotional intelligence, behavioral analysis, mood detection |
| **Reasoning** | MCTS, FOL, Critique, Graph, Master | Logical reasoning, planning, theorem proving, verification |
| **Governance** | Sub-agents, Master | Compliance enforcement, policy management, audit trails |
| **Infrastructure** | Sync, Validator, Master | System synchronization, data validation, health monitoring |

### 🧠 Memory System

| Type | Description |
|------|-------------|
| **Core Memory** | Short-term working memory for current session |
| **Enhanced Memory** | Long-term storage with automatic consolidation |
| **Social Memory** | User relationship tracking and preferences |
| **Temporal Memory** | Time-based memory with trend detection and timeline queries |
| **Memory Vault** | Obsidian-style knowledge base with bidirectional linking |
| **Memory Canary** | Anomaly detection for memory integrity verification |

### 🔒 Security & Safety

| Layer | Description |
|-------|-------------|
| **Sandbox** | 4 isolation levels: Basic → Namespace → Bubblewrap → Full |
| **Prompt Injection** | Multi-layer detection and blocking (regex + LLM-based) |
| **Memory Guard** | Sensitive data encryption at rest |
| **Adaptive Rules** | Hot-reloadable security rules without restart |
| **Shadow Mode** | Test changes before applying to production |
| **Rate Limiting** | Built-in API rate limiter (Python + Rust) |

### 💰 Billing & Auth

| Feature | Description |
|---------|-------------|
| **Multi-tenant** | Per-user data isolation with workspace separation |
| **RBAC** | Admin, user, guest roles with granular permissions |
| **Usage Metering** | Per-user API usage tracking with cost calculation |
| **SSO** | Single sign-on integration manager |
| **Email Verification** | User email verification and password reset flows |

### 🔌 Plugin System

| Feature | Description |
|---------|-------------|
| **Marketplace** | Share and download plugins from community |
| **Hook System** | Pre/post action hooks for extending core functionality |
| **Skill Crystallization** | Auto-detect patterns and crystallize into reusable skills |
| **Plugin Docs** | Auto-generated documentation for installed plugins |

### 📡 MCP Protocol

| Component | Description |
|-----------|-------------|
| **MCP Server** | Expose Aeryn tools via Model Context Protocol |
| **MCP Client** | Connect to external MCP servers (Firecrawl, GitHub, etc.) |
| **MCP Registry** | Discover and register MCP services |

### 🌐 Multi-Region Deploy

| Feature | Description |
|---------|-------------|
| **Terraform** | Infrastructure as code templates |
| **AWS Multi-Region** | Deploy to multiple AWS regions with single command |
| **Cloud Sync** | Sync data and state across regions |

---

## 📡 API Endpoints

### Core

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check: `{"status":"healthy","memory_mb":65.5,"version":"40.44"}` |
| `/web/` | GET | SPA Dashboard |
| `/docs` | GET | Swagger API documentation |
| `/redoc` | GET | ReDoc API documentation |

### Adaptive System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/adaptive/health` | GET | Full health report (API, memory, disk) |
| `/api/adaptive/errors` | GET | Error summary for last N hours |
| `/api/adaptive/adaptations` | GET | Adaptation summary for last N hours |
| `/api/adaptive/run-cycle` | POST | Manually trigger a self-improvement cycle |

### Improvement & Feedback

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/improvement/feedback` | POST | Submit user feedback for an interaction |
| `/improvement/report` | GET | Get improvement report with suggestions |

### Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/monitoring/sessions` | GET | Get all chat sessions |
| `/api/monitoring/history` | GET | Get conversation history for a session |
| `/api/monitoring/stats` | GET | Get monitoring statistics |

---

## 📊 Test Coverage

```
661 tests pass · 0 failures · 1 warning (deprecated audioop)
```

### By Category

| Category | Tests | Coverage |
|----------|-------|----------|
| Auth & Billing | 15 | ✅ |
| Workspaces | 12 | ✅ |
| Plugins | 18 | ✅ |
| Features V50–V57 | 45 | ✅ |
| Security & Cost | 20 | ✅ |
| Core Reasoning | 35 | ✅ |
| Agent Divisions | 28 | ✅ |
| MCP & Multi-Agent | 12 | ✅ |
| Sandbox | 10 | ✅ |
| Other | 526 | ✅ |

---

## 📋 PM2 Commands

```bash
pm2 list                    # List all processes
pm2 logs aeryn-api          # Backend logs (live)
pm2 logs aeryn-api --lines 100  # Last 100 lines
pm2 restart aeryn-api       # Restart backend
pm2 save                    # Save PM2 config
pm2 monit                   # Interactive CPU/memory monitor
pm2 delete aeryn-api        # Remove from PM2
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Aeryn Platform                                    │
├──────────────────────────────────────────────────────────────────────────┤
│  Frontend Layer                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐  │
│  │ SPA Dashboard  │  │  Web UI (V58)  │  │  Next.js 16 (planned V59)  │  │
│  │  HTML/CSS/JS   │  │  Accessible    │  │  Turbopack + React 19      │  │
│  └────────────────┘  └────────────────┘  └────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────────┤
│  API Layer                                                               │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐  │
│  │ FastAPI        │  │ Adaptive Sys   │  │  MCP Server                │  │
│  │ port 3010      │  │ Self-improving │  │  Model Context Protocol    │  │
│  └────────────────┘  └────────────────┘  └────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────────┤
│  Core Layer                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐  │
│  │ 5 Divisions    │  │ Memory System   │  │  Security Engine           │  │
│  │ 12+ agents     │  │ 6 types        │  │  4-level sandbox           │  │
│  └────────────────┘  └────────────────┘  └────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────────┤
│  Infrastructure                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐  │
│  │ PostgreSQL     │  │ Vector DB       │  │  PM2 Process Manager       │  │
│  │ Neon Cloud     │  │ pgvector 0.8.6  │  │  Auto-restart              │  │
│  └────────────────┘  └────────────────┘  └────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🗺️ Roadmap

### V58.0 (Current — Released 2026-08-30)

- [x] SPA Dashboard with full WCAG 2.1 AA accessibility
- [x] Fully adaptive system with recursive self-improvement loop
- [x] Error detection & auto-recovery (10+ strategies)
- [x] Health monitoring (`/api/adaptive/health`)
- [x] Dark/Light theme toggle
- [x] Keyboard shortcuts (`Ctrl+K`, `Ctrl+T`, `Ctrl+/`)
- [x] Toast notifications
- [x] Offline detection banner
- [x] Loading skeleton with shimmer animation
- [x] Responsive design (mobile + desktop)
- [x] PM2 integration

### V59.0 (Next)

- [ ] Fix Next.js 16 + Turbopack Bus Error on ARM64
- [ ] Projects page with CRUD operations
- [ ] Chat page with conversational AI interface
- [ ] Workspaces page with multi-tenant management
- [ ] Plugins page with marketplace/browser
- [ ] Audit Trail page with activity logging
- [ ] Notification center with badge counts

### V60.0 (Long-term)

- [ ] Command palette (`Cmd/Ctrl+Shift+P`)
- [ ] Multi-tab navigation
- [ ] Offline mode with service worker
- [ ] PWA (Progressive Web App) installable
- [ ] Advanced search with fuzzy matching
- [ ] Onboarding flow for new users
- [ ] Multi-region cloud sync
- [ ] Advanced monitoring (Prometheus + Grafana)

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Changelog](CHANGELOG.md) | Version history (V40–V58) |
| [UI Recommendations](docs/ui-recommendations.md) | UI development roadmap with design tokens |
| [Troubleshooting](docs/troubleshooting-nextjs-turbopack.md) | Next.js + Turbopack fixes |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+, FastAPI, Uvicorn, PM2 |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (zero dependencies) |
| **Database** | PostgreSQL (Neon), SQLite (local), pgvector |
| **Security** | 4-level sandbox, prompt injection defense, encryption |
| **Monitoring** | PM2, custom health checks, distributed tracing |
| **Deployment** | Docker, Terraform, AWS, multi-region |

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/my-feature`
3. Run tests: `pytest tests/ -x`
4. Commit changes: `git commit -m "Add my feature"`
5. Push: `git push origin feature/my-feature`
6. Open Pull Request

---

## 💡 Philosophy

> "Aeryn grows with you."

Aeryn is designed to be:
- **Self-improving**: Every interaction makes it smarter
- **Accessible**: Usable by everyone, regardless of ability
- **Resilient**: Graceful degradation, never full failure
- **Open**: MIT licensed, self-hostable, community-driven
- **Adaptive**: Changes behavior based on feedback and patterns

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*

---

## 📄 License

[MIT](LICENSE)
