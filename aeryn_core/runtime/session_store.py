"""Session State — persistent checkpointer + multi-user isolation.

Per research (AWS/Azure playbook requirement #2):
- "checkpointer that survives process restarts"
- "scales across multiple instances"
- "isolates state between users"

Design:
- PersistentSessionStore: SQLite-backed (survives restart)
- User-scoped sessions: each user gets isolated session namespace
- Session = user_id + session_id composite key (no cross-user bleed)
"""

import os
import json
import sqlite3
import threading
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from aeryn_core.utils.config import DATABASE_DIR


@dataclass
class PersistentSession:
    """A session scoped to a specific user."""
    session_id: str
    user_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    title: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "message_count": len(self.messages),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "title": self.title,
        }


class PersistentSessionStore:
    """SQLite-backed session checkpointer with user isolation."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(DATABASE_DIR, "sessions.db")
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                messages TEXT DEFAULT '[]',
                title TEXT DEFAULT '',
                created_at REAL,
                updated_at REAL,
                PRIMARY KEY (user_id, session_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
        conn.commit()
        conn.close()

    def save_session(self, user_id: str, session_id: str, messages: List[Dict[str, Any]], title: str = ""):
        """Save (upsert) a session, isolated by user_id."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            now = time.time()
            # Check if exists to preserve created_at
            exists = conn.execute(
                "SELECT created_at FROM sessions WHERE user_id = ? AND session_id = ?",
                (user_id, session_id)
            ).fetchone()

            if exists:
                conn.execute(
                    "UPDATE sessions SET messages = ?, title = ?, updated_at = ? WHERE user_id = ? AND session_id = ?",
                    (json.dumps(messages), title, now, user_id, session_id)
                )
            else:
                conn.execute(
                    "INSERT INTO sessions (user_id, session_id, messages, title, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                    (user_id, session_id, json.dumps(messages), title, now, now)
                )
            conn.commit()
            conn.close()

    def load_session(self, user_id: str, session_id: str) -> Optional[PersistentSession]:
        """Load a session, scoped to user_id."""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT * FROM sessions WHERE user_id = ? AND session_id = ?",
            (user_id, session_id)
        ).fetchone()
        conn.close()

        if not row:
            return None

        cols = ["user_id", "session_id", "messages", "title", "created_at", "updated_at"]
        data = dict(zip(cols, row))
        return PersistentSession(
            session_id=data["session_id"],
            user_id=data["user_id"],
            messages=json.loads(data["messages"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            title=data["title"],
        )

    def list_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """List sessions for a specific user (isolated)."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT session_id, title, created_at, updated_at, messages FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        conn.close()

        result = []
        for row in rows:
            messages = json.loads(row[4])
            result.append({
                "session_id": row[0],
                "title": row[1],
                "created_at": row[2],
                "updated_at": row[3],
                "message_count": len(messages),
            })
        return result

    def delete_session(self, user_id: str, session_id: str):
        """Delete a session, isolated by user_id."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM sessions WHERE user_id = ? AND session_id = ?", (user_id, session_id))
            conn.commit()
            conn.close()


# Global store
_store = None

def get_session_store() -> PersistentSessionStore:
    global _store
    if _store is None:
        _store = PersistentSessionStore()
    return _store