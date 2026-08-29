#!/usr/bin/env python3
"""V41.0 — Phase 2: Auto-Task from Chat.

Convert natural language into structured tasks.
"""

import os, json, sqlite3, re, uuid
from typing import Dict, List, Optional
from datetime import datetime
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR


class AutoTask:
    """Parse natural language into tasks."""
    
    def __init__(self):
        self.db_path = os.path.join(DATABASE_DIR, "auto_tasks.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS parsed_tasks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                source_text TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 5,
                tags TEXT DEFAULT '[]',
                confidence REAL DEFAULT 0.7,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def parse(self, user_id: str, text: str) -> List[Dict]:
        """Parse text into tasks."""
        tasks = []
        
        # Simple pattern matching
        # Pattern: "I need to X" or "I want to X" or "Let me X"
        patterns = [
            r"(?:i need to|i want to|let me|i should|i must|help me)\s+(.+)",
            r"(?:create|build|fix|update|write|research|find|search for)\s+(.+)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                title = match.strip().capitalize()
                if len(title) > 5:  # Filter out very short matches
                    task = {
                        "title": title[:100],
                        "description": f"From: {text[:200]}",
                        "priority": 5,
                        "tags": [],
                        "confidence": 0.7,
                    }
                    tasks.append(task)
        
        # Remove duplicates
        seen = set()
        unique = []
        for t in tasks:
            if t["title"] not in seen:
                seen.add(t["title"])
                unique.append(t)
        
        # Store
        conn = sqlite3.connect(self.db_path)
        for t in unique:
            conn.execute("""
                INSERT INTO parsed_tasks (id, user_id, source_text, title, description, priority, tags, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4())[:12],
                user_id,
                text[:500],
                t["title"],
                t["description"],
                t["priority"],
                json.dumps(t["tags"]),
                t["confidence"],
            ))
        conn.commit()
        conn.close()
        
        return unique


# ── Singleton ─────────────────────────────────

_auto_task: Optional[AutoTask] = None

def get_auto_task() -> AutoTask:
    global _auto_task
    if _auto_task is None:
        _auto_task = AutoTask()
    return _auto_task
