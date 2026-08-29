# Aeryn Development Skill

> Procedural knowledge untuk develop dan maintain Aeryn platform.

---

## Trigger Conditions

Gunakan skill ini ketika:
- Membuat fitur baru di aeryn_core/
- Menambah endpoint API
- Fix bug di Aeryn
- Menambah test case
- Refactoring kode Aeryn

---

## Directory Structure

```
aeryn-core-agent/
├── aeryn_core/
│   ├── auth/           ← auth, sso, rate_limiter
│   ├── billing/        ← billing, usage_metering
│   ├── database/       ← neon_db, sqlite, vector_db
│   ├── hermes/         ← hermes_brain, hermes_hands, hermes_reflex
│   ├── memory/         ← vault, core_memory, semantic, temporal
│   ├── platform/       ← webhook, plugin, workspace, integrations
│   ├── reasoning/      ← context, reasoning_style, proactive
│   ├── safety/         ← security, guardrails, sandbox
│   └── utils/          ← logger, config, performance
├── apps/api/           ← FastAPI endpoints
├── sdk/                ← Python + TypeScript SDKs
├── scripts/            ← operational scripts
├── skills/             ← procedural knowledge
└── tests/              ← test suite
```

---

## Adding New Feature

### Step 1: Create Module

```python
# aeryn_core/{category}/{feature_name}.py
"""
V41.0 — {Feature Name}
{Description}
"""

from aeryn_core.utils.logger import info, warn, error

class FeatureClass:
    def __init__(self):
        pass
```

### Step 2: Add to Category `__init__.py`

```python
# aeryn_core/{category}/__init__.py
from .{feature_name} import *
```

### Step 3: Create Endpoint (if needed)

```python
# apps/api/aeryn_api.py
from aeryn_core.{category}.{feature_name} import get_{feature}_manager

class {Feature}Request(BaseModel):
    field: str

@app.post("/{feature}")
async def create_{feature}(req: {Feature}Request, authorization: str = Header(None)):
    auth = get_auth()
    # ... auth check ...
    manager = get_{feature}_manager()
    return manager.create(req.field)
```

### Step 4: Add Test

```python
# tests/test_{feature}.py
"""Test {feature}."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.{category}.{feature_name} import FeatureClass

def test_{feature}_create():
    f = FeatureClass()
    result = f.create("test")
    assert result["status"] == "ok"
```

### Step 5: Verify

```bash
./venv-proot/bin/python -m pytest tests/test_{feature}.py -v
./venv-proot/bin/python -m pytest tests/ -q  # All tests still pass
```

---

## Code Standards

1. **Semua kode berbahasa Indonesia** (docstring, komentar, log)
2. **Tidak ada shell=True** di subprocess calls
3. **Semua SQL pakai parameterized query**
4. **Semua table names di-sanitize** dengan regex `^[a-zA-Z][a-zA-Z0-9_]*$`
5. **Password pakai PBKDF2-SHA256**
6. **Semua endpoint pakai auth** (Bearer token atau API key)
7. **Log pakai structured logger** dari aeryn_core.utils.logger

---

## Common Patterns

### Database Access

```python
from aeryn_core.database.neon_db import get_neon

db = get_neon()
result = db.fetchone("SELECT * FROM users WHERE id = %s", (user_id,))
```

### Auth Check

```python
from aeryn_core.auth.auth import get_auth

auth = get_auth()
user = auth.validate_token(token)
if not user:
    return {"error": "Invalid token"}
if not auth.has_permission(user, "admin:read"):
    return {"error": "Permission denied"}
```

### Error Handling

```python
from aeryn_core.utils.logger import log_exception

try:
    # ... code ...
except Exception as e:
    log_exception(e, context="my_function")
    return {"error": str(e)}
```

---

## Pitfalls

1. **Jangan lupa `__init__.py`** di setiap subdirectory
2. **Jangan hardcode paths** — pakai config.py
3. **Jangan skip rate limiting** di endpoint baru
4. **Jangan tambah shell=True** — pakai shlex + list args
5. **Jangan lupa test** untuk setiap fitur baru
6. **Jangan commit .env** atau secrets

---

*Last updated: 2026-08-29*
*Aeryn V41.0*
