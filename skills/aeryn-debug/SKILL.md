# Aeryn Debug Skill

> Procedural knowledge untuk debug dan troubleshoot Aeryn.

---

## Common Issues

### 1. Import Error setelah Restructure

Jika `ModuleNotFoundError: No module named 'aeryn_core.xxx'`:

1. Cek apakah file ada di `aeryn_core/{category}/xxx.py`
2. Cek `__init__.py` di category folder
3. Cek import path di file yang import

### 2. Database Locked

Jika muncul `database is locked`:

```bash
# Cek WAL mode
for db in Personalisasi/Database/*.db; do
    sqlite3 "$db" "PRAGMA journal_mode;"
done

# Fix: set WAL mode
for db in Personalisasi/Database/*.db; do
    sqlite3 "$db" "PRAGMA journal_mode=WAL;"
done
```

### 3. Neon PostgreSQL Offline

Jika Neon offline, cek:
1. Koneksi internet
2. Credential di `aeryn_core/database/neon_db.py`
3. Apakah database masih exist di Neon console

Fallback: aplikasi tetap jalan dengan SQLite.

### 4. Test Failure

```bash
# Run specific test
./venv-proot/bin/python -m pytest tests/test_xxx.py -v

# Run all tests
./venv-proot/bin/python -m pytest tests/ -q

# Check syntax semua file
find aeryn_core apps/api -name '*.py' -exec python3 -m py_compile {} \;
```

### 5. Port 3010 Already in Use

```bash
# Kill existing process
pkill -f aeryn_api.py
# Or restart PM2
pm2 restart aeryn-api
```

---

## Debug Checklist

1. ✅ API running (`curl http://127.0.0.1:3010/health`)
2. ✅ Tests pass (`./venv-proot/bin/python -m pytest tests/ -q`)
3. ✅ No shell=True (`grep -r 'shell=True' aeryn_core/`)
4. ✅ No SQL injection (`grep -r 'f"SELECT' aeryn_core/`)
5. ✅ WAL mode active
6. ✅ Neon PostgreSQL connected
7. ✅ Logs clean (`tail -20 logs/aeryn-api-*.log`)

---

*Last updated: 2026-08-29*
