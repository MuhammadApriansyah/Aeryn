#!/usr/bin/env python3
"""
V41.0 — Auth System: users, JWT, API keys, RBAC.
"""

import os
import json
import hashlib
import secrets
import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from aeryn_core.config import DATABASE_DIR, JWT_SECRET
from aeryn_core.logger import info, warn, error, log_exception

DB_PATH = os.path.join(DATABASE_DIR, "auth.db")

# ── Roles & Permissions ──────────────────────

@dataclass
class Permission:
    """Permission constants."""
    CHAT_READ = "chat:read"
    CHAT_WRITE = "chat:write"
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    USAGE_READ = "usage:read"
    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"

ROLE_PERMISSIONS = {
    "admin": [
        Permission.CHAT_READ, Permission.CHAT_WRITE,
        Permission.ADMIN_READ, Permission.ADMIN_WRITE,
        Permission.USAGE_READ, Permission.BILLING_READ, Permission.BILLING_WRITE,
    ],
    "user": [
        Permission.CHAT_READ, Permission.CHAT_WRITE,
        Permission.USAGE_READ, Permission.BILLING_READ,
    ],
    "readonly": [
        Permission.CHAT_READ, Permission.USAGE_READ, Permission.BILLING_READ,
    ],
}


class AuthManager:
    """Authentication and authorization manager."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize auth database schema."""
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                email_verified INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                key_hash TEXT UNIQUE NOT NULL,
                name TEXT DEFAULT 'default',
                scopes TEXT DEFAULT '["chat:read"]',
                expires_at TEXT,
                last_used TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
            
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
            CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
        """)
        conn.commit()
        conn.close()
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt using PBKDF2."""
        salt = secrets.token_hex(16)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return salt + pwdhash.hex()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        salt = password_hash[:32]
        stored_hash = password_hash[32:]
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return pwdhash.hex() == stored_hash
    
    def create_user(self, email: str, password: str, display_name: str = None,
                    role: str = "user") -> Optional[Dict]:
        """Create a new user."""
        conn = sqlite3.connect(self.db_path)
        try:
            user_id = secrets.token_hex(8)
            password_hash = self._hash_password(password)
            conn.execute("""
                INSERT INTO users (id, email, password_hash, display_name, role)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, email, password_hash, display_name or email.split("@")[0], role))
            conn.commit()
            
            info("User created", email=email, role=role)
            return {
                "id": user_id,
                "email": email,
                "display_name": display_name or email.split("@")[0],
                "role": role,
            }
        except sqlite3.IntegrityError:
            warn("User creation failed — email exists", email=email)
            return None
        finally:
            conn.close()
    
    def authenticate(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email + password."""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT id, email, password_hash, display_name, role, is_active FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        conn.close()
        
        if not row:
            warn("Login failed — user not found", email=email)
            return None
        
        user_id, email, pwd_hash, display_name, role, is_active = row
        
        if not is_active:
            warn("Login failed — inactive user", email=email)
            return None
        
        if not self._verify_password(password, pwd_hash):
            warn("Login failed — wrong password", email=email)
            return None
        
        # Update last login
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE users SET last_login = ? WHERE id = ?",
                     (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()
        
        info("User authenticated", email=email, role=role)
        return {
            "id": user_id,
            "email": email,
            "display_name": display_name,
            "role": role,
        }
    
    def generate_token(self, user_id: str, expires_hours: int = 24) -> str:
        """Generate a session token."""
        token = secrets.token_hex(32)
        expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)
        """, (token, user_id, expires_at))
        conn.commit()
        conn.close()
        
        return token
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate a session token and return user info."""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("""
            SELECT s.token, s.user_id, s.expires_at, u.email, u.display_name, u.role
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
        """, (token,)).fetchone()
        conn.close()
        
        if not row:
            return None
        
        token, user_id, expires_at, email, display_name, role = row
        
        if datetime.fromisoformat(expires_at) < datetime.now():
            # Token expired
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            conn.close()
            return None
        
        return {
            "id": user_id,
            "email": email,
            "display_name": display_name,
            "role": role,
        }
    
    def generate_api_key(self, user_id: str, name: str = "default",
                         scopes: List[str] = None, expires_days: int = 365) -> str:
        """Generate an API key for a user."""
        api_key = "ak_" + secrets.token_hex(24)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
        scopes_json = json.dumps(scopes or [Permission.CHAT_READ])
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO api_keys (id, user_id, key_hash, name, scopes, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (secrets.token_hex(8), user_id, key_hash, name, scopes_json, expires_at))
        conn.commit()
        conn.close()
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key and return user info."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("""
            SELECT k.user_id, k.scopes, k.expires_at, u.email, u.display_name, u.role
            FROM api_keys k
            JOIN users u ON k.user_id = u.id
            WHERE k.key_hash = ? AND k.is_active = 1
        """, (key_hash,)).fetchone()
        conn.close()
        
        if not row:
            return None
        
        user_id, scopes, expires_at, email, display_name, role = row
        
        if datetime.fromisoformat(expires_at) < datetime.now():
            return None
        
        # Update last used
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE api_keys SET last_used = ? WHERE key_hash = ?",
                     (datetime.now().isoformat(), key_hash))
        conn.commit()
        conn.close()
        
        return {
            "id": user_id,
            "email": email,
            "display_name": display_name,
            "role": role,
            "scopes": json.loads(scopes),
        }
    
    def has_permission(self, user: Dict, permission: str) -> bool:
        """Check if user has a specific permission."""
        role = user.get("role", "readonly")
        permissions = ROLE_PERMISSIONS.get(role, [])
        return permission in permissions


# ── Singleton ────────────────────────────────

_auth_manager = None


def get_auth() -> AuthManager:
    """Get or create auth manager singleton."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


def create_admin_user(email: str, password: str) -> Optional[Dict]:
    """Create an admin user."""
    auth = get_auth()
    return auth.create_user(email, password, role="admin")
