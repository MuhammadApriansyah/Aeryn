"""Identity & Auth — managed identity + least-privilege tool scopes.

Per research (AWS/Azure playbook requirement #4, Contro1):
- Agent needs managed identity (not shared service account)
- Least-privilege scope per tool (not blanket access)
- API key/token per user

Design:
- UserIdentity: user_id + api_key + allowed_tools (least-privilege)
- AuthManager: issue/validate API keys, check tool permission
- API key hashed at rest (never stored plaintext)
"""

import os
import json
import hashlib
import secrets
import sqlite3
import time
import threading
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from aeryn_core.utils.config import DATABASE_DIR


@dataclass
class UserIdentity:
    """A managed identity for a user/agent."""
    user_id: str
    api_key_hash: str
    allowed_tools: List[str]  # least-privilege scope
    role: str = "user"  # user | admin | agent
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "allowed_tools": self.allowed_tools,
            "role": self.role,
            "created_at": self.created_at,
        }


class AuthManager:
    """Issue/validate identities with least-privilege tool scopes."""

    def __init__(self):
        self.db_path = os.path.join(DATABASE_DIR, "auth.db")
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS identities (
                user_id TEXT PRIMARY KEY,
                api_key_hash TEXT NOT NULL,
                allowed_tools TEXT DEFAULT '[]',
                role TEXT DEFAULT 'user',
                created_at REAL,
                last_active REAL
            )
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def _hash_key(api_key: str) -> str:
        """Hash API key with SHA-256 (never store plaintext)."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def issue_key(self, user_id: str, allowed_tools: List[str] = None, role: str = "user") -> str:
        """Issue a new API key for a user. Returns the raw key (shown once)."""
        api_key = f"aeryn_{secrets.token_hex(32)}"
        key_hash = self._hash_key(api_key)

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT OR REPLACE INTO identities (user_id, api_key_hash, allowed_tools, role, created_at, last_active) VALUES (?,?,?,?,?,?)",
                (user_id, key_hash, json.dumps(allowed_tools or []), role, time.time(), time.time())
            )
            conn.commit()
            conn.close()

        return api_key

    def validate_key(self, api_key: str) -> Optional[UserIdentity]:
        """Validate an API key, return identity if valid."""
        key_hash = self._hash_key(api_key)
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT * FROM identities WHERE api_key_hash = ?", (key_hash,)
        ).fetchone()
        conn.close()

        if not row:
            return None

        cols = ["user_id", "api_key_hash", "allowed_tools", "role", "created_at", "last_active"]
        data = dict(zip(cols, row))

        # Update last_active
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute("UPDATE identities SET last_active = ? WHERE user_id = ?", (time.time(), data["user_id"]))
            conn.commit()
            conn.close()

        return UserIdentity(
            user_id=data["user_id"],
            api_key_hash=data["api_key_hash"],
            allowed_tools=json.loads(data["allowed_tools"]),
            role=data["role"],
            created_at=data["created_at"],
            last_active=time.time(),
        )

    def check_tool_permission(self, identity: UserIdentity, tool_name: str) -> bool:
        """Check if a user is allowed to use a tool (least-privilege)."""
        # Empty allowed_tools = all tools allowed (owner/admin)
        if not identity.allowed_tools:
            return True
        if identity.role == "admin":
            return True
        return tool_name in identity.allowed_tools

    def get_identity(self, user_id: str) -> Optional[UserIdentity]:
        """Get identity by user_id."""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT * FROM identities WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        if not row:
            return None
        cols = ["user_id", "api_key_hash", "allowed_tools", "role", "created_at", "last_active"]
        data = dict(zip(cols, row))
        return UserIdentity(
            user_id=data["user_id"],
            api_key_hash=data["api_key_hash"],
            allowed_tools=json.loads(data["allowed_tools"]),
            role=data["role"],
            created_at=data["created_at"],
            last_active=data["last_active"],
        )

    def revoke_key(self, user_id: str):
        """Revoke a user's API key."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM identities WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()


# Global manager
_manager = None

def get_auth_manager() -> AuthManager:
    global _manager
    if _manager is None:
        _manager = AuthManager()
    return _manager