#!/usr/bin/env python3
"""Audit Trail — Track all actions for compliance."""
import os
import sqlite3
import threading
import time
from typing import Dict, List

DATABASE_DIR = os.path.join(os.path.expanduser("~"), "aeryn-core-agent", "Personalisasi", "Database")
DB_PATH = os.path.join(DATABASE_DIR, "audit_trail.db")

class AuditTrail:
    def __init__(self):
        os.makedirs(DATABASE_DIR, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, user_id TEXT, action TEXT, resource TEXT, details TEXT, ip TEXT)")
            conn.commit()
            conn.close()
    
    def log(self, user_id: str, action: str, resource: str, details: str = "", ip: str = "127.0.0.1"):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("INSERT INTO audit_log (timestamp, user_id, action, resource, details, ip) VALUES (?, ?, ?, ?, ?, ?)", (time.time(), user_id, action, resource, details, ip))
            conn.commit()
            conn.close()
    
    def get_logs(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            if user_id:
                cursor = conn.execute("SELECT timestamp, user_id, action, resource, details, ip FROM audit_log WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
            else:
                cursor = conn.execute("SELECT timestamp, user_id, action, resource, details, ip FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,))
            results = [{"timestamp": r[0], "user_id": r[1], "action": r[2], "resource": r[3], "details": r[4], "ip": r[5]} for r in cursor.fetchall()]
            conn.close()
        return results

audit_trail = AuditTrail()
