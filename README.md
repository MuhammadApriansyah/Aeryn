# 🤖 Aeryn — Personal AI Assistant Platform

> **5,600+ files · 661 tests · 18 major versions · WCAG 2.1 AA · Self-improving · Adaptive**

Aeryn is a **fully adaptive, recursive self-improving AI personal assistant platform** with 5 cognitive divisions, a memory system that evolves with you, enterprise-grade security, and a SPA dashboard accessible to everyone.

---

## 🚀 Quick Start

```bash
# 1. Clone & enter
git clone https://github.com/MuhammadApriansyah/Aeryn.git && cd Aeryn

# 2. Backend setup
python3 -m venv venv-proot && source venv-proot/bin/activate
pip install -r requirements.txt

# 3. Start everything (backend + web UI)
pm2 start ecosystem.config.cjs

# 4. Open Dashboard
open http://localhost:3010/
```

| Service | URL |
|---------|-----|
| Backend API | `http://localhost:3010` |
| API v1 (versioned) | `http://localhost:3010/v1/` |
| Web UI | `http://localhost:3010/` |
| API Docs (Swagger) | `http://localhost:3010/docs` |
| Gateway Status | `http://localhost:3010/gateway/env` |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AERYN_ENV` | `proot` | Runtime environment: `proot`, `vps`, `k8s`, `docker` |
| `AERYN_BASE_DIR` | `~/aeryn-core-agent` | Project root (portable path) |
| `AERYN_PORT` | `3010` | API port |
| `AERYN_HOST` | `127.0.0.1` | API host |
| `DATABASE_URL` | (none) | PostgreSQL connection (optional, falls back to SQLite) |
| `TZ` | `UTC` | Timezone (e.g. `Asia/Jakarta`) |
| `TELEGRAM_BOT_TOKEN` | (none) | Telegram bot token (optional) |
| `DISCORD_BOT_TOKEN` | (none) | Discord bot token (optional) |
| `SLACK_BOT_TOKEN` | (none) | Slack bot token (optional) |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host for memory plugin |
| `POSTGRES_DB` | `sen` | PostgreSQL database name |
| `POSTGRES_USER` | `sen` | PostgreSQL username |
| `POSTGRES_PASSWORD` | (none) | PostgreSQL password |

---

## 📊 Stats

![Version](https://img.shields.io/badge/version-61.4-87CEEB)
![Dimensions](https://img.shields.io/badge/dimensions-11/11-brightgreen)
![Sources](https://img.shields.io/badge/sources_analyzed-8-blue)
![Dashboard](https://img.shields.io/badge/dashboard-ajbury--inspired-success)
![Tests](https://img.shields.io/badge/tests-661%20passed-87CEEB)
![Security](https://img.shields.io/badge/security-layered-87CEEB)
![Accessibility](https://img.shields.io/badge/accessibility-WCAG%202.1%20AA-87CEEB)
![Python](https://img.shields.io/badge/python-3.11+-87CEEB)
![License](https://img.shields.io/badge/license-MIT-87CEEB)

---

## 🎯 What is Aeryn?

Aeryn is an **AI personal assistant platform** built from the ground up with:

- **5 agent divisions** (Creative, Psychology, Reasoning, Governance, Infrastructure)
- **19 major versions** of continuous development (V40–V61)
- **661 automated tests** covering auth, billing, workspaces, plugins, security, and more
- **Fully adaptive system** with recursive self-improvement capabilities
- **SPA dashboard** with full WCAG 2.1 AA accessibility compliance
- **PostgreSQL-backed memory** with semantic search and auto-save/load
- **Multi-platform messaging** via Telegram, Discord, and Slack

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
│   └── web/                       # SPA Dashboard (HTML/CSS/SS)
├── tests/                         # 661 tests (auth, billing, features)
├── plugins/                       # Plugin system + built-in plugins
│   ├── code-review/               # Python code analysis
│   ├── research-assistant/        # Vault search & summarize
│   ├── postgres-memory/           # PostgreSQL-backed memory
│   ├── messaging-gateway/         # Telegram/Discord/Slack
│   └── experience-transfer/       # Hermes → Aeryn learning
├── scripts/                       # Monitoring + reflection
└── docs/                          # Documentation
```

---

## 🎨 Features (V61.4)

### ✨ PostgreSQL Memory Plugin (NEW)

| Feature | Description |
|---------|-------------|
| **Auto-save** | Session summaries automatically saved to PostgreSQL |
| **Semantic Search** | pgvector-powered similarity search across all memories |
| **Tiered Storage** | Hot (7d) → Warm (30d) → Cold (90d) → Pruned |
| **Entity Tracking** | Automatic entity extraction and relationship mapping |
| **Fast Mode** | Skip embedding for instant response |
| **Fallback Recall** | Falls back to vault search when episodes.jsonl missing |

### 📡 Messaging Gateway (NEW)

| Platform | Status | Features |
|----------|--------|----------|
| **Telegram** | ✅ | Bot API, inline keyboards, webhook support |
| **Discord** | ✅ | Slash commands, embeds, role-based permissions |
| **Slack** | ✅ | Web API, interactive blocks, URL verification |

### 🧬 Experience Transfer (NEW)

| Feature | Description |
|---------|-------------|
| **Pattern Extraction** | Extract successful task patterns from Hermes sessions |
| **User Preferences** | Learn language, style, and workflow preferences |
| **Task Templates** | Reuse proven task completion templates |
| **System Prompt Enhancement** | Auto-generate context-aware system prompts |

### 🖥️ Modern Frontend

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
| **Error Boundary** | Graceful error fallback with reload + go-home options |
| **Empty States** | Custom empty states for all pages (Projects, Chat, Plugins, etc.) |
| **Command Palette** | `Ctrl+Shift+P` fuzzy search across all features |
| **Notification Center** | Full notification management with read/unread + badge |

### 🧠 Memory System

| Type | Description |
|------|-------------|
| **Core Memory** | Short-term working memory for current session |
| **Enhanced Memory** | Long-term storage with automatic consolidation |
| **Social Memory** | User relationship tracking and preferences |
| **Temporal Memory** | Time-based memory with trend detection and timeline queries |
| **Memory Vault** | Obsidian-style knowledge base with bidirectional linking |
| **PostgreSQL Memory** | Unlimited storage with semantic search and auto-lifecycle |

### 🔒 Security & Safety

| Layer | Description |
|-------|-------------|
| **Sandbox** | 4 isolation levels: Basic → Namespace → Bubblewrap → Full |
| **Prompt Injection** | Multi-layer detection and blocking (regex + LLM-based) |
| **Memory Guard** | Sensitive data encryption at rest |
| **Adaptive Rules** | Hot-reloadable security rules without restart |
| **Shadow Mode** | Test changes before applying to production |
| **Rate Limiting** | Built-in API rate limiter |

### 🔌 Plugin System

| Feature | Description |
|---------|-------------|
| **Marketplace** | Share and download plugins from community |
| **Hook System** | Pre/post action hooks for extending core functionality |
| **Skill Crystallization** | Auto-detect patterns and crystallize into reusable skills |
| **Plugin Runner** | Execute plugins via API with JSON input/output |
| **CLI Entry Points** | Plugins can be run standalone via `python3 main.py` |

---

## 📡 API Endpoints

### Core

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check: `{"status":"healthy","memory_mb":65.5,"version":"61.0"}` |
| `/` | GET | SPA Dashboard |
| `/docs` | GET | Swagger API documentation |
| `/redoc` | GET | ReDoc API documentation |

### Chat & Execution

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Chat with Aeryn (LLM response) |
| `/run` | POST | Execute a task with tool routing |
| `/compile` | POST | Compile Python code |
| `/search` | GET | Search vault entries |
| `/digest` | POST | Generate digest/summary |

### Divisions & Workflows

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/divisions` | GET | List all divisions |
| `/divisions/{name}/execute` | POST | Execute tasks on a division |
| `/workflows` | GET | List workflows |
| `/workflows/{id}/step` | POST | Advance workflow step |

### PostgreSQL Memory

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/postgres-memory/stats` | GET | Memory statistics |
| `/v1/postgres-memory/remember` | POST | Store a memory |
| `/v1/postgres-memory/recall` | GET | Semantic search |
| `/v1/postgres-memory/sessions` | GET | Search sessions |
| `/v1/postgres-memory/session` | POST | Save session summary |
| `/v1/postgres-memory/forget` | DELETE | Remove a memory |

### Messaging Gateway

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/messaging/status` | GET | Gateway status |
| `/v1/messaging/webhook/{platform}` | POST | Handle incoming webhook |
| `/v1/messaging/send/{platform}` | POST | Send message to platform |

### Experience Transfer

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/experience/status` | GET | Transfer status |
| `/v1/experience/lessons` | GET | Get extracted lessons |
| `/v1/experience/preferences` | GET | Get user preferences |
| `/v1/experience/initialize` | POST | Initialize fine-tuning |

---

## ♿ Accessibility

Aeryn is built with **WCAG 2.1 AA** compliance in mind. Here's how we ensure everyone can use it:

### Visual

- **Color Contrast**: All text meets 4.5:1 contrast ratio (AA standard)
- **Color Independence**: Information never conveyed by color alone
- **Text Resizing**: Interface works at 200% zoom without horizontal scroll
- **Focus Indicators**: Visible focus rings on all interactive elements

### Keyboard

- **Full Navigation**: Every feature accessible via keyboard
- **Skip Links**: "Skip to main content" link at top of page
- **Focus Trap**: Modals trap focus and return focus on close
- **Shortcuts**: `Ctrl+K` search, `Escape` close, `Tab` navigation

### Screen Reader

- **ARIA Labels**: All interactive elements have descriptive labels
- **Live Regions**: Dynamic content announced via `aria-live`
- **Semantic HTML**: Proper heading hierarchy and landmark roles
- **Alt Text**: All images have descriptive alternative text

### Motor

- **Large Targets**: Minimum 44x44px touch targets
- **No Time Limits**: No auto-refresh or time-limited interactions
- **Error Prevention**: Confirmation dialogs for destructive actions

### Cognitive

- **Plain Language**: Simple, clear Indonesian and English
- **Consistent Navigation**: Same layout across all pages
- **Error Messages**: Clear, actionable error descriptions
- **Help Context**: Contextual help available everywhere

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
│  │ SPA Dashboard  │  │  Web UI (V61)  │  │  Mobile Responsive         │  │
│  │  HTML/CSS/JS   │  │  Accessible    │  │  PWA-ready                 │  │
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
│  │ + pgvector     │  │ pgvector 0.8.6  │  │  Auto-restart              │  │
│  └────────────────┘  └────────────────┘  └────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🗺️ Roadmap

### V61.4 (Current — Released 2026-09-01)

- [x] PostgreSQL Memory Plugin with semantic search
- [x] Messaging Gateway (Telegram, Discord, Slack)
- [x] Experience Transfer from Hermes sessions
- [x] Runtime fixes (plugins, memory, observability, divisions)
- [x] Web UI V61.4 with memory tab and plugin runner
- [x] Async/await fixes throughout orchestration
- [x] Duplicate endpoint cleanup

### V62.0 (Next)

- [ ] Advanced analytics dashboard with charts
- [ ] Multi-model support (GPT-4, Claude, Gemini, local)
- [ ] Voice interaction (STT/TTS)
- [ ] Mobile app (React Native)
- [ ] Plugin marketplace with community plugins
- [ ] Advanced workflow builder with visual editor

### V63.0 (Long-term)

- [ ] Multi-region cloud sync
- [ ] Advanced monitoring (Prometheus + Grafana)
- [ ] PWA (Progressive Web App) installable
- [ ] Offline mode with service worker
- [ ] Onboarding flow for new users
- [ ] Enterprise features (SSO, audit logs, compliance)

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Changelog](CHANGELOG.md) | Version history (V40–V61) |
| [UI Recommendations](docs/ui-recommendations.md) | UI development roadmap with design tokens |
| [Troubleshooting](docs/troubleshooting-nextjs-turbopack.md) | Next.js + Turbopack fixes |
| [Design V61.3](DESIGN_V61.3.md) | Dashboard design document |
| [PostgreSQL Memory](DESIGN_HERMES_POSTGRES_MEMORY.md) | Memory plugin design |

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
