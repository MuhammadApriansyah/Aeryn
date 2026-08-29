#!/usr/bin/env python3
"""
V42.0 — Token Monitoring.
Track and attribute token usage by team/feature/user.
"""

import time
import sqlite3
import threading
from typing import Dict, List, Optional
from pathlib import Path

DATABASE_DIR = Path.home() / "aeryn-core-agent" / "Personalisasi" / "Database"
DB_PATH = DATABASE_DIR / "token_usage.db"


class TokenMonitor:
    """Token usage tracking and attribution."""
    
    def __init__(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    session_id TEXT,
                    user_id TEXT,
                    feature TEXT,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    model TEXT,
                    cost REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_token_session ON token_usage(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_token_user ON token_usage(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_token_time ON token_usage(timestamp)")
            conn.commit()
            conn.close()
    
    def record(self, session_id: str, user_id: str, feature: str,
               prompt_tokens: int, completion_tokens: int, model: str, cost: float):
        """Record token usage."""
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute(
                """INSERT INTO token_usage 
                   (timestamp, session_id, user_id, feature, prompt_tokens, completion_tokens, total_tokens, model, cost)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (time.time(), session_id, user_id, feature, prompt_tokens, completion_tokens,
                 prompt_tokens + completion_tokens, model, cost)
            )
            conn.commit()
            conn.close()
    
    def get_stats(self, user_id: str = None, days: int = 7) -> Dict:
        """Get token usage statistics."""
        cutoff = time.time() - (days * 86400)
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            
            if user_id:
                cursor = conn.execute(
                    """SELECT COUNT(*), SUM(total_tokens), SUM(cost), AVG(total_tokens)
                       FROM token_usage WHERE user_id = ? AND timestamp > ?""",
                    (user_id, cutoff)
                )
            else:
                cursor = conn.execute(
                    """SELECT COUNT(*), SUM(total_tokens), SUM(cost), AVG(total_tokens)
                       FROM token_usage WHERE timestamp > ?""",
                    (cutoff,)
                )
            
            row = cursor.fetchone()
            conn.close()
        
        return {
            "requests": row[0] or 0,
            "total_tokens": row[1] or 0,
            "total_cost": row[2] or 0.0,
            "avg_tokens": row[3] or 0.0,
        }
    
    def check_budget(self, user_id: str, budget: float, days: int = 30) -> bool:
        """Check if user has exceeded budget."""
        cutoff = time.time() - (days * 86400)
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.execute(
                "SELECT SUM(cost) FROM token_usage WHERE user_id = ? AND timestamp > ?",
                (user_id, cutoff)
            )
            total = cursor.fetchone()[0] or 0
            conn.close()
        return total < budget
    
    def cleanup(self, days: int = 90):
        """Clean up old records."""
        cutoff = time.time() - (days * 86400)
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("DELETE FROM token_usage WHERE timestamp < ?", (cutoff,))
            conn.commit()
            conn.close()


monitor = TokenMonitor()
