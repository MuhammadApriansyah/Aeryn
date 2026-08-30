# Onboarding Guide (V59)

> **Purpose**: Get new users up and running with Aeryn in 5 minutes.
> **Rule**: Real setup steps — follows the actual development workflow.

---

## 🚀 5-Minute Quick Start

### Prerequisites

- Linux (Ubuntu 20.04+, tested on 25.10 ARM64)
- Python 3.11+
- 4GB+ RAM (11GB+ recommended)
- git

### Step 1: Clone Repository

```bash
git clone https://github.com/MuhammadApriansyah/Aeryn.git
cd Aeryn
```

### Step 2: Set Up Environment

```bash
# Create virtual environment
python3 -m venv venv-proot

# Activate
source venv-proot/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Start Aeryn

```bash
# Start the API server
pm2 start apps/api/aeryn_api.py --name aeryn-api --interpreter ./venv-proot/bin/python
```

### Step 4: Verify Installation

```bash
# Check health
curl http://127.0.0.1:3010/health
# Expected: {"status":"healthy","memory_mb":24.3,"version":"40.44"}

# Open dashboard
open http://localhost:3010
```

---

## 🎯 First Actions

### 1. Check System Health

Open `http://localhost:3010` in your browser. You should see the dashboard with:
- Backend status: **healthy**
- Memory usage
- API version

### 2. Send Your First Message

```bash
curl -X POST http://127.0.0.1:3010/chat \
  -H "Content-Type: application/json" \
  -d '{"goal":"Hello Aeryn, what can you do?","session_id":"welcome"}'
```

### 3. Run Your First Goal

```bash
curl -X POST http://127.0.0.1:3010/run \
  -H "Content-Type: application/json" \
  -d '{"goal":"Search the knowledge base for FastAPI best practices","session_id":"welcome"}'
```

### 4. Search Knowledge

```bash
curl "http://127.0.0.1:3010/search?q=FastAPI&limit=5"
```

---

## 📚 Learning Resources

### Documentation

| Guide | Description |
|-------|-------------|
| `CLAUDE.md` | Project overview for AI agents |
| `AGENTS.md` | Project structure & conventions |
| `docs/ai-coding-checklist.md` | Pre-flight checklist |
| `docs/prompts/` | System and user prompt templates |
| `docs/api/api-reference.md` | Full API endpoint reference |
| `docs/api/plugins.md` | Plugin system guide |
| `docs/billing/billing.md` | Billing and pricing |

### Tutorial Path

1. **Hello World**: Send your first chat message
2. **Run a Goal**: Execute a complex task
3. **Search Knowledge**: Find existing information
4. **Create a Project**: Use the SPA dashboard
5. **Install a Plugin**: Extend Aeryn's capabilities
6. **Write a Plugin**: Create your own extension

---

## 🎨 Dashboard Tour

### Navigation

The dashboard has 7 sections:

1. **Dashboard** (📊) — System health, quick actions
2. **Projects** (📁) — Create and manage AI projects
3. **Workspaces** (🏢) — Multi-tenant workspace management
4. **Chat** (💬) — Conversational interface
5. **Plugins** (🧩) — Plugin management
6. **Audit Trail** (📋) — Activity logs
7. **Settings** (⚙️) — Theme, shortcuts, preferences

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Search |
| `Ctrl+T` | Toggle theme |
| `Ctrl+Shift+P` | Command palette |
| `Ctrl+/` | Help |

---

## 🔧 Troubleshooting

### Backend Not Starting

```bash
# Check if port is in use
lsof -i :3010

# Kill and restart
fuser -k 3010/tcp
pm2 restart aeryn-api

# Check logs
pm2 logs aeryn-api
```

### PostgreSQL Errors

> ⚠️ **This is expected.** Aeryn uses SQLite, not PostgreSQL.

PostgreSQL connection errors in logs are **by design** — the system catches them and falls back to SQLite automatically. No action needed unless you see actual failures.

### Dashboard Not Loading

```bash
# Check static files
curl http://127.0.0.1:3010/web/static/css/dashboard.css
curl http://127.0.0.1:3010/web/static/js/dashboard.js

# Restart server
pm2 restart aeryn-api
```

---

## 🧪 Running Tests

```bash
# Full suite (661 tests — must pass)
python -m pytest tests/ -x -q

# Specific test file
python -m pytest tests/test_auth.py -x -q

# Verbose
python -m pytest tests/ -x -v
```

---

## 📦 Project Structure

```
aeryn-core-agent/
├── aeryn_core/          # Core system (5,600+ files)
├── apps/api/            # FastAPI backend
├── apps/web/            # SPA Dashboard
├── tests/               # 661 automated tests
├── docs/                # Documentation
├── plugins/             # Plugin system
├── venv-proot/          # Python environment
└── requirements.txt     # Dependencies
```

---

## 🆘 Getting Help

1. **Check docs**: Look in `/docs/` for relevant guides
2. **Run health check**: `curl http://127.0.0.1:3010/health`
3. **Check logs**: `pm2 logs aeryn-api`
4. **Search memory**: Look in vault or memory system
5. **Ask Aeryn**: Send a question via `/chat` endpoint

---

*Onboarding guide v59.0 — Updated 2026-08-30.*
