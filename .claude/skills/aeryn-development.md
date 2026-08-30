# Aeryn Detailed Development Guide

## Environment Setup

### Prerequisites

- **OS**: Linux (ARM64 or x86_64) — tested on Ubuntu 25.10 ARM64
- **Python**: 3.11+ (PEP 668 compliant — use venv)
- **RAM**: 11GB minimum (7.5GB used baseline)
- **No Docker**: All services run natively via PM2
- **Database**: SQLite only — PostgreSQL connection errors are expected and handled

### Virtual Environment

```bash
python3 -m venv venv-proot
source venv-proot/bin/activate
pip install -r requirements.txt
```

### PM2 Process Management

```bash
# Start API
pm2 start apps/api/aeryn_api.py --name aeryn-api --interpreter ./venv-proot/bin/python

# Restart
pm2 restart aeryn-api

# Logs
pm2 logs aeryn-api

# Kill port if needed
fuser -k 3010/tcp
```

## Database Architecture

### SQLite Configuration

All SQLite operations use patched connections for WAL mode + busy_timeout.

```python
# Import patch first — it patches sqlite3.connect globally
import aeryn_core.utils.patch_sqlite  # noqa

# Then any sqlite3.connect() will use WAL + busy_timeout
conn = sqlite3.connect("data/some_database.db")
```

### Shared Database

```python
from aeryn_core.database.shared_db import get_shared_db

db = get_shared_db()
# Returns SQLite connection with:
# - WAL mode enabled
# - busy_timeout = 5000ms
# - check_same_thread = False
# - foreign_keys = ON
```

### Database Locations

| Database | Location | Purpose |
|----------|----------|---------|
| Adaptive | `Personalisasi/Database/adaptive_system.db` | Error logs, adaptations, health metrics |
| Feedback | `Personalisasi/Database/feedback.db` | User feedback for self-improvement |
| Memory | `Personalisasi/Database/memory.db` | Long-term memory storage |
| Chat | `Personalisasi/Database/chat_history.db` | Chat session history |

## Memory System

### Core Modules

#### 1. Vault (`aeryn_core/memory/vault.py`)
- Obsidian-style knowledge base
- Bidirectional linking
- Tags and categories
- Search by content, tags, links

#### 2. Social Memory (`aeryn_core/memory/social_memory.py`)
- User relationship tracking
- Persona preferences
- Conversation history
- Relationship strength scoring

#### 3. Hybrid Search (`aeryn_core/memory/hybrid_search.py`)
- BM25 (Okapi) for keyword search
- Vector search for semantic similarity
- Combined ranking
- Query expansion

#### 4. Temporal Memory (`aeryn_core/memory/temporal_memory.py`)
- Time-based memory decay
- Timeline queries
- Trend detection
- Memory consolidation

#### 5. Enhanced Memory (`aeryn_core/memory/enhanced_memory.py`)
- Entity extraction (people, places, concepts)
- Preference learning
- Cross-session recall
- Memory importance scoring

### Using Memory

```python
from aeryn_core.memory.vault import AerynVault

vault = AerynVault()
vault.store_entry(
    layer="wiki",
    title="My Note",
    content="Content here",
    tags=["tag1", "tag2"]
)
results = vault.search("query text")
```

## Auth System

### API Keys (`aeryn_core/auth/api_keys.py`)

```python
from aeryn_core.auth.api_keys import get_api_key_manager

manager = get_api_key_manager()
key = manager.create_key(user_id="user1", name="my-key")
valid = manager.validate_key(key)
```

### Rate Limiting (`aeryn_core/auth/rate_limiter.py`)

```python
from aeryn_core.auth.rate_limiter import RateLimiter

limiter = RateLimiter(max_requests=100, window_seconds=60)
if limiter.check("user1"):
    # Process request
    pass
else:
    # Rate limited
    pass
```

### SSO Manager (`aeryn_core/auth/sso_manager.py`)

```python
from aeryn_core.auth.sso_manager import get_sso_manager

sso = get_sso_manager()
# Supports OAuth2, OIDC flows
```

## Billing System (`aeryn_core/billing/`)

### Billing (`aeryn_core/billing/billing.py`)

```python
from aeryn_core.billing.billing import get_billing, PRICING, PLANS

billing = get_billing()
plans = PLANS  # Available subscription plans
pricing = PRICING  # Token pricing tiers
```

### Usage Metering (`aeryn_core/billing/usage_metering.py`)

```python
from aeryn_core.billing.usage_metering import get_usage_metering

meter = get_usage_metering()
meter.record_usage(user_id, tokens_used)
stats = meter.get_usage_stats(user_id)
```

## Safety Layer

### Safety Engine (`aeryn_core/safety/safety_engine.py`)

```python
from aeryn_core.safety.safety_engine import get_safety_engine, sanitize_output

engine = get_safety_engine()
result = engine.validate_input(user_prompt)
sanitized = sanitize_output(llm_output)
```

### Enhanced Guardrails (`aeryn_core/safety/enhanced_guardrails.py`)

```python
from aeryn_core.safety.enhanced_guardrails import get_enhanced_guardrails

guardrails = get_enhanced_guardrails()
result = guardrails.validate_request({
    "text": user_input,
    "context": "general"
})
```

### Enhanced Sandbox (`aeryn_core/safety/enhanced_sandbox.py`)

```python
from aeryn_core.safety.enhanced_sandbox import get_enhanced_sandbox, SandboxLimits

sandbox = get_enhanced_sandbox()
result = sandbox.execute(code, limits=SandboxLimits(
    max_memory_mb=256,
    max_time_seconds=10
))
```

### OWASP Security (`aeryn_core/safety/owasp_security.py`)

```python
from aeryn_core.safety.owasp_security import get_owasp_security

security = get_owasp_security()
report = security.scan(user_input)
```

## Platform & Plugins

### Plugin System (`aeryn_core/platform/plugin_system/`)

```python
from aeryn_core.platform.plugin_system import get_plugin_manager

manager = get_plugin_manager()
plugins = manager.list_plugins()
enabled = manager.get_enabled_plugins()
result = manager.execute_plugin("plugin_name", args)
```

### Plugin Marketplace (`aeryn_core/plugin_marketplace/`)

```python
from aeryn_core.plugin_marketplace import get_plugin_marketplace

market = get_plugin_marketplace()
plugins = market.search(query="search term")
plugin = market.get("plugin_id")
```

### Tool Runtime (`aeryn_core/platform/tool_runtime.py`)

```python
from aeryn_core.platform.tool_runtime import get_tool_runtime

runtime = get_tool_runtime()
result = runtime.execute_tool("tool_name", {"arg": "value"})
```

### Background Queue (`aeryn_core/platform/background_queue.py`)

```python
from aeryn_core.platform.background_queue import get_task_queue

queue = get_task_queue()
task_id = queue.enqueue(async_func, args, kwargs)
result = queue.get_result(task_id)
```

## Adaptive System

### Adaptive Orchestrator (`aeryn_core/adaptive/`)

```python
from aeryn_core.adaptive import get_adaptive_system

system = get_adaptive_system()
system.run_adaptive_cycle()
health = system.get_health_report()
errors = system.get_error_summary()
```

### Self-Improvement (`aeryn_core/reasoning/self_improvement.py`)

```python
from aeryn_core.reasoning.self_improvement import get_self_improvement_engine

engine = get_self_improvement_engine()
engine.record_interaction(...)
engine.record_feedback(...)
engine.optimize_prompt(...)
```

## Multi-Agent System

### Orchestrator (`aeryn_core/platform/multi_agent.py`)

```python
from aeryn_core.platform.multi_agent import get_multi_agent_orchestrator, AgentRole

orchestrator = get_multi_agent_orchestrator()
agent_id = orchestrator.register_agent("name", AgentRole.WORKER)
task_id = orchestrator.create_task("title", "description", agent_id)
```

## Frontend Development

### File Structure

```
apps/web/
├── templates/
│   └── dashboard.html    # Main template (264 lines)
├── static/
│   ├── css/
│   │   └── dashboard.css  # Styles (462 lines)
│   └── js/
│       └── dashboard.js   # Logic (964 lines)
└── server.py             # Routing + API proxy
```

### Key Patterns

1. **State at top**: All variables declared in IIFE scope
2. **Render functions**: Each page has `render{PageName}()` function
3. **Safe execution**: Wrap in `safeExecute()` for error boundary
4. **Real data**: Use `localStorage` for CRUD operations (no mock data)
5. **Accessibility**: Always use ARIA labels, keyboard shortcuts, screen reader announcements

### Adding a New Page

1. Add to `navItems` array
2. Add route in `server.py` (both `@app.get` and SPA route)
3. Add case in `renderPage()` switch
4. Add render function
5. Add state management

## Testing Guidelines

- Run `python -m pytest tests/ -x -q` after every change
- **NO test doubles** — real implementations only
- Each test should verify real behavior, not mock responses
- Add tests for new features before completing
