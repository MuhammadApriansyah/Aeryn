# AGENTS.md — Project Structure & Conventions

## Directory Layout

```
aeryn-core-agent/
├── aeryn_core/          # Core system (5,600+ files)
│   ├── agents/          # 5 cognitive divisions
│   │   ├── division_1_creative/   # POV + Style agents
│   │   ├── division_2_psych/      # Psychology agents
│   │   ├── division_3_reasoning/  # MCTS + FOL + Critique + Graph
│   │   ├── division_4_gov/        # Governance agents
│   │   └── division_5_infra/      # Sync + Validator agents
│   ├── adaptive/                  # ✨ Fully adaptive + self-improvement
│   ├── auth/                    # Auth + billing + rate limiting
│   ├── billing/                # Billing + usage metering
│   ├── cost/                    # Token monitor + model router
│   ├── database/                # SQLite (WAL) + vector DB
│   ├── memory/                  # Core + Social + Temporal + Vault
│   │   ├── vault.py            # Obsidian-style knowledge base
│   │   ├── social_memory.py    # User relationship tracking
│   │   ├── hybrid_search.py    # BM25 + vector search
│   │   └── temporal_memory.py  # Time-based memory
│   ├── platform/                # MCP + Webhooks + Cloud Sync
│   │   ├── plugin_system/      # Plugin loader + registry
│   │   ├── multi_agent.py      # Multi-agent orchestrator
│   │   ├── tool_runtime.py     # Tool execution runtime
│   │   ├── background_queue.py # Job queue
│   │   └── notification_system.py # Notifications + scheduler
│   ├── reasoning/               # Self-improvement + Meta-evolution
│   │   └── self_improvement.py # Feedback collection
│   ├── safety/                  # 4-level sandbox + security
│   │   ├── safety_engine.py    # Prompt injection detection
│   │   ├── enhanced_guardrails.py # Enhanced guardrails
│   │   ├── enhanced_sandbox.py # Security sandbox
│   │   ├── owasp_security.py   # OWASP compliance
│   └── utils/                   # Config + Logger + Adapters
│       ├── config.py           # Configuration
│       ├── logger.py           # Structured logging
│       ├── patch_sqlite.py     # SQLite WAL + busy_timeout patch
│       ├── adapters.py         # Composable capability modules
│       ├── guardrails.py       # Cognitive guardrail engine
│       ├── error_recovery.py   # Error recovery strategies
│       └── model_client.py     # LLM client

├── apps/
│   ├── api/                    # FastAPI backend (port 3010)
│   │   └── aeryn_api.py       # Main API file (4154+ lines)
│   └── web/                    # SPA Dashboard (HTML/CSS/JS)
│       ├── templates/          # HTML templates
│       │   └── dashboard.html # Main dashboard template
│       ├── static/
│       │   ├── css/
│       │   │   └── dashboard.css  # 462 lines CSS
│       │   └── js/
│       │       └── dashboard.js   # 964 lines vanilla JS
│       └── server.py           # Dashboard routing + API proxy

├── tests/                      # 661 automated tests
├── plugins/                    # Plugin marketplace
├── scripts/                    # Monitoring + reflection
├── Personalisasi/              # User personalization data
└── docs/                       # Documentation

├── venv-proot/                # Python virtualenv
└── requirements.txt           # Python dependencies
```

## Naming Conventions

- **Python**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants
- **JavaScript**: `camelCase` for functions/variables, `PascalCase` for classes
- **CSS**: `kebab-case` for custom properties (`--color-primary`)
- **Files**: `snake_case.py`, `kebab-case.css`, `camelCase.js`

## Import Style

- **Python**: Absolute imports preferred (e.g., `from aeryn_core.memory.vault import AerynVault`)
- **JavaScript**: No imports (vanilla JS, everything in IIFE)

## Testing

- **Runner**: `python -m pytest tests/ -x -q`
- **Count**: 661 tests (auth, billing, features, API endpoints)
- **Location**: `tests/` directory
- **Pattern**: Real testing only — no mocks/stubs in production code
- **Coverage**: Run full suite after every change

## Git Workflow

```bash
git add -A
git commit -m "type: concise description"
git push origin main
```

**Always update README + CHANGELOG + RELEASE before pushing.**

## Process Management

- **PM2**: `pm2 start apps/api/aeryn_api.py --name aeryn-api --interpreter ./venv-proot/bin/python`
- **Logs**: `pm2 logs aeryn-api`
- **Restart**: `pm2 restart aeryn-api`
- **Port**: 3010 (kill with `fuser -k 3010/tcp` if needed)

## Code Structure Patterns

### Adding a New API Endpoint

1. Open `apps/api/aeryn_api.py`
2. Find the appropriate section (search for existing patterns)
3. Add route with `@app.get("/endpoint")` or `@app.post("/endpoint")`
4. Follow existing async pattern
5. Return dict (FastAPI handles JSON automatically)

### Adding a New SPA Feature

1. Edit `apps/web/static/js/dashboard.js`
2. Add state variable at top
3. Add render function
4. Add case to `renderPage()` switch
5. Add navigation item to `navItems` array
6. Test in browser

### Adding a New Memory Module

1. Create file in `aeryn_core/memory/`
2. Import in `aeryn_core/__init__.py` if needed
3. Use SQLite with patched connection (`aeryn_core/database/shared_db.py`)
4. Add tests in `tests/`

### Adding a New Agent Division

1. Add directory in `aeryn_core/agents/division_*/`
2. Follow pattern of `sub_agents_real.py` (real implementations, no mocks)
3. Register in `aeryn_core/platform/multi_agent.py`
