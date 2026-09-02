#!/usr/bin/env python3
"""V44.0 — Proactive Engine."""
import os
import time
import sqlite3
import threading
from typing import Dict, List

DATABASE_DIR = os.path.join(os.path.expanduser("~"), "aeryn-core-agent", "Personalisasi", "Database")
DB_PATH = os.path.join(DATABASE_DIR, "proactive.db")

class ProactiveEngine:
    def __init__(self):
        os.makedirs(DATABASE_DIR, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("CREATE TABLE IF NOT EXISTS user_patterns (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, action TEXT, context TEXT, timestamp REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS suggestions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, suggestion TEXT, reason TEXT, priority INTEGER DEFAULT 5, dismissed INTEGER DEFAULT 0, created_at REAL)")
            # Schema migration: detect old schema and migrate
            existing_cols = [r[1] for r in conn.execute("PRAGMA table_info(suggestions)").fetchall()]
            if "suggestion" not in existing_cols and "suggestion_type" in existing_cols:
                # Old schema detected — migrate to new schema
                conn.execute("DROP TABLE suggestions")
                conn.execute("CREATE TABLE suggestions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, suggestion TEXT, reason TEXT, priority INTEGER DEFAULT 5, dismissed INTEGER DEFAULT 0, created_at REAL)")
            conn.commit()
            conn.close()
    
    def record_action(self, user_id, action, context=""):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("INSERT INTO user_patterns (user_id, action, context, timestamp) VALUES (?, ?, ?, ?)", (user_id, action, context, time.time()))
            conn.commit()
            conn.close()
    
    def get_frequent_actions(self, user_id, days=30, limit=10):
        cutoff = time.time() - (days * 86400)
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.execute("SELECT action, COUNT(*) as count FROM user_patterns WHERE user_id = ? AND timestamp > ? GROUP BY action ORDER BY count DESC LIMIT ?", (user_id, cutoff, limit))
            results = [{"action": r[0], "count": r[1]} for r in cursor.fetchall()]
            conn.close()
        return results
    
    def generate_suggestions(self, user_id):
        frequent = self.get_frequent_actions(user_id, days=7, limit=5)
        suggestions = []
        for item in frequent:
            if item["count"] >= 3:
                suggestions.append({"suggestion": f"You often do '{item['action']}'. Would you like to automate this?", "reason": f"Frequent action ({item['count']} times)", "priority": min(10, item["count"])})
        hour = time.localtime().tm_hour
        if hour < 9:
            suggestions.append({"suggestion": "Good morning! Summary of today's tasks?", "reason": "Time-based", "priority": 3})
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            for s in suggestions:
                conn.execute("INSERT INTO suggestions (user_id, suggestion, reason, priority, created_at) VALUES (?, ?, ?, ?, ?)", (user_id, s["suggestion"], s["reason"], s["priority"], time.time()))
            conn.commit()
            conn.close()
        return suggestions

proactive_engine = ProactiveEngine()
