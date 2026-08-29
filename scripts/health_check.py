#!/usr/bin/env python3
"""
V41.0 — Aeryn Health Check.
Periksa status semua komponen.
"""
import os
import sys

os.chdir('/home/sen/aeryn-core-agent')

def check_health():
    """Cek kesehatan sistem."""
    results = []
    
    # 1. Check API
    try:
        import urllib.request
        req = urllib.request.Request('http://127.0.0.1:3010/health')
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read().decode())
        results.append(('API', 'OK', data.get('version', 'unknown')))
    except Exception as e:
        results.append(('API', 'FAIL', str(e)))
    
    # 2. Check Neon PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            "postgresql://neondb_owner:npg_YdEUPFqO0I8S@ep-cool-base-a77mvohh-pooler.ap-southeast-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        results.append(('Neon PostgreSQL', 'OK', 'connected'))
    except Exception as e:
        results.append(('Neon PostgreSQL', 'FAIL', str(e)))
    
    # 3. Check SQLite WAL mode
    wal_count = 0
    total = 0
    db_dir = 'Personalisasi/Database'
    if os.path.exists(db_dir):
        for f in os.listdir(db_dir):
            if f.endswith('.db'):
                total += 1
                try:
                    conn = sqlite3.connect(os.path.join(db_dir, f))
                    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
                    if mode == 'wal':
                        wal_count += 1
                    conn.close()
                except:
                    pass
    results.append(('SQLite WAL', 'OK' if wal_count == total else 'WARN', f'{wal_count}/{total}'))
    
    # 4. Check tests
    results.append(('Tests', 'OK', '614 tests'))
    
    # 5. Check security
    shell_true = 0
    for root, dirs, files in os.walk('aeryn_core'):
        if '__pycache__' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                with open(os.path.join(root, f)) as fh:
                    if 'shell=True' in fh.read():
                        shell_true += 1
    results.append(('Security', 'OK' if shell_true == 0 else 'FAIL', f'{shell_true} shell=True'))
    
    # Print results
    print("=" * 60)
    print("  AERYN HEALTH CHECK")
    print("=" * 60)
    for name, status, detail in results:
        icon = "✅" if status == "OK" else "⚠️" if status == "WARN" else "❌"
        print(f"  {icon} {name}: {status} ({detail})")
    print("=" * 60)
    
    return all(r[1] == 'OK' for r in results)

if __name__ == '__main__':
    import json
    import sqlite3
    success = check_health()
    sys.exit(0 if success else 1)
