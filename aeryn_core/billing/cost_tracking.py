#!/usr/bin/env python3
"""V40.47 — Cost Tracking: Token usage, billing, and budget management."""

import os, sys, json, sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from aeryn_core.utils.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "cost_tracking.db")

class CostTracker:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS usage_log (
                id TEXT PRIMARY KEY, user_id TEXT, session_id TEXT,
                model TEXT, prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0, total_tokens INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0, endpoint TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS budgets (
                user_id TEXT PRIMARY KEY, daily_limit REAL DEFAULT 10.0,
                monthly_limit REAL DEFAULT 100.0, alert_threshold REAL DEFAULT 0.8,
                current_daily REAL DEFAULT 0.0, current_monthly REAL DEFAULT 0.0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS cost_alerts (
                id TEXT PRIMARY KEY, user_id TEXT, alert_type TEXT,
                message TEXT, is_acknowledged INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_usage_user_time ON usage_log(user_id, created_at DESC);
        """)
        conn.commit()
        conn.close()
    
    def log_usage(self, user_id: str, model: str, prompt_tokens: int,
                  completion_tokens: int, endpoint: str = "chat",
                  session_id: str = None) -> Dict:
        import uuid
        
        total = prompt_tokens + completion_tokens
        # Approximate cost (varies by model)
        cost_per_1k = {
            "gpt-4o": 0.005, "gpt-4o-mini": 0.00015, "gpt-3.5-turbo": 0.0005,
            "gemini-3.5-flash-lite": 0.0001, "meituan/longcat-2.0:free": 0.0,
        }.get(model, 0.001)
        
        cost = (total / 1000) * cost_per_1k
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO usage_log (id, user_id, session_id, model, prompt_tokens,
                                   completion_tokens, total_tokens, cost_usd, endpoint)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4())[:8], user_id, session_id, model, prompt_tokens,
              completion_tokens, total, cost, endpoint))
        
        # Update budget tracking
        conn.execute("""
            INSERT OR REPLACE INTO budgets (user_id, current_daily, current_monthly, updated_at)
            VALUES (?, 
                    COALESCE((SELECT current_daily FROM budgets WHERE user_id=?), 0) + ?,
                    COALESCE((SELECT current_monthly FROM budgets WHERE user_id=?), 0) + ?,
                    ?)
        """, (user_id, user_id, cost, user_id, cost, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return {"total_tokens": total, "cost_usd": round(cost, 6)}
    
    def get_usage_summary(self, user_id: str, days: int = 30) -> Dict:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        conn = sqlite3.connect(self.db_path)
        
        row = conn.execute("""
            SELECT COUNT(*), SUM(total_tokens), SUM(cost_usd)
            FROM usage_log WHERE user_id = ? AND created_at >= ?
        """, (user_id, cutoff)).fetchone()
        
        budget_row = conn.execute(
            "SELECT * FROM budgets WHERE user_id=?", (user_id,)
        ).fetchone()
        
        conn.close()
        
        return {
            "period_days": days,
            "total_requests": row[0] or 0,
            "total_tokens": row[1] or 0,
            "total_cost_usd": round(row[2] or 0, 4),
            "daily_limit": budget_row[1] if budget_row else 10.0,
            "monthly_limit": budget_row[2] if budget_row else 100.0,
        }

_cost = None
def get_cost_tracker() -> CostTracker:
    global _cost
    if _cost is None: _cost = CostTracker()
    return _cost
