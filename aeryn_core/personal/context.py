#!/usr/bin/env python3
"""V44.0 — Personal Context."""
import os
import json
import time
import sqlite3
import threading

DATABASE_DIR = os.path.join(os.path.expanduser("~"), "aeryn-core-agent", "Personalisasi", "Database")
DB_PATH = os.path.join(DATABASE_DIR, "personal_context.db")

class PersonalContext:
    def __init__(self):
        os.makedirs(DATABASE_DIR, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("CREATE TABLE IF NOT EXISTS user_context (user_id TEXT PRIMARY KEY, name TEXT, role TEXT, goals TEXT, interests TEXT, work_style TEXT, energy_pattern TEXT, updated_at REAL)")
            conn.commit()
            conn.close()
    
    def set_context(self, user_id, name, role="", goals=None, interests=None, work_style="", energy_pattern=""):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("INSERT OR REPLACE INTO user_context (user_id, name, role, goals, interests, work_style, energy_pattern, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (user_id, name, role, json.dumps(goals or []), json.dumps(interests or []), work_style, energy_pattern, time.time()))
            conn.commit()
            conn.close()
    
    def get_context(self, user_id):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.execute("SELECT name, role, goals, interests, work_style, energy_pattern FROM user_context WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()
        if not row:
            return {}
        return {"name": row[0], "role": row[1], "goals": json.loads(row[2]), "interests": json.loads(row[3]), "work_style": row[4], "energy_pattern": row[5]}
    
    def build_system_prompt(self, user_id, base_prompt):
        ctx = self.get_context(user_id)
        if not ctx:
            return base_prompt
        parts = [base_prompt]
        if ctx.get("name"):
            parts.append(f"The user's name is {ctx['name']}.")
        if ctx.get("role"):
            parts.append(f"The user works as a {ctx['role']}.")
        return "\n".join(parts)

personal_context = PersonalContext()
