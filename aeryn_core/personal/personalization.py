#!/usr/bin/env python3
"""V44.0 — Personalization."""
import os
import time
import sqlite3
import threading
from typing import Dict, List

DATABASE_DIR = os.path.join(os.path.expanduser("~"), "aeryn-core-agent", "Personalisasi", "Database")
DB_PATH = os.path.join(DATABASE_DIR, "personalization.db")

class PersonalizationEngine:
    def __init__(self):
        os.makedirs(DATABASE_DIR, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("CREATE TABLE IF NOT EXISTS preferences (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, key TEXT, value TEXT, updated_at REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, interaction_type TEXT, content TEXT, response TEXT, timestamp REAL)")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_prefs ON preferences(user_id, key)")
            conn.commit()
            conn.close()
    
    def set_preference(self, user_id, key, value):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("INSERT OR REPLACE INTO preferences (user_id, key, value, updated_at) VALUES (?, ?, ?, ?)", (user_id, key, value, time.time()))
            conn.commit()
            conn.close()
    
    def get_preference(self, user_id, key, default=""):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.execute("SELECT value FROM preferences WHERE user_id = ? AND key = ?", (user_id, key))
            row = cursor.fetchone()
            conn.close()
        return row[0] if row else default
    
    def get_all_preferences(self, user_id):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.execute("SELECT key, value FROM preferences WHERE user_id = ?", (user_id,))
            results = {r[0]: r[1] for r in cursor.fetchall()}
            conn.close()
        return results
    
    def add_history(self, user_id, interaction_type, content, response):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("INSERT INTO history (user_id, interaction_type, content, response, timestamp) VALUES (?, ?, ?, ?, ?)", (user_id, interaction_type, content, response, time.time()))
            conn.commit()
            conn.close()
    
    def get_history(self, user_id, limit=20):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.execute("SELECT interaction_type, content, response, timestamp FROM history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
            results = [{"type": r[0], "content": r[1], "response": r[2], "timestamp": r[3]} for r in cursor.fetchall()]
            conn.close()
        return results
    
    def personalize_prompt(self, user_id, base_prompt):
        prefs = self.get_all_preferences(user_id)
        additions = []
        if prefs.get("tone"):
            additions.append(f"Use a {prefs['tone']} tone.")
        if prefs.get("language"):
            additions.append(f"Respond in {prefs['language']}.")
        if additions:
            return f"{base_prompt}\n\nPersonalization: {' '.join(additions)}"
        return base_prompt

personalization_engine = PersonalizationEngine()
