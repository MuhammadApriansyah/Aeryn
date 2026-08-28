#!/usr/bin/env python3
"""V41.0 — Phase 3: Usage Metering."""

import os, json, sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class UsageMetering:
    """Track usage per user for billing."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.expanduser(
            "~/aeryn-core-agent/Personalisasi/Database/usage.db"
        )
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS usage_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                endpoint TEXT,
                tokens_input INTEGER DEFAULT 0,
                tokens_output INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_events(user_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_usage_date ON usage_events(created_at);
        """)
        conn.commit()
        conn.close()
    
    def track(self, user_id: str, event_type: str, endpoint: str = None,
              tokens_input: int = 0, tokens_output: int = 0, cost: float = 0.0,
              metadata: dict = None):
        """Track a usage event."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO usage_events (user_id, event_type, endpoint, tokens_input, tokens_output, cost, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, event_type, endpoint, tokens_input, tokens_output, cost, json.dumps(metadata or {})))
        conn.commit()
        conn.close()
    
    def get_summary(self, user_id: str = None, days: int = 30) -> Dict:
        """Get usage summary."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        
        if user_id:
            row = conn.execute("""
                SELECT COUNT(*), SUM(tokens_input), SUM(tokens_output), SUM(cost)
                FROM usage_events
                WHERE user_id = ? AND created_at >= ?
            """, (user_id, since)).fetchone()
        else:
            row = conn.execute("""
                SELECT COUNT(*), SUM(tokens_input), SUM(tokens_output), SUM(cost)
                FROM usage_events
                WHERE created_at >= ?
            """, (since,)).fetchone()
        
        conn.close()
        
        return {
            "period_days": days,
            "total_events": row[0] or 0,
            "total_tokens_input": row[1] or 0,
            "total_tokens_output": row[2] or 0,
            "total_cost": row[3] or 0.0,
        }
    
    def get_events(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get recent usage events."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT event_type, endpoint, tokens_input, tokens_output, cost, metadata, created_at
            FROM usage_events
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
        conn.close()
        
        return [
            {
                "event_type": r[0],
                "endpoint": r[1],
                "tokens_input": r[2],
                "tokens_output": r[3],
                "cost": r[4],
                "metadata": json.loads(r[5]),
                "created_at": r[6],
            }
            for r in rows
        ]


# ── Singleton ─────────────────────────────────

_metering: Optional[UsageMetering] = None

def get_usage_metering() -> UsageMetering:
    global _metering
    if _metering is None:
        _metering = UsageMetering()
    return _metering
