#!/usr/bin/env python3
"""V41.0 — Phase 1: Proactive Engine v1.

Generates proactive suggestions based on context:
- Time-based reminders
- Pattern-based suggestions
- Follow-up recommendations
- Anomaly detection
"""

import os, json, sqlite3, asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class Suggestion:
    def __init__(self, user_id: str, suggestion_type: str, title: str,
                 description: str, priority: str = "normal", metadata: dict = None):
        self.id = None
        self.user_id = user_id
        self.suggestion_type = suggestion_type  # reminder, follow_up, pattern, anomaly
        self.title = title
        self.description = description
        self.priority = priority
        self.metadata = metadata or {}
        self.is_read = False
        self.created_at = datetime.now().isoformat()


class ProactiveEngine:
    """Generate proactive suggestions."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.expanduser(
            "~/aeryn-core-agent/Personalisasi/Database/proactive.db"
        )
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                suggestion_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                metadata TEXT DEFAULT '{}',
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_sugg_user ON suggestions(user_id, is_read, created_at DESC);
        """)
        conn.commit()
        conn.close()
    
    def create_suggestion(self, suggestion: Suggestion) -> str:
        import uuid
        sid = str(uuid.uuid4())[:12]
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO suggestions (id, user_id, suggestion_type, title, description, priority, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            sid, suggestion.user_id, suggestion.suggestion_type,
            suggestion.title, suggestion.description, suggestion.priority,
            json.dumps(suggestion.metadata)
        ))
        conn.commit()
        conn.close()
        
        return sid
    
    def get_unread(self, user_id: str = None, limit: int = 10) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        if user_id:
            rows = conn.execute("""
                SELECT id, user_id, suggestion_type, title, description, priority, metadata, created_at
                FROM suggestions WHERE user_id = ? AND is_read = 0
                ORDER BY created_at DESC LIMIT ?
            """, (user_id, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT id, user_id, suggestion_type, title, description, priority, metadata, created_at
                FROM suggestions WHERE is_read = 0
                ORDER BY created_at DESC LIMIT ?
            """, (limit,)).fetchall()
        conn.close()
        
        return [
            {
                "id": r[0], "user_id": r[1], "type": r[2], "title": r[3],
                "description": r[4], "priority": r[5], "metadata": json.loads(r[6]),
                "created_at": r[7],
            }
            for r in rows
        ]
    
    def mark_read(self, suggestion_id: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE suggestions SET is_read = 1 WHERE id = ?", (suggestion_id,))
        conn.commit()
        conn.close()
    
    def generate_time_based(self, user_id: str) -> List[Dict]:
        """Generate time-based suggestions (greeting, daily summary, etc.)."""
        suggestions = []
        now = datetime.now()
        hour = now.hour
        
        # Morning greeting
        if hour < 10:
            suggestions.append({
                "type": "greeting",
                "title": f"Good morning! It's {now.strftime('%A, %B %d')}",
                "description": "Here's your daily briefing...",
                "priority": "low",
            })
        
        # Afternoon check-in
        elif hour >= 13 and hour < 14:
            suggestions.append({
                "type": "check_in",
                "title": "Afternoon check-in",
                "description": "Don't forget to take a break!",
                "priority": "low",
            })
        
        return suggestions
    
    def generate_follow_ups(self, user_id: str, db_path: str = None) -> List[Dict]:
        """Generate follow-up suggestions based on conversation history."""
        suggestions = []
        
        # Check for recent tasks
        from aeryn_core.shared_db import get_shared_db
        db = get_shared_db()
        pending = db.get_pending_tasks()
        
        if pending:
            suggestions.append({
                "type": "follow_up",
                "title": f"You have {len(pending)} pending tasks",
                "description": "Would you like to review them?",
                "priority": "normal",
                "metadata": {"task_count": len(pending)},
            })
        
        return suggestions
    
    def generate_all(self, user_id: str) -> List[Dict]:
        """Generate all types of suggestions."""
        all_suggestions = []
        all_suggestions.extend(self.generate_time_based(user_id))
        all_suggestions.extend(self.generate_follow_ups(user_id))
        
        # Store in DB
        for s in all_suggestions:
            suggestion = Suggestion(
                user_id=user_id,
                suggestion_type=s["type"],
                title=s["title"],
                description=s["description"],
                priority=s.get("priority", "normal"),
                metadata=s.get("metadata", {}),
            )
            self.create_suggestion(suggestion)
        
        return all_suggestions


# ── Singleton ─────────────────────────────────

_engine: Optional[ProactiveEngine] = None

def get_proactive_engine() -> ProactiveEngine:
    global _engine
    if _engine is None:
        _engine = ProactiveEngine()
    return _engine
