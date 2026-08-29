#!/usr/bin/env python3
"""V44.0 — Security Dashboard."""
import os
import time
import sqlite3
import threading
from typing import Dict, List

DATABASE_DIR = os.path.join(os.path.expanduser("~"), "aeryn-core-agent", "Personalisasi", "Database")
DB_PATH = os.path.join(DATABASE_DIR, "security_dashboard.db")

class SecurityDashboard:
    def __init__(self):
        os.makedirs(DATABASE_DIR, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("CREATE TABLE IF NOT EXISTS security_events (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, event_type TEXT, severity TEXT, source TEXT, details TEXT, resolved INTEGER DEFAULT 0)")
            conn.execute("CREATE TABLE IF NOT EXISTS threat_alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, threat_type TEXT, severity TEXT, description TEXT, action_taken TEXT, resolved INTEGER DEFAULT 0)")
            conn.commit()
            conn.close()
    
    def log_event(self, event_type, severity, source, details):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("INSERT INTO security_events (timestamp, event_type, severity, source, details) VALUES (?, ?, ?, ?, ?)", (time.time(), event_type, severity, source, details))
            conn.commit()
            conn.close()
    
    def get_events(self, severity=None, limit=50):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            if severity:
                cursor = conn.execute("SELECT timestamp, event_type, severity, source, details, resolved FROM security_events WHERE severity = ? ORDER BY timestamp DESC LIMIT ?", (severity, limit))
            else:
                cursor = conn.execute("SELECT timestamp, event_type, severity, source, details, resolved FROM security_events ORDER BY timestamp DESC LIMIT ?", (limit,))
            results = [{"timestamp": r[0], "event_type": r[1], "severity": r[2], "source": r[3], "details": r[4], "resolved": r[5]} for r in cursor.fetchall()]
            conn.close()
        return results
    
    def create_alert(self, threat_type, severity, description, action_taken):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("INSERT INTO threat_alerts (timestamp, threat_type, severity, description, action_taken) VALUES (?, ?, ?, ?, ?)", (time.time(), threat_type, severity, description, action_taken))
            conn.commit()
            conn.close()
    
    def get_alerts(self, resolved=False, limit=20):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.execute("SELECT timestamp, threat_type, severity, description, action_taken FROM threat_alerts WHERE resolved = ? ORDER BY timestamp DESC LIMIT ?", (1 if resolved else 0, limit))
            results = [{"timestamp": r[0], "threat_type": r[1], "severity": r[2], "description": r[3], "action_taken": r[4]} for r in cursor.fetchall()]
            conn.close()
        return results
    
    def get_stats(self):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.execute("SELECT severity, COUNT(*) FROM security_events GROUP BY severity")
            events_by_severity = {r[0]: r[1] for r in cursor.fetchall()}
            cursor = conn.execute("SELECT severity, COUNT(*) FROM threat_alerts GROUP BY severity")
            alerts_by_severity = {r[0]: r[1] for r in cursor.fetchall()}
            cursor = conn.execute("SELECT COUNT(*) FROM threat_alerts WHERE resolved = 0")
            unresolved = cursor.fetchone()[0]
            conn.close()
        return {"events_by_severity": events_by_severity, "alerts_by_severity": alerts_by_severity, "unresolved_alerts": unresolved}
    
    def resolve_alert(self, alert_id):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("UPDATE threat_alerts SET resolved = 1 WHERE id = ?", (alert_id,))
            conn.commit()
            conn.close()

security_dashboard = SecurityDashboard()
