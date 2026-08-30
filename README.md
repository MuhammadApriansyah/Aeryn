# 🤖 Aeryn — Personal Assistant Agent SaaS

> AI-powered personal assistant platform with **5,600+ source files**, **661 tests**, 18+ major versions, and a fully adaptive recursive self-improvement system.

---

## 📊 Stats

![Version](https://img.shields.io/badge/version-58.0-blue)
![Tests](https://img.shields.io/badge/tests-661%20passed-brightgreen)
![Security](https://img.shields.io/badge/security-layered-success)
![Fullstack](https://img.shields.io/badge/fullstack-engineer-success)
![Dashboard](https://img.shields.io/badge/dashboard-SPA-success)
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
![Accessibility](https://img.shields.io/badge/accessibility-WCAG%202.1%20AA-success)
![Theme](https://img.shields.io/badge/theme-dark%2Flight-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Rust](https://img.shields.io/badge/rust-1.75+-orange)
![Hermes](https://img.shields.io/badge/hermes-integrated-purple)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🎯 What is Aeryn?

Aeryn is an **AI personal assistant platform** built from the ground up with:

- **5 agent divisions** (Creative, Psychology, Reasoning, Governance, Infrastructure)
- **18 major versions** of continuous development (V40–V58)
- **661 automated tests** covering auth, billing, workspaces, plugins, security, and more
- **Fully adaptive system** with recursive self-improvement capabilities
- **SPA dashboard** with full WCAG 2.1 AA accessibility compliance

---

## 🚀 Quick Start

```bash
# Clone repo
git clone https://github.com/MuhammadApriysyah/Aeryn.git
cd Aeryn

# Setup backend
python3 -m venv venv-proot
source venv-proot/bin/activate
pip install -r requirements.txt

# Start backend + web UI
pm2 start apps/api/aeryn_api.py --name aeryn-api --interpreter ./venv-proot/bin/python

# Access Dashboard
open http://localhost:3010/web/
```

**Default ports:**
- Backend API: `http://localhost:3010`
- Web UI: `http://localhost:3010/web/`
- API Docs: `http://localhost:3010/docs`

---

## 📁 Project Structure

```
aeryn-core-agent/
├── aeryn_core/              # Core system (5,600+ files)
│   ├── agents/              # 5 cognitive divisions
│   │   ├── division_1_creative/    # POV + Style agents
│   │   ├── division_2_psych/       # Psychology agents
│   │   ├── division_3_reasoning/   # MCTS + FOL + Critique + Graph
│   │   ├── division_4_gov/         # Governance agents
│   │   └── division_5_infra/       # Sync + Validator agents
│   ├── adaptive/            # ✨ V58: Fully adaptive + self-improvement
│   ├── auth/                # Auth + billing + rate limiting
│   ├── cost/                # Token monitor + model router
│   ├── database/            # Neon PostgreSQL + Vector DB
│   ├── memory/              # Core + Social + Temporal + Vault
│   ├── platform/            # MCP + Webhooks + Cloud Sync
│   ├── reasoning/           # Self-improvement + Meta-evolution
│   ├── safety/              # 4-level sandbox + security hardening
│   └── utils/               # Config + Logger + Adapters
├── apps/
│   ├── api/                 # FastAPI backend (port 3010)
│   └── web/                 # SPA Dashboard (HTML/CSS/JS)
├── tests/                   # 661 tests (auth, billing, features)
├── plugins/                 # Plugin system
├── scripts/                 # Monitoring + reflection
└── docs/                    # Documentation
```

---

## 🎨 Features (V58.0)

### ✨ Fully Adaptive System (NEW)
- **Error Detection & Auto-Recovery**: 10+ recovery strategies for common failures
- **Fallback Chain Management**: Register fallback actions for resilient operations
- **Health Monitoring**: Real-time API, memory, and disk health checks
- **Recursive Self-Improvement Loop**: Runs every 60 minutes, analyzes error patterns, applies fixes
- **SQLite Logging**: All errors, adaptations, and health metrics stored in `data/adaptive_system.db`

### 🖥️ Modern Frontend (V58)
- **SPA Dashboard**: Single Page Application with zero JavaScript dependencies
- **Full Accessibility (WCAG 2.1 AA)**:
  - Skip links for keyboard navigation
  - Screen reader announcements (`aria-live="polite"`)
  - Focus management and visible focus rings
  - Keyboard-only navigation support
- **Dark/Light Theme**: Toggle with `localStorage` persistence
- **Keyboard Shortcuts**:
  | Shortcut | Action |
  |----------|--------|
  | `Ctrl+K` | Focus search |
  | `Ctrl+T` | Toggle theme |
  | `Ctrl+/` | Show help |
  | `Escape` | Blur search |
  | `Tab` | Skip to main content |
- **Toast Notifications**: Success, error, info, warning with auto-dismiss
- **Offline Detection**: Banner when backend API is unreachable
- **Loading Skeleton**: Shimmer animation during data fetch
- **Responsive Design**: Works on mobile and desktop
- **Real-time Health**: Dashboard polls backend every 5 seconds

### 🧬 5 Cognitive Divisions

| Division | Agents | Purpose |
|----------|--------|---------|
| **Creative** | POV, Style, Master | Content generation, creative writing |
| **Psychology** | Sub-agents, Master | Emotional intelligence, behavioral analysis |
| **Reasoning** | MCTS, FOL, Critique, Graph, Master | Logical reasoning, planning, verification |
| **Governance** | Sub-agents, Master | Compliance, policy enforcement |
| **Infrastructure** | Sync, Validator, Master | System synchronization, data validation |

### 🧠 Memory System
- **Core Memory**: Short-term working memory
- **Enhanced Memory**: Long-term storage with consolidation
- **Social Memory**: User relationship tracking
- **Temporal Memory**: Time-based memory with trend detection
- **Memory Vault**: Obsidian-style knowledge base
- **Memory Canary**: Anomaly detection for memory integrity

### 🔒 Security & Safety
- **4 Isolation Levels**: Basic → Namespace → Bubblewrap → Full
- **Prompt Injection Defense**: Multi-layer detection and blocking
- **Memory Guard**: Sensitive data encryption at rest
- **Adaptive Rule Engine**: Hot-reloadable security rules
- **Shadow Mode**: Test changes before applying to production

### 💰 Billing & Auth
- **Multi-tenant Workspaces**: Per-user data isolation
- **Role-Based Access Control**: Admin, user, guest roles
- **Usage Metering**: Track API usage per user
- **Rate Limiting**: Built-in API rate limiter (Python + Rust)
- **SSO Manager**: Single sign-on integration

### 🔌 Plugin System
- **Plugin Marketplace**: Share and download plugins
- **Hook System**: Extend core functionality
- **Skill Crystallization**: Auto-detect patterns and crystallize into skills
- **Plugin Docs**: Auto-generated documentation

### 📡 MCP Protocol
- **MCP Server**: Expose tools via Model Context Protocol
- **MCP Client**: Connect to external MCP servers
- **MCP Registry**: Discover and register MCP services

### 🌐 Multi-Region Deploy
- **Terraform Templates**: Infrastructure as code
- **AWS Multi-Region**: Deploy to multiple regions
- **Cloud Sync**: Sync data across regions

---

## 📡 API Endpoints

### Core
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (status, memory, version) |
| `/web/` | GET | SPA Dashboard |
| `/docs` | GET | Swagger API documentation |
| `/redoc` | GET | ReDoc API documentation |

### Adaptive System
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/adaptive/health` | GET | Health report (API, memory, disk) |
| `/api/adaptive/errors` | GET | Error summary (last 24h) |
| `/api/adaptive/adaptations` | GET | Adaptation summary (last 24h) |
| `/api/adaptive/run-cycle` | POST | Trigger manual improvement cycle |

### Improvement
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/improvement/feedback` | POST | Submit user feedback |
| `/improvement/report` | GET | Get improvement report |

### Monitoring
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/monitoring/sessions` | GET | Get all chat sessions |
| `/api/monitoring/history` | GET | Get conversation history |
| `/api/monitoring/stats` | GET | Get monitoring statistics |

---

## 📊 Test Coverage

```
661 tests pass
0 failures
1 warning (deprecated audioop)
```

### Test Categories

| Category | Tests | Coverage |
|----------|-------|----------|
| Auth & Billing | 15 | ✅ |
| Workspaces | 12 | ✅ |
| Plugins | 18 | ✅ |
| Features V50-V57 | 45 | ✅ |
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
pm2 logs aeryn-api          # Backend logs
pm2 restart aeryn-api       # Restart backend
pm2 save                    # Save PM2 config
pm2 monit                   # Monitor CPU/memory
```

---

## 🗺️ Roadmap

### Completed (V58.0)
- [x] SPA Dashboard with full accessibility
- [x] Fully adaptive system with recursive self-improvement
- [x] Error detection and auto-recovery
- [x] Health monitoring (API, memory, disk)
- [x] Dark/Light theme toggle
- [x] Keyboard shortcuts
- [x] Toast notifications
- [x] Offline detection
- [x] Loading skeleton

### Planned (V59.0)
- [ ] Next.js 16 integration (fix Turbopack Bus Error on ARM64)
- [ ] Projects page (CRUD operations)
- [ ] Chat page (conversational AI interface)
- [ ] Workspaces page (multi-tenant management)
- [ ] Plugins page (marketplace/browser)
- [ ] Audit Trail page (activity logging)

### Long-term
- [ ] Command palette (Cmd/Ctrl+Shift+P)
- [ ] Multi-tab navigation
- [ ] Offline mode with service worker
- [ ] PWA (Progressive Web App)
- [ ] Advanced search with fuzzy matching
- [ ] Notification center
- [ ] Onboarding flow for new users

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Changelog](CHANGELOG.md) | Version history (V40–V58) |
| [UI Recommendations](docs/ui-recommendations.md) | UI development roadmap |
| [Troubleshooting](docs/troubleshooting-nextjs-turbopack.md) | Next.js + Turbopack fixes |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Aeryn Platform                           │
├─────────────────────────────────────────────────────────────────┤
│  Frontend Layer                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ SPA Dashboard│  │ Web UI (V58) │  │ Next.js 16 (planned) │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  API Layer                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ FastAPI      │  │ Adaptive Sys │  │ MCP Server           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Core Layer                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ 5 Divisions  │  │ Memory Sys   │  │ Security Engine      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ PostgreSQL   │  │ Vector DB    │  │ PM2 Process Mgr      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 👤 Author

**Sen** — AI Engineer & Creator of Aeryn

*Built with ❤️ in Indonesia 🇮🇩*

---

## 📄 License

MIT
