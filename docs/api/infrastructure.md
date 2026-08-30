# Infrastructure Documentation

> **Purpose**: Document Aeryn's infrastructure setup, deployment, and maintenance.
> **Rule**: Real setup used in production — no test doubles.

---

## 🏗️ Infrastructure Overview

```
┌─────────────────────────────────────────────┐
│           Host: Ubuntu 25.10 ARM64           │
│           CPU: ARM64 (no Docker)            │
│           RAM: 11GB (7.5GB used)            │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│        PM2 Process Manager                   │
│        (port 3010)                          │
└──────────────┬──────────────────────────────┘
               │
        ┌──────┴──────┐
        ▼              ▼
┌─────────────┐ ┌──────────────────┐
│ FastAPI API │ │   SPA Dashboard   │
│ (Uvicorn)   │ │   (Static Files)  │
│  Port: 3010  │ │   /web/           │
└──────┬──────┘ └──────────────────┘
       │
       ▼
┌─────────────┐
│   SQLite    │ (WAL mode, in-process)
│  Databases  │
│  No PG      │
└─────────────┘
```

---

## 🗄️ Storage Layout

### Database Locations

| Database | Path | Purpose |
|----------|------|---------|
| Adaptive | `Personalisasi/Database/adaptive_system.db` | Error logs, adaptations, health |
| Feedback | `Personalisasi/Database/feedback.db` | User feedback |
| Memory | `Personalisasi/Database/memory.db` | Long-term memory |
| Chat | `Personalisasi/Database/chat_history.db` | Chat history |
| Auth | `Personalisasi/Database/auth.db` | API keys, sessions |
| Billing | `Personalisasi/Database/billing.db` | Subscriptions, usage |
| Plugins | `Personalisasi/Database/plugins.db` | Installed plugins |

### File Storage

| Directory | Purpose |
|-----------|---------|
| `plugins/installed/` | Installed plugin code |
| `plugins/marketplace/` | Cached marketplace metadata |
| `Personalisasi/` | User personalization data |
| `data/` | Runtime data |
| `logs/` | Application logs |

---

## 🚀 Deployment

### Starting Aeryn

```bash
# 1. Activate venv
source venv-proot/bin/activate

# 2. Start API via PM2
pm2 start apps/api/aeryn_api.py \
  --name aeryn-api \
  --interpreter ./venv-proot/bin/python

# 3. Verify health
curl http://127.0.0.1:3010/health
```

### PM2 Ecosystem

```bash
# Check status
pm2 list

# Restart
pm2 restart aeryn-api

# Stop
pm2 stop aeryn-api

# Logs
pm2 logs aeryn-api
```

### Port Management

```bash
# Check port usage
lsof -i :3010

# Kill process on port
fuser -k 3010/tcp

# Verify
curl http://127.0.0.1:3010/health
```

---

## 🔧 SQLite Configuration

### WAL Mode Patch

All SQLite connections use patched settings via `aeryn_core/utils/patch_sqlite.py`:

```python
import aeryn_core.utils.patch_sqlite  # noqa - must be first import

# Now all sqlite3.connect() calls use:
# - journal_mode = wal
# - busy_timeout = 5000ms
# - synchronous = normal
# - temp_store = memory
```

### Shared Database

```python
from aeryn_core.database.shared_db import get_shared_db

db = get_shared_db()
conn = db.get_connection("database_name")
# Returns: sqlite3.Connection with all patches applied
```

---

## 🌐 Network Configuration

### Reverse Proxy (Optional)

For production behind nginx:

```nginx
server {
    listen 80;
    server_name aeryn.local;
    
    location / {
        proxy_pass http://127.0.0.1:3010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /socket.io/ {
        proxy_pass http://127.0.0.1:3010;
        proxy_http_upgrade on;
        proxy_set_header Upgrade $http_upgrade;
    }
}
```

### CORS

CORS is disabled by default — all requests must come from the same origin (localhost:3010).

---

## 🔍 Monitoring

### Health Check

```bash
# Basic health
curl http://127.0.0.1:3010/health

# Adaptive system health
curl http://127.0.0.1:3010/api/adaptive/health

# Dashboard stats
curl http://127.0.0.1:3010/dashboard/stats
```

### Log Monitoring

```bash
# Watch all logs
pm2 logs aeryn-api --lines 100

# Filter by type
pm2 logs aeryn-api | grep -i "error"
pm2 logs aeryn-api | grep -i "warning"
pm2 logs aeryn-api | grep "adaptive"
```

### Self-Reflection Logs

The self-improvement system logs to:
- `aeryn_core/utils/reflection.py` — daily reflection
- `Personalisasi/Database/feedback.db` — user feedback
- Adaptive system DB — all adaptations

---

## 🛡️ Security

### Rate Limiting

```python
from aeryn_core.auth.rate_limiter import RateLimiter

limiter = RateLimiter(max_requests=100, window_seconds=60)
if limiter.check("user_id"):
    # Allow
    pass
else:
    # Reject
    pass
```

### API Key Management

```python
from aeryn_core.auth.api_keys import get_api_key_manager

manager = get_api_key_manager()
key = manager.create_key("user123", "my-key")
# Store key["key"] securely — only shown once
```

### Secrets Management

```python
from aeryn_core.safety.secrets_runtime import get_secrets_manager

secrets = get_secrets_manager()
api_key = secrets.get("OPENAI_API_KEY", "[REDACTED]")
```

---

## 🔧 Maintenance

### Daily Tasks

```bash
# Check health
curl http://127.0.0.1:3010/health

# Check adaptive errors
curl http://127.0.0.1:3010/api/adaptive/errors
```

### Weekly Tasks

```bash
# Run full test suite
python -m pytest tests/ -x -q

# Check database size
du -sh Personalisasi/Database/

# Cleanup old logs
find logs/ -name "*.log" -mtime +30 -delete
```

### Monthly Tasks

```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Check for security issues
python -m pip-audit

# Review plugin security
python -m pytest tests/test_security.py -x -q
```

---

## 📊 Resource Usage

### Baseline Metrics

| Resource | Current | Limit |
|----------|---------|-------|
| CPU | ~5% | 100% |
| RAM | 7.5GB / 11GB | 100% |
| Disk | 81% used | 100% |
| SQLite DBs | < 500MB total | — |

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API response | < 500ms | ~200ms |
| Dashboard load | < 2s | ~1s |
| Test suite | < 60s | ~35s |
| Full suite | 661 tests | ✅ |

---

*Infrastructure v59.0 — Updated 2026-08-30.*
