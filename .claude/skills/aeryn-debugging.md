# Aeryn Debugging Guide

## Quick Start Debugging

```bash
# 1. Check if backend is running
curl http://127.0.0.1:3010/health

# 2. Check PM2 logs
pm2 logs aeryn-api --lines 50

# 3. Check process status
pm2 list

# 4. Restart if needed
pm2 restart aeryn-api
```

## Common Issues & Solutions

### 1. PostgreSQL Connection Errors

**Error**: `connection to server on socket "/var/run/postgresql/.s.PGSQL.3010" failed`

**Cause**: Aeryn uses SQLite, but some code paths try PostgreSQL.

**Solution**: 
- This is EXPECTED behavior — the system gracefully falls back to SQLite
- Check error logs to confirm fallback is working
- Do NOT try to install PostgreSQL

**Log verification**:
```bash
pm2 logs aeryn-api | grep "Database connection failed"
# Should see: "Using SQLite fallback" after the PostgreSQL error
```

### 2. Port Already in Use

**Error**: `Address already in use` when starting server

**Solution**:
```bash
fuser -k 3010/tcp
pm2 restart aeryn-api
```

### 3. API Route Conflict (SPA)

**Problem**: Direct URL access to `/plugins` returns 500 error.

**Cause**: FastAPI API route `/plugins` conflicts with SPA route.

**Workaround**: 
- Use client-side navigation (click menu items)
- Direct URL access for `/plugins` not supported due to PostgreSQL dependency
- All other routes (`/projects`, `/workspaces`, `/chat`, `/audit`, `/settings`) work via direct URL

### 4. Rate Limiter TypeError

**Error**: `RateLimiter.check() got an unexpected keyword argument 'ip_address'`

**Cause**: Existing bug in `apps/api/aeryn_api.py` line 158 — middleware calls `limiter.check()` with wrong signature.

**Status**: Non-fatal — exceptions are caught and logged. API still functions.

**Fix needed**: Update `aeryn_core/auth/rate_limiter.py` or fix middleware in `aeryn_api.py`.

### 5. SQLite Busy Timeout

**Error**: `database is locked`

**Solution**: The patched SQLite connection uses `busy_timeout=5000ms`, but concurrent access may still cause issues.

```python
import aeryn_core.utils.patch_sqlite  # Must be imported first
conn = sqlite3.connect("data.db")
conn.execute("PRAGMA busy_timeout = 5000")
```

## Debugging Tools

### 1. Health Check Endpoint

```bash
curl http://127.0.0.1:3010/health
# {"status":"healthy","memory_mb":24.3,"version":"40.44"}
```

### 2. Adaptive System Endpoints

```bash
curl http://127.0.0.1:3010/api/adaptive/health
curl http://127.0.0.1:3010/api/adaptive/errors
curl -X POST http://127.0.0.1:3010/api/adaptive/run-cycle
```

### 3. API Docs

- Swagger UI: `http://127.0.0.1:3010/docs`
- ReDoc: `http://127.0.0.1:3010/redoc`

### 4. Browser DevTools

For SPA debugging:
1. Open DevTools (F12)
2. Check Console tab for JS errors
3. Check Network tab for API failures
4. Use Application tab to inspect localStorage

### 5. Error Recovery System

```python
from aeryn_core.utils.error_recovery import get_error_recovery, with_retry, with_fallback

recovery = get_error_recovery()

# Check error patterns
errors = recovery.get_error_log()

# Manual recovery
recovery.apply_fix("connection_error", {"retry_count": 3})
```

## Error Handling Architecture

### Error Recovery Strategies

Located in `aeryn_core/utils/error_recovery.py`:

| Strategy | Trigger | Action |
|----------|---------|--------|
| `retry_with_backoff` | Network errors | Retry with exponential backoff |
| `connection_fallback` | DB connection errors | Switch to SQLite fallback |
| `cache_fallback` | API timeout | Return cached response |
| `skip_on_error` | Non-critical errors | Continue with reduced features |

### Using Error Recovery

```python
from aeryn_core.utils.error_recovery import with_retry, with_fallback

# With retry
result = with_retry(risky_function, max_retries=3, delay=2.0)

# With fallback
result = with_fallback(
    primary_func=call_api,
    fallback_func=return_cache,
    exception_types=[TimeoutError, ConnectionError]
)
```

## Adaptive System Debugging

The adaptive system auto-heals. To debug:

```bash
# Run a manual cycle
curl -X POST http://127.0.0.1:3010/api/adaptive/run-cycle

# Check what fixes were applied
curl http://127.0.0.1:3010/api/adaptive/errors
curl http://127.0.0.1:3010/api/adaptive/health

# Check database
sqlite3 Personalisasi/Database/adaptive_system.db "SELECT * FROM adaptations ORDER BY timestamp DESC LIMIT 10;"
```

### Adaptive System Files

| File | Purpose |
|------|---------|
| `aeryn_core/adaptive/__init__.py` | Main adaptive orchestrator |
| `aeryn_core/adaptive/error_detector.py` | Error pattern detection |
| `aeryn_core/adaptive/fallback_chains.py` | Fallback action chains |
| `aeryn_core/adaptive/health_monitor.py` | Real-time health monitoring |
| `aeryn_core/adaptive/fix_applier.py` | Apply automatic fixes |
