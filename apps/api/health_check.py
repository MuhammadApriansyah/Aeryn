#!/usr/bin/env python3
"""V39.64 — Health Check & Monitoring for Aeryn."""

import os
import sys
import time
import json
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.config import DATABASE_DIR, ensure_dirs

def check_disk_space():
    """Check available disk space."""
    stat = os.statvfs(DATABASE_DIR)
    free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
    return {"free_gb": round(free_gb, 2), "ok": free_gb > 0.5}

def check_memory():
    """Check memory usage."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        return {
            "total_mb": round(mem.total / 1024 / 1024, 1),
            "used_mb": round(mem.used / 1024 / 1024, 1),
            "percent": mem.percent,
            "ok": mem.percent < 90,
        }
    except ImportError:
        return {"ok": True, "note": "psutil not available"}

def check_database():
    """Check database connectivity."""
    try:
        db_path = os.path.join(DATABASE_DIR, "hybrid_search.db")
        if not os.path.exists(db_path):
            return {"ok": True, "note": "DB not created yet"}
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1")
        conn.close()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def check_safety_engine():
    """Check safety engine is loaded."""
    try:
        from aeryn_core.safety_engine import get_safety_engine
        eng = get_safety_engine()
        result = eng.check_input("test")
        return {"ok": True, "risk": result.risk}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def check_vault():
    """Check vault is accessible."""
    try:
        from aeryn_core.vault import AerynVault, ensure_dirs
        ensure_dirs()
        vault = AerynVault()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def run_health_check():
    """Run all health checks."""
    checks = {
        "timestamp": datetime.now().isoformat(),
        "disk": check_disk_space(),
        "memory": check_memory(),
        "database": check_database(),
        "safety_engine": check_safety_engine(),
        "vault": check_vault(),
    }
    
    all_ok = all(c.get("ok", False) for c in checks.values() if isinstance(c, dict))
    checks["overall"] = "healthy" if all_ok else "degraded"
    
    return checks

if __name__ == "__main__":
    ensure_dirs()
    result = run_health_check()
    print(json.dumps(result, indent=2))
