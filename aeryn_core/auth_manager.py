#!/usr/bin/env python3
"""V40.43 — SSO/SSO + RBAC: Authentication and role-based access control."""

import os, sys, json, sqlite3, hashlib, uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/auth.db")

class AuthManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL, email TEXT, role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            );
            CREATE TABLE IF NOT EXISTS roles (
                name TEXT PRIMARY KEY, description TEXT, permissions TEXT DEFAULT '[]',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS audit_auth (
                id TEXT PRIMARY KEY, user_id TEXT, action TEXT, ip_address TEXT,
                success INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
        self._seed_roles()
    
    def _seed_roles(self):
        roles = [
            ("admin", "Full access", '["read","write","delete","admin","manage_users"]'),
            ("user", "Standard user", '["read","write"]'),
            ("viewer", "Read only", '["read"]'),
        ]
        conn = sqlite3.connect(self.db_path)
        for r in roles:
            conn.execute("INSERT OR IGNORE INTO roles (name, description, permissions) VALUES (?,?,?)", r)
        conn.commit()
        conn.close()
    
    def create_user(self, username: str, password: str, role: str = "user") -> str:
        user_id = str(uuid.uuid4())[:8]
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO users (id, username, password_hash, role) VALUES (?,?,?,?)",
                     (user_id, username, pw_hash, role))
        conn.commit()
        conn.close()
        return user_id
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT id FROM users WHERE username=? AND password_hash=? AND is_active=1",
            (username, pw_hash)
        ).fetchone()
        conn.close()
        
        if row:
            token = str(uuid.uuid4())
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?,?,?)",
                         (token, row[0], (datetime.now() + timedelta(days=7)).isoformat()))
            conn.commit()
            conn.close()
            return token
        return None
    
    def check_permission(self, token: str, permission: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("""
            SELECT u.role FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ? AND s.expires_at > ?
        """, (token, datetime.now().isoformat())).fetchone()
        
        if not row:
            conn.close()
            return False
        
        role_row = conn.execute(
            "SELECT permissions FROM roles WHERE name=?", (row[0],)
        ).fetchone()
        conn.close()
        
        if role_row:
            perms = json.loads(role_row[0]) if role_row[0] else []
            return permission in perms
        return False

_auth = None
def get_auth() -> AuthManager:
    global _auth
    if _auth is None: _auth = AuthManager()
    return _auth

if __name__ == "__main__":
    auth = get_auth()
    uid = auth.create_user("test", "password123", "admin")
    token = auth.authenticate("test", "password123")
    print(f"Auth: {token is not None}")
    if token:
        print(f"Admin: {auth.check_permission(token, 'admin')}")
