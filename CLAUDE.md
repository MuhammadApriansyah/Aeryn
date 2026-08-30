# Aeryn — Personal AI Assistant Platform

## Project Overview

Aeryn is a comprehensive personal AI assistant platform with 5,600+ files, 661 tests, and version V59.0. It provides a multi-agent cognitive architecture, adaptive self-improvement system, full-stack SPA dashboard, and API gateway. The system manages memory, reasoning, billing, plugins, multi-agent orchestration, and more.

**Key stats:**
- **Files:** 5,600+ (5,600 Python, 4,723 JS, 12 HTML, 5 CSS)
- **API file size:** 4,182 lines (aeryn_api.py)
- **Dashboard file size:** 964 lines (dashboard.js)
- **Tests:** 91 test files, 661 total tests
- **Version:** V59.0

## Tech Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.11 |
| Server | FastAPI + Uvicorn |
| Database | SQLite with WAL mode |
| Frontend | Vanilla HTML/CSS/JS SPA (zero dependencies) |
| Process Manager | PM2 (Node.js-based) |
| Config | ecosystem.config.cjs, .env |
| Architecture | Monolithic FastAPI + vanilla SPA |

## Working Directory

```
/home/sen/aeryn-core-agent
```

## Environment

- **OS:** ARM64 Ubuntu 25.10
- **RAM:** 11 GB
- **Virtual environment:** `venv-proot/` (Python 3.11)
- **No Docker** — all services run directly on host
- **No PostgreSQL** — SQLite only (WAL mode with busy_timeout)

## Key Commands

### Start API server
```bash
cd /home/sen/aeryn-core-agent
pm2 start apps/api/aeryn_api.py --name aeryn-api --interpreter ./venv-proot/bin/python
```

### Run tests
```bash
cd /home/sen/aeryn-core-agent
source venv-proot/bin/activate
python -m pytest tests/ -x -q
```

### Check PM2 status
```bash
pm2 status
pm2 logs aeryn-api
```

### Restart services
```bash
pm2 restart aeryn-api
pm2 restart aeryn-dashboard
```

## Critical Rules

1. **NO test doubles in production code.** Real testing only — no mocks, stubs, or fakes in production code paths. Tests use real implementations.
2. **SQLite only.** Never add PostgreSQL code or dependencies.
3. **Zero JS dependencies.** Frontend is vanilla HTML/CSS/JS — no npm packages, no build step.
4. **PM2 for process management.** Use ecosystem.config.cjs for configuration.
5. **WAL mode.** All SQLite connections go through `aeryn_core.utils.patch_sqlite` which enables WAL mode + busy_timeout.

## Architecture

- `apps/api/aeryn_api.py` — Monolithic FastAPI backend (4,182 lines)
- `apps/web/static/` — SPA frontend (HTML/CSS/JS)
- `aeryn_core/` — Core library (76 subdirectories)
  - `agents/` — 5 cognitive divisions with master/sub-agents
  - `memory/` — Memory system (vault, hybrid search, temporal, social, graph)
  - `reasoning/` — Reasoning engines (dream synthesis, constitutional AI, planner)
  - `auth/` — Authentication (API keys, SSO, rate limiting, billing)
  - `safety/` — Safety systems (engine, guardrails, sandbox, OWASP)
  - `platform/` — Platform features (MCP, plugins, multi-agent, browser, Discord)
  - `utils/` — Utilities (error recovery, logging, performance, config)
  - `adaptive/` — Self-improvement system (auto-recovery, learning, health)

## API Endpoints

Base URL: `http://127.0.0.1:3010`

Key endpoints:
- `POST /auth/login` — Bearer token auth
- `POST /auth/api-keys` — API key management
- `GET /health` — Health check
- `GET /status` — System status
- WebSocket `/ws` — Real-time events

## Testing Strategy

- **Framework:** pytest
- **Count:** 661 tests across 91 test files
- **Pattern:** Real implementations, no test doubles
- **Location:** `tests/` directory

## Git

- **Main branch:** `main`
- **Push target:** `origin/main`
- **Never commit:** `.env`, `venv*/`, `__pycache__/`, `*.pyc`, `data/`, `logs/`