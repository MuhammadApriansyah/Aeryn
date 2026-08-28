#!/usr/bin/env python3
"""V41.0 — Phase 3: API Key Management."""

import os, json, sqlite3, uuid, hashlib, secrets
from typing import Dict, Optional, List
from datetime import datetime


class APIKey:
    def __init__(self, user_id: str, name: str, key: str, permissions: list = None):
        self.id = str(uuid.uuid4())[:12]
        self.user_id = user_id
        self.name = name
        self.key = key
        self.permissions = permissions or ["read"]
        self.is_active = True
        self.created_at = datetime.now().isoformat()
        self.last_used = None


class APIKeyManager:
    """Manage API keys for multi-user access."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.expanduser(
            "~/aeryn-core-agent/Personalisasi/Database/api_keys.db"
        )
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                permissions TEXT DEFAULT '["read"]',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_used TEXT,
                request_count INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_key_hash ON api_keys(key_hash);
            CREATE INDEX IF NOT EXISTS idx_key_user ON api_keys(user_id);
        """)
        conn.commit()
        conn.close()
    
    def create(self, user_id: str, name: str, permissions: list = None) -> Dict:
        """Create new API key."""
        raw_key = "ae_" + secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        kid = str(uuid.uuid4())[:12]
        conn.execute("""
            INSERT INTO api_keys (id, user_id, name, key_hash, permissions)
            VALUES (?, ?, ?, ?, ?)
        """, (kid, user_id, name, key_hash, json.dumps(permissions or ["read"])))
        conn.commit()
        conn.close()
        
        return {
            "id": kid,
            "key": raw_key,  # Only shown once
            "name": name,
            "permissions": permissions or ["read"],
        }
    
    def validate(self, raw_key: str) -> Optional[Dict]:
        """Validate API key."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("""
            SELECT id, user_id, name, permissions, is_active FROM api_keys
            WHERE key_hash = ?
        """, (key_hash,)).fetchone()
        
        if not row:
            conn.close()
            return None
        
        if not row[4]:  # is_active
            conn.close()
            return None
        
        # Update usage
        conn.execute("""
            UPDATE api_keys SET last_used = ?, request_count = request_count + 1
            WHERE key_hash = ?
        """, (datetime.now().isoformat(), key_hash))
        conn.commit()
        conn.close()
        
        return {
            "id": row[0],
            "user_id": row[1],
            "name": row[2],
            "permissions": json.loads(row[3]),
        }
    
    def list_keys(self, user_id: str) -> List[Dict]:
        """List user's API keys (without raw keys)."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT id, name, permissions, is_active, created_at, last_used, request_count
            FROM api_keys WHERE user_id = ?
        """, (user_id,)).fetchall()
        conn.close()
        
        return [
            {
                "id": r[0],
                "name": r[1],
                "permissions": json.loads(r[2]),
                "is_active": bool(r[3]),
                "created_at": r[4],
                "last_used": r[5],
                "request_count": r[6],
            }
            for r in rows
        ]
    
    def revoke(self, key_id: str) -> bool:
        """Revoke an API key."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0


# ── Singleton ─────────────────────────────────

_key_manager: Optional[APIKeyManager] = None

def get_api_key_manager() -> APIKeyManager:
    global _key_manager
    if _key_manager is None:
        _key_manager = APIKeyManager()
    return _key_manager
