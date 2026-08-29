#!/usr/bin/env python3
"""V44.0 — Compliance Module."""
import os
import json
import time
import sqlite3
import threading
from typing import Dict, List

DATABASE_DIR = os.path.join(os.path.expanduser("~"), "aeryn-core-agent", "Personalisasi", "Database")
DB_PATH = os.path.join(DATABASE_DIR, "compliance.db")

class ComplianceModule:
    def __init__(self):
        os.makedirs(DATABASE_DIR, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("CREATE TABLE IF NOT EXISTS compliance_checks (id INTEGER PRIMARY KEY AUTOINCREMENT, standard TEXT, control TEXT, description TEXT, status TEXT, evidence TEXT, last_checked REAL, next_check REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS compliance_reports (id INTEGER PRIMARY KEY AUTOINCREMENT, standard TEXT, generated_at REAL, overall_score TEXT, findings TEXT, recommendations TEXT)")
            conn.commit()
            conn.close()
    
    def add_check(self, standard, control, description, status, evidence, next_check_days=90):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("INSERT INTO compliance_checks (standard, control, description, status, evidence, last_checked, next_check) VALUES (?, ?, ?, ?, ?, ?, ?)", (standard, control, description, status, evidence, time.time(), time.time() + (next_check_days * 86400)))
            conn.commit()
            conn.close()
    
    def get_checks(self, standard=None, status=None):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            if standard and status:
                cursor = conn.execute("SELECT standard, control, description, status, evidence, last_checked, next_check FROM compliance_checks WHERE standard = ? AND status = ? ORDER BY next_check", (standard, status))
            elif standard:
                cursor = conn.execute("SELECT standard, control, description, status, evidence, last_checked, next_check FROM compliance_checks WHERE standard = ? ORDER BY next_check", (standard,))
            else:
                cursor = conn.execute("SELECT standard, control, description, status, evidence, last_checked, next_check FROM compliance_checks ORDER BY next_check")
            results = [{"standard": r[0], "control": r[1], "description": r[2], "status": r[3], "evidence": r[4], "last_checked": r[5], "next_check": r[6]} for r in cursor.fetchall()]
            conn.close()
        return results
    
    def generate_report(self, standard):
        checks = self.get_checks(standard=standard)
        if not checks:
            return {"standard": standard, "score": "N/A", "passed": 0, "failed": 0, "total": 0}
        total = len(checks)
        passed = sum(1 for c in checks if c["status"] == "pass")
        failed = sum(1 for c in checks if c["status"] == "fail")
        score_pct = (passed / total * 100) if total > 0 else 0
        overall = "A" if score_pct >= 95 else "B" if score_pct >= 85 else "C" if score_pct >= 70 else "F"
        return {"standard": standard, "score": overall, "passed": passed, "failed": failed, "total": total, "findings": [c for c in checks if c["status"] == "fail"], "generated_at": time.time()}

compliance_module = ComplianceModule()
