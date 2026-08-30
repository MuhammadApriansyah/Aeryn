# Aeryn — Detailed Development Guide

## Environment Setup

### Virtual Environment

Always use `venv-proot` (Python 3.11):

```bash
cd /home/sen/aeryn-core-agent
source venv-proot/bin/activate
```

Verify:
```bash
python --version  # Python 3.11.x
which python      # /home/sen/aeryn-core-agent/venv-proot/bin/python
```

### Environment Variables

The `.env` file contains:
- `AERYN_PORT=3010`
- `AERYN_HOST=127.0.0.1`
- `AERYN_MODE=standalone`
- API keys and secrets (never commit)

### Python Dependencies

```bash
pip install -r requirements.txt
```

Core dependencies:
- `fastapi>=0.109.0` — Web framework
- `uvicorn>=0.27.0` — ASGI server
- `pydantic>=2.0.0` — Data validation
- `numpy>=1.22.0` — Numerical operations
- `pytest>=7.0.0` — Testing
- `python-dotenv>=1.0.0` — Environment variables
- `python-dateutil>=2.8.0` — Date parsing

### PM2 Setup

PM2 manages all Node.js and Python processes:

```bash
pm2 start ecosystem.config.cjs
pm2 status
pm2 logs
```

## Database: SQLite with WAL Mode

### Connection Pattern

All SQLite connections MUST go through the WAL patch:

```python
# This import MUST be first — patches sqlite3.connect
import aeryn_core.utils.patch_sqlite  # noqa

# Now all sqlite3.connect calls get WAL + busy_timeout
import sqlite3
conn = sqlite3.connect("data/aeryn.db")
```

### WAL Mode Benefits
- **Better concurrency** — Readers don't block writers
- **Better performance** — WAL is faster for most workloads
- **busy_timeout** — Waits for locks instead of failing immediately

### Database Location
- Main DB: `data/aeryn.db`
- Personalisasi DBs: `Personalisasi/Database/`
- Test DBs: Created in-memory or temp files

### Schema Management
- No migrations framework — schema is managed in code
- Tables created on first use via `CREATE TABLE IF NOT EXISTS`
- See `aeryn_core/database/` for schema definitions

## Memory System

The memory system is one of Aeryn's core components, located in `aeryn_core/memory/`.

### Vault (`vault.py`)
Long-term persistent storage with layers:

```python
from aeryn_core.memory.vault import AerynVault, VaultEntry, LAYER_WIKI

vault = AerynVault()

# Store entry
entry = VaultEntry(
    key="project/idea",
    value={"title": "My Idea", "status": "draft"},
    layer=LAYER_WIKI,
    tags=["project", "idea"]
)
vault.store(entry)

# Retrieve
result = vault.retrieve("project/idea")
```

### Hybrid Search (`hybrid_search.py`)
Combines semantic and keyword search:

```python
from aeryn_core.memory.hybrid_search import get_search_engine

engine = get_search_engine()
engine.index("doc1", "Aeryn is a personal AI assistant")
results = engine.search("AI assistant", limit=10)
```

### Social Memory (`social_memory.py`)
Tracks social interactions and relationships:

```python
from aeryn_core.memory.social_memory import SocialMemory

social = SocialMemory()
social.record_interaction("user123", "asked about pricing", sentiment="positive")
profile = social.get_profile("user123")
```

### Temporal Memory (`temporal_memory.py`)
Time-based memory with decay:

```python
from aeryn_core.memory.temporal_memory import get_temporal_memory

temporal = get_temporal_memory()
temporal.store("event", {"type": "login", "user": "user123"})
events = temporal.query(since="2024-01-01", event_type="login")
```

### Graph Memory (`graph_memory.py`)
Graph-based knowledge representation:

```python
from aeryn_core.memory.graph_memory import GraphMemory

graph = GraphMemory()
graph.add_node("user123", {"type": "user", "name": "Alice"})
graph.add_edge("user123", "project456", "owns")
```

### Memory Decay (`memory_decay.py`)
Automatically decays old memories:

```python
from aeryn_core.memory.memory_decay import get_memory_decay_engine

decay = get_memory_decay_engine()
decay.check_and_decay()  # Run periodically
```

### Entity Resolution (`entity_resolution.py`)
Resolves entities across mentions:

```python
from aeryn_core.memory.entity_resolution import get_entity_resolver

resolver = get_entity_resolver()
canonical = resolver.resolve("Alice", "A. Smith", "user123")
```

## Auth System

Located in `aeryn_core/auth/`.

### API Keys (`api_keys.py`)
```python
from aeryn_core.auth.api_keys import get_api_key_manager

manager = get_api_key_manager()
key = manager.create_key(user_id="user123", name="My App")
is_valid = manager.validate_key(key)
```

### Bearer Token Auth (`auth.py`)
```python
from aeryn_core.auth.auth import get_auth, ROLE_PERMISSIONS

auth = get_auth()
token = auth.login(username="alice", password="secret")
payload = auth.verify_token(token)
```

### Rate Limiter (`rate_limiter.py`)
```python
from aeryn_core.auth.rate_limiter import get_rate_limiter

limiter = get_rate_limiter()
allowed, retry_after = limiter.check_rate_limit(user_id="user123", tier="free")
```

### SSO Manager (`sso_manager.py`)
```python
from aeryn_core.auth.sso_manager import get_sso_manager

sso = get_sso_manager()
auth_url = sso.get_auth_url(provider="google")
user_info = sso.handle_callback(provider="google", code="...")
```

### Email Verification (`email_verification.py`)
```python
from aeryn_core.auth.email_verification import get_email_verification

ev = get_email_verification()
ev.send_verification(user_id="user123", email="alice@example.com")
ev.verify_code(user_id="user123", code="123456")
```

### Billing (`billing/billing.py`)
```python
from aeryn_core.billing.billing import get_billing, PRICING, PLANS

billing = get_billing()
subscription = billing.get_subscription(user_id="user123")
usage = billing.get_usage(user_id="user123", period="monthly")
```

## Safety System

Located in `aeryn_core/safety/`.

### Safety Engine (`safety_engine.py`)
Core safety orchestrator (24K):

```python
from aeryn_core.safety.safety_engine import get_safety_engine, sanitize_output

engine = get_safety_engine()
result = engine.check_safety(user_input, context={})
safe_output = sanitize_output(raw_output)
```

### Enhanced Guardrails (`enhanced_guardrails.py`)
```python
from aeryn_core.safety.enhanced_guardrails import get_enhanced_guardrails

guardrails = get_enhanced_guardrails()
result = guardrails.check(input_text, context)
```

### Enhanced Sandbox (`enhanced_sandbox.py`)
```python
from aeryn_core.safety.enhanced_sandbox import get_enhanced_sandbox, SandboxLimits

sandbox = get_enhanced_sandbox()
result = sandbox.execute(code, limits=SandboxLimits(max_memory_mb=128, timeout_s=30))
```

### OWASP Security (`owasp_security.py`)
```python
from aeryn_core.safety.owasp_security import get_owasp_security

owasp = get_owasp_security()
issues = owasp.scan_input(user_input)
```

### Guardian (`guardian.py`)
```python
from aeryn_core.safety.guardian import Guardian

guardian = Guardian()
guardian.monitor(action, context)
```

### Security Kernel (`security_kernel.py`)
```python
from aeryn_core.safety.security_kernel import SecurityKernel

kernel = SecurityKernel()
kernel.enforce_policy(action, subject, resource)
```

## Plugin System

Located in `aeryn_core/platform/plugin_system.py`.

### Plugin Manager
```python
from aeryn_core.platform.plugin_system import get_plugin_manager

manager = get_plugin_manager()
plugins = manager.list_plugins()
manager.load_plugin("my_plugin")
manager.unload_plugin("my_plugin")
```

### Plugin Marketplace
```python
from aeryn_core.platform.plugin_marketplace import get_plugin_marketplace

marketplace = get_plugin_marketplace()
available = marketplace.search("analytics")
marketplace.install("analytics-plugin")
```

### Creating a Plugin

1. Create directory in `plugins/my_plugin/`
2. Add `plugin.json` manifest
3. Add `main.py` with entry point
4. Register hooks and filters

```
plugins/my_plugin/
├── plugin.json
├── main.py
└── README.md
```

## Platform Integrations

### Multi-Agent (`platform/multi_agent.py`)
```python
from aeryn_core.platform.multi_agent import get_multi_agent_orchestrator, AgentRole

orch = get_multi_agent_orchestrator()
task = orch.create_task("Analyze data", role=AgentRole.ANALYST)
orch.assign_task(task.id, agent_id="agent_1")
```

### MCP Server (`platform/mcp_server.py`)
```python
from aeryn_core.platform.mcp_server import get_mcp_server

mcp = get_mcp_server()
mcp.register_tool("search", search_handler)
mcp.start()
```

### Browser Automation (`platform/browser_automation.py`)
```python
from aeryn_core.platform.browser_automation import get_browser_automation

browser = get_browser_automation()
browser.navigate("https://example.com")
result = browser.extract("h1")
```

### Discord Bot (`platform/discord_bot.py`)
```python
from aeryn_core.platform.discord_bot import get_telegram_bot

bot = get_discord_bot()
bot.send_message(channel_id="123", content="Hello!")
```

### WebSocket Server (`platform/websocket_server.py`)
```python
from aeryn_core.platform.websocket_server import get_websocket_server

ws = get_websocket_server()
ws.broadcast({"type": "notification", "data": "..."})
```

### Notification System (`platform/notification_system.py`)
```python
from aeryn_core.platform.notification_system import get_notification_manager, get_scheduler

notifications = get_notification_manager()
scheduler = get_scheduler()

notifications.send(user_id="user123", message="Task complete")
scheduler.schedule(task, when="2024-01-01T10:00:00")
```

## Utility Modules

### Configuration (`utils/config.py`)
```python
from aeryn_core.utils.config import ensure_dirs, get_config

ensure_dirs()  # Create required directories
config = get_config()
```

### Error Recovery (`utils/error_recovery.py`)
```python
from aeryn_core.utils.error_recovery import get_error_recovery, with_retry, with_fallback

recovery = get_error_recovery()

@with_retry(max_attempts=3, delay=2)
def flaky_operation():
    # Will retry on failure
    pass

@with_fallback(fallback_value="default")
def risky_operation():
    # Returns fallback on failure
    pass
```

### Logging (`utils/logger.py`)
```python
from aeryn_core.utils.logger import info, warn, error, log_exception

info("Operation complete", user_id="user123")
warn("Rate limit approaching", usage=95)
error("Operation failed", error=str(e))
```

### Performance (`utils/performance.py`)
```python
from aeryn_core.utils.performance import get_optimizer, get_uptime

optimizer = get_optimizer()
optimizer.profile("slow_function")
uptime = get_uptime()
```

### Data Encryption (`utils/data_encryption.py`)
```python
from aeryn_core.utils.data_encryption import get_encryption

enc = get_encryption()
encrypted = enc.encrypt("sensitive data")
decrypted = enc.decrypt(encrypted)
```

### Persona Engine (`utils/persona_engine.py`)
```python
from aeryn_core.utils.persona_engine import load_persona

persona = load_persona()
# Returns persona configuration for AI behavior
```

## Testing Patterns

### Test Structure
```python
# tests/test_my_feature.py
import pytest
from aeryn_core.<category>.my_feature import get_my_feature

class TestMyFeature:
    def setup_method(self):
        self.feature = get_my_feature()
    
    def test_basic_operation(self):
        result = self.feature.do_something("test")
        assert result is not None
    
    def test_error_handling(self):
        with pytest.raises(ValueError):
            self.feature.do_something("")
    
    def test_singleton_pattern(self):
        a = get_my_feature()
        b = get_my_feature()
        assert a is b
```

### Running Tests
```bash
cd /home/sen/aeryn-core-agent
source venv-proot/bin/activate
python -m pytest tests/ -x -q
```

### Test Coverage Areas
- **Auth:** API keys, rate limiting, SSO, email verification
- **Billing:** Plans, usage metering, subscription management
- **Memory:** Vault, hybrid search, temporal, social, graph
- **Safety:** Engine, guardrails, sandbox, OWASP
- **Platform:** Multi-agent, plugins, MCP, browser automation
- **API:** All endpoints, WebSocket, error handling