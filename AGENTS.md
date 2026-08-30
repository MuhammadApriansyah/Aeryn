# Aeryn — Project Structure & Conventions

## Directory Layout

```
aeryn-core-agent/
├── apps/
│   ├── api/
│   │   ├── aeryn_api.py          # Main FastAPI backend (4,182 lines)
│   │   ├── dashboard.html         # Legacy dashboard
│   │   ├── health_check.py        # Health endpoint
│   │   ├── llm_runner.py          # LLM execution engine
│   │   ├── monitor.py             # System monitor
│   │   └── scheduler.py           # Task scheduler
│   ├── hermes_bridge/             # Hermes integration bridge
│   └── web/
│       ├── server.py              # Static file server
│       ├── static/
│       │   ├── css/               # Stylesheets
│       │   └── js/
│       │       └── dashboard.js   # SPA frontend (964 lines)
│       └── templates/             # Jinja2 templates
├── aeryn_core/                    # Core library (76 subdirectories)
│   ├── __init__.py
│   ├── adaptive/                  # Self-improvement system
│   │   └── __init__.py            # 34K — error recovery, learning, health
│   ├── agents/                    # 5 cognitive divisions
│   │   ├── division_1_creative/   # Creative agents (POV, Style)
│   │   ├── division_2_psych/      # Psychological intelligence
│   │   ├── division_3_reasoning/  # Reasoning (MCTS, FOL, Critique, Graph)
│   │   ├── division_4_gov/        # Governance
│   │   └── division_5_infra/      # Infrastructure (Sync, Validator)
│   ├── auth/                      # Authentication
│   │   ├── api_keys.py            # API key management
│   │   ├── auth.py                # Bearer token auth
│   │   ├── email_verification.py  # Email verification
│   │   ├── rate_limiter.py        # Rate limiting
│   │   └── sso_manager.py         # SSO integration
│   ├── billing/                   # Billing system
│   │   ├── billing.py             # Plans, PRICING
│   │   └── usage_metering.py      # Usage tracking
│   ├── memory/                    # Memory system
│   │   ├── vault.py               # Long-term vault storage
│   │   ├── hybrid_search.py       # Hybrid search engine
│   │   ├── social_memory.py       # Social memory
│   │   ├── temporal_memory.py     # Temporal memory
│   │   ├── graph_memory.py        # Graph-based memory
│   │   ├── session_history.py     # Session history
│   │   ├── enhanced_memory.py     # Enhanced memory features
│   │   ├── memory_decay.py        # Memory decay engine
│   │   ├── memory_consolidation.py # Memory consolidation
│   │   ├── semantic_recall.py     # Semantic recall
│   │   └── entity_resolution.py   # Entity resolution
│   ├── reasoning/                 # Reasoning engines
│   │   ├── reasoning_style.py     # Research reasoning
│   │   ├── dream_synthesis.py     # Dream synthesis
│   │   ├── constitutional_ai.py   # Constitutional AI
│   │   ├── planner.py             # Task planner
│   │   ├── proactive_engine.py    # Proactive suggestions
│   │   ├── long_horizon.py        # Long-horizon planning
│   │   ├── emotional_intelligence.py # Emotional intelligence
│   │   ├── self_improvement.py    # Self-improvement engine
│   │   ├── context_manager.py     # Context management
│   │   └── reflection.py          # Reflection engine
│   ├── safety/                    # Safety systems
│   │   ├── safety_engine.py       # Core safety engine (24K)
│   │   ├── enhanced_guardrails.py # Enhanced guardrails
│   │   ├── enhanced_sandbox.py    # Enhanced sandbox
│   │   ├── guardrails.py          # Base guardrails
│   │   ├── guardian.py            # Guardian system
│   │   ├── owasp_security.py      # OWASP security
│   │   ├── security_kernel.py     # Security kernel
│   │   ├── sandbox.py             # Sandbox execution
│   │   ├── secrets_runtime.py     # Secrets management
│   │   └── soc2_compliance.py     # SOC2 compliance
│   ├── platform/                  # Platform integrations
│   │   ├── plugin_system.py       # Plugin system
│   │   ├── plugin_marketplace.py  # Plugin marketplace
│   │   ├── multi_agent.py         # Multi-agent orchestration
│   │   ├── mcp_server.py          # MCP server
│   │   ├── browser_automation.py  # Browser automation
│   │   ├── discord_bot.py         # Discord bot
│   │   ├── telegram_bot.py        # Telegram bot
│   │   ├── email_agent.py         # Email agent
│   │   ├── calendar_integration.py # Calendar integration
│   │   ├── github_integration.py  # GitHub integration
│   │   ├── websocket_server.py    # WebSocket server
│   │   ├── notification_system.py # Notification system
│   │   ├── tool_runtime.py        # Tool runtime
│   │   ├── tool_bridge.py         # Tool bridge
│   │   └── skill_crystallization.py # Skill crystallization
│   └── utils/                     # Utilities
│       ├── config.py              # Configuration
│       ├── patch_sqlite.py        # SQLite WAL patch
│       ├── error_handling.py      # Error handling
│       ├── error_recovery.py      # Error recovery
│       ├── logger.py              # Logging
│       ├── performance.py         # Performance monitoring
│       ├── event_bus.py           # Event bus
│       ├── llm_client.py          # LLM client
│       ├── model_client.py        # Model client
│       ├── data_encryption.py     # Data encryption
│       ├── persona_engine.py      # Persona engine
│       ├── guardrails.py          # Guardrails utils
│       └── adapters.py            # Adapters
├── tests/                         # Test suite (91 files, 661 tests)
├── data/                          # Runtime data (SQLite databases)
├── logs/                          # PM2 logs
├── docs/                          # Documentation
├── scripts/                       # Utility scripts
├── plugins/                       # Plugin storage
├── Personalisasi/                 # Personalization data
├── ecosystem.config.cjs           # PM2 config for API + dashboard
├── ecosystem-web.config.cjs       # PM2 config for Next.js web app
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables (git-ignored)
└── venv-proot/                    # Python 3.11 virtual environment
```

## Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Python modules | `snake_case.py` | `aeryn_api.py`, `safety_engine.py` |
| Python functions | `snake_case()` | `get_safety_engine()`, `sanitize_output()` |
| Python classes | `PascalCase` | `AerynVault`, `SandboxLimits` |
| JavaScript files | `camelCase.js` | `dashboard.js` |
| JavaScript functions | `camelCase()` | `showErrorBoundary()`, `loadPersona()` |
| JavaScript variables | `camelCase` | `currentPage`, `healthData` |
| Constants | `UPPER_SNAKE_CASE` | `LAYER_WIKI`, `PRICING`, `PLANS` |
| Test files | `test_<feature>.py` | `test_safety_engine.py`, `test_rate_limiter.py` |

## Import Style

**Python — absolute imports preferred:**
```python
# Good (absolute)
from aeryn_core.safety.safety_engine import get_safety_engine, sanitize_output
from aeryn_core.memory.vault import AerynVault, VaultEntry, LAYER_WIKI
from aeryn_core.utils.error_recovery import get_error_recovery, with_retry

# Bad (relative)
from ..safety.safety_engine import get_safety_engine
```

**JavaScript — ES5 patterns (no modules):**
```javascript
// All code in IIFE — no imports/exports
(function() {
  'use strict';
  // Code here
})();
```

## Testing Conventions

- **Framework:** pytest
- **Total tests:** 661
- **Test files:** 91
- **Run command:** `python -m pytest tests/ -x -q`
- **Location:** `tests/` directory (flat structure)
- **Naming:** `test_<feature>.py`
- **Pattern:** Test classes or functions, no complex hierarchies

## Git Conventions

- **Main branch:** `main`
- **Push target:** `origin/main`
- **Feature branches:** `feature/<name>` or `v<version>/<feature>`
- **Never commit:** `.env`, `venv*/`, `__pycache__/`, `*.pyc`, `data/*.db`, `logs/`

## PM2 Configuration

**Main API** (`ecosystem.config.cjs`):
```javascript
{
  name: "aeryn-api",
  script: "apps/api/aeryn_api.py",
  interpreter: "./venv-proot/bin/python",
  cwd: "/home/sen/aeryn-core-agent",
  env: {
    AERYN_PORT: "3010",
    AERYN_HOST: "127.0.0.1",
    AERYN_MODE: "standalone"
  }
}
```

**Dashboard** (`ecosystem.config.cjs`):
```javascript
{
  name: "aeryn-dashboard",
  script: "aeryn_core/dashboard/run_server.py",
  interpreter: "./venv-proot/bin/python",
  env: { AERYN_DASHBOARD_PORT: "3020" }
}
```

**Next.js Web** (`ecosystem-web.config.cjs`):
```javascript
{
  name: "aeryn-web",
  script: "/home/sen/aeryn-core-agent/aeryn-web/start.sh",
  env: { NODE_ENV: "development" }
}
```

## Python Style

- **Python version:** 3.11
- **Formatting:** PEP 8
- **Type hints:** Encouraged for public APIs
- **Docstrings:** Triple quotes, describe purpose and args
- **Line length:** ~100 chars (flexibility for readability)
- **Virtual environment:** Always use `venv-proot/`