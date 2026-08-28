#!/usr/bin/env python3
"""V40.30 — Constitutional AI: Self-governance via ethical principles."""

import os, sys, json, sqlite3
from typing import Dict, List, Optional
from datetime import datetime

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/constitutional_ai.db")

class ConstitutionalAI:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS principles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                priority INTEGER DEFAULT 5,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS violations (
                id TEXT PRIMARY KEY,
                principle_id TEXT NOT NULL,
                context TEXT,
                severity TEXT DEFAULT 'medium',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
        self._seed_defaults()
    
    def _seed_defaults(self):
        defaults = [
            ("P01", "Do no harm", "Never provide information that could cause physical, psychological, or financial harm", 10),
            ("P02", "Protect privacy", "Never reveal personal, confidential, or sensitive information without authorization", 9),
            ("P03", "Be honest", "Never deceive or mislead; acknowledge uncertainty", 9),
            ("P04", "Respect autonomy", "Respect user's right to make their own decisions", 8),
            ("P05", "Be helpful", "Provide useful, accurate, and relevant information", 7),
            ("P06", "Stay in scope", "Don't exceed authorized capabilities or permissions", 8),
            ("P07", "Transparency", "Be clear about capabilities, limitations, and data usage", 7),
        ]
        conn = sqlite3.connect(self.db_path)
        for d in defaults:
            conn.execute("INSERT OR IGNORE INTO principles (id, name, description, priority) VALUES (?,?,?,?)", d)
        conn.commit()
        conn.close()
    
    def check_action(self, action: str, context: str = "") -> Dict:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT id, name, description FROM principles WHERE is_active=1 ORDER BY priority DESC").fetchall()
        violations = []
        for r in rows:
            if self._violates(action, r[1]):
                violations.append({"principle": r[1], "description": r[2]})
        conn.close()
        return {"allowed": len(violations) == 0, "violations": violations}
    
    def _violates(self, action: str, principle: str) -> bool:
        action_lower = action.lower()
        checks = {
            "Do no harm": any(w in action_lower for w in ["hack", "exploit", "weapon", "bomb", "kill", "harm"]),
            "Protect privacy": any(w in action_lower for w in ["reveal", "leak", "expose private", "dump"]),
            "Stay in scope": any(w in action_lower for w in ["sudo", "root access", "system files"]),
        }
        return checks.get(principle, False)

_cai = None
def get_constitutional_ai() -> ConstitutionalAI:
    global _cai
    if _cai is None: _cai = ConstitutionalAI()
    return _cai

if __name__ == "__main__":
    cai = get_constitutional_ai()
    result = cai.check_action("How to hack a wifi network?")
    print(f"Hack: allowed={result['allowed']}, violations={len(result['violations'])}")
    result = cai.check_action("How to install Docker?")
    print(f"Docker: allowed={result['allowed']}")
