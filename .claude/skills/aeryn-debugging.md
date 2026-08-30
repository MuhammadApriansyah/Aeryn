# Aeryn — Debugging Guide

## Common Issues & Solutions

### Issue: PostgreSQL Connection Errors

**Symptom:** Logs show PostgreSQL connection attempts or errors.

**Cause:** This is EXPECTED. Aeryn uses SQLite only, but some libraries may attempt PostgreSQL connections.

**Solution:** Ignore PostgreSQL errors — they are non-fatal. The system falls back to SQLite:

```python
# This is by design — SQLite is the only database
import aeryn_core.utils.patch_sqlite  # Patches sqlite3.connect for WAL
```

**If PostgreSQL errors block startup:**
- Check `psycopg2` is not in `requirements.txt` (it isn't)
- Verify no `.env` file contains `DATABASE_URL` pointing to PostgreSQL
- Run `grep -r "postgres" apps/ aeryn_core/` to find accidental references

---

### Issue: Port Already in Use (Port 3010)

**Symptom:** `Address already in use` or `EADDRINUSE` when starting API.

**Solution:**
```bash
# Find and kill process on port 3010
fuser -k 3010/tcp

# Or more specifically
lsof -i :3010
kill -9 <PID>

# Then restart
pm2 restart aeryn-api
```

---

### Issue: PM2 Process Won't Start

**Symptom:** `pm2 start` fails or process shows `errored` status.

**Debug steps:**
```bash
# Check PM2 logs
pm2 logs aeryn-api --lines 50

# Check error log file
tail -50 logs/aeryn-api-error.log

# Check output log file
tail -50 logs/aeryn-api-out.log

# Test run without PM2
cd /home/sen/aeryn-core-agent
source venv-proot/bin/python
python apps/api/aeryn_api.py
```

**Common causes:**
- Missing virtual environment activation
- Import error (check `sys.path` includes project root)
- Port conflict (see above)
- Missing environment variables

---

### Issue: Module Not Found / Import Error

**Symptom:** `ModuleNotFoundError: No module named 'aeryn_core'`

**Solution:**
```bash
# Ensure venv is activated
source venv-proot/bin/activate

# Verify sys.path
python -c "import sys; print(sys.path)"

# The code includes this at top of aeryn_api.py:
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
```

---

### Issue: Rate Limiter TypeError

**Symptom:** `TypeError` in rate limiter middleware.

**Known issue:** The rate limiter middleware has a known TypeError. Check:

```python
# aeryn_core/auth/rate_limiter.py
# The middleware may have signature issues

# Workaround: Check middleware registration
# In aeryn_api.py, rate limiting is applied per-endpoint
```

**Debug:**
```bash
grep -n "rate_limiter" apps/api/aeryn_api.py
python -c "from aeryn_core.auth.rate_limiter import get_rate_limiter; rl = get_rate_limiter(); print(rl)"
```

---

### Issue: /plugins Route Conflict

**Symptom:** API `/plugins` endpoint conflicts with SPA `/plugins` page.

**Cause:** The `/plugins` API route (plugin system) conflicts with the SPA route for the plugins dashboard page.

**Solution:** Use different paths:
- API: `/api/v1/plugins/` (with prefix)
- SPA: `/plugins` (dashboard page)

**Status:** Known issue — prioritize SPA route, move API to `/api/v1/plugins/`.

---

### Issue: SQLite Database Locked

**Symptom:** `database is locked` errors.

**Cause:** Concurrent writes without proper WAL configuration.

**Solution:**
```python
# Ensure WAL patch is imported FIRST
import aeryn_core.utils.patch_sqlite  # noqa

# This sets:
# - journal_mode=WAL
# - busy_timeout=5000
```

**If still occurring:**
```bash
# Check for stale lock files
ls -la data/*.db-*

# Remove stale locks
rm -f data/*.db-journal data/*.db-wal data/*.db-shm

# Restart
pm2 restart aeryn-api
```

---

## Debug Tools

### PM2 Logs
```bash
# All logs
pm2 logs

# Specific service
pm2 logs aeryn-api

# Error only
pm2 logs aeryn-api --err

# Last N lines
pm2 logs aeryn-api --lines 100
```

### Log Files
```bash
# Error log
tail -f logs/aeryn-api-error.log

# Output log
tail -f logs/aeryn-api-out.log

# Dashboard logs
tail -f logs/aeryn-dashboard-error.log
```

### Python Debugging
```bash
# Run with Python directly (no PM2)
source venv-proot/bin/activate
python apps/api/aeryn_api.py

# With debug logging
AERYN_LOG_LEVEL=debug python apps/api/aeryn_api.py

# With pdb
python -m pdb apps/api/aeryn_api.py
```

### Browser DevTools (for SPA)

1. Open dashboard at `http://127.0.0.1:3010`
2. Press `F12` for DevTools
3. **Console tab:** JavaScript errors and logs
4. **Network tab:** API request/response inspection
5. **Elements tab:** DOM structure debugging

**Key things to check in DevTools:**
- 404 errors on API calls (wrong endpoint)
- 500 errors (server-side failures)
- WebSocket connection status
- JavaScript exceptions

### SQLite Database Inspection
```bash
# Connect to database
sqlite3 data/aeryn.db

# List tables
.tables

# Check schema
.schema

# Query data
SELECT * FROM vault LIMIT 5;

# Check WAL mode
PRAGMA journal_mode;

# Exit
.quit
```

---

## Error Handling System

### Error Recovery (`aeryn_core/utils/error_recovery.py`)

Provides decorators for resilient operations:

```python
from aeryn_core.utils.error_recovery import with_retry, with_fallback, with_circuit_breaker

# Retry on failure
@with_retry(max_attempts=3, delay=2, backoff=2)
def flaky_api_call():
    # Will retry up to 3 times with exponential backoff
    pass

# Fallback value on failure
@with_fallback(fallback_value={"status": "degraded"})
def risky_operation():
    # Returns fallback_value on any exception
    pass

# Circuit breaker
@with_circuit_breaker(failure_threshold=5, recovery_timeout=60)
def unreliable_service():
    # Stops calling after 5 failures, retries after 60s
    pass
```

### Error Handling (`aeryn_core/utils/error_handling.py`)

Centralized error handling with structured responses.

### Logger (`aeryn_core/utils/logger.py`)

```python
from aeryn_core.utils.logger import info, warn, error, log_exception

# Structured logging
info("User logged in", user_id="user123", ip="192.168.1.1")
warn("Rate limit exceeded", usage=95, limit=100)
error("Database write failed", error=str(e))

# Exception logging with traceback
try:
    risky_operation()
except Exception as e:
    log_exception(e, context={"operation": "risky"})
```

---

## Adaptive System (Self-Healing)

Located in `aeryn_core/adaptive/__init__.py` (34K).

### Key Features
1. **Error Detection & Auto-Recovery** — Catches exceptions and retries with backoff
2. **Recursive Self-Improvement Loop** — Learns from past errors
3. **Adaptive Behavior Adjustment** — Adjusts parameters based on success/failure
4. **Self-Healing Infrastructure** — Restarts failed components

### How to Use
```python
from aeryn_core.adaptive import get_adaptive_system

adaptive = get_adaptive_system()

# Record an error for learning
adaptive.record_error(
    component="api_handler",
    error_message="Connection timeout",
    context={"endpoint": "/api/v1/chat"}
)

# Get recommendation
reccommendation = adaptive.get_recommendation("api_handler", context)

# Check health
health = adaptive.get_health_status()
```

### Health Monitoring
```python
from aeryn_core.utils.performance import get_optimizer, get_uptime

optimizer = get_optimizer()
metrics = optimizer.get_metrics()

uptime = get_uptime()
print(f"Uptime: {uptime}")
```

---

## Debugging Checklist

When something goes wrong, follow this order:

1. **Check PM2 logs:** `pm2 logs aeryn-api --lines 50`
2. **Check error log:** `tail -50 logs/aeryn-api-error.log`
3. **Check port:** `lsof -i :3010`
4. **Check venv:** `which python` (should be venv-proot)
5. **Check .env:** `cat .env` (verify required vars)
6. **Check SQLite:** `sqlite3 data/aeryn.db ".tables"`
7. **Check WAL:** `sqlite3 data/aeryn.db "PRAGMA journal_mode;"`
8. **Run tests:** `python -m pytest tests/ -x -q`
9. **Browser DevTools:** Check Console and Network tabs
10. **Restart services:** `pm2 restart all`

---

## Known Issues & Workarounds

| Issue | Status | Workaround |
|-------|--------|------------|
| PostgreSQL connection errors | Expected — SQLite is used | Ignore non-fatal errors |
| /plugins route conflict | Known | Use `/api/v1/plugins/` for API, `/plugins` for SPA |
| rate_limiter middleware TypeError | Known | Check decorator signature |
| Port 3010 conflict | Occasional | `fuser -k 3010/tcp` then restart |
| SQLite locked on heavy write | Rare | Ensure WAL mode, increase busy_timeout |

---

## Performance Debugging

### Slow API Response
```bash
# Check PM2 memory usage
pm2 status

# Check logs for slow queries
grep "slow\|timeout\|took" logs/aeryn-api-out.log

# Profile Python code
python -m cProfile -s cumulative apps/api/aeryn_api.py
```

### Memory Issues
```bash
# Check memory usage
free -h
pm2 status

# Check for memory leaks
pm2 reload aeryn-api  # Hot reload
```

### Database Performance
```bash
# Check SQLite performance
sqlite3 data/aeryn.db "PRAGMA cache_size;"
sqlite3 data/aeryn.db "PRAGMA page_size;"

# Analyze slow queries
sqlite3 data/aeryn.db "EXPLAIN QUERY SELECT * FROM vault LIMIT 10;"
```