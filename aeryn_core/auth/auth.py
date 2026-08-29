#!/usr/bin/env python3
"""
V41.0 — Auth System: users, JWT, API keys, RBAC.
Uses PostgreSQL (Neon) as backend.
"""

import os
import json
import hashlib
import secrets
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from aeryn_core.utils.config import DATABASE_DIR, JWT_SECRET
from aeryn_core.utils.logger import info, warn, error, log_exception
from aeryn_core.database.neon_db import get_neon

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
    
    def __init__(self):
        self.db = get_neon()
    
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
        try:
            user_id = secrets.token_hex(8)
            password_hash = self._hash_password(password)
            
            self.db.insert('users', {
                'id': user_id,
                'email': email,
                'password_hash': password_hash,
                'display_name': display_name or email.split("@")[0],
                'role': role,
            })
            
            info("User created", email=email, role=role)
            return {
                "id": user_id,
                "email": email,
                "display_name": display_name or email.split("@")[0],
                "role": role,
            }
        except Exception as e:
            warn("User creation failed", email=email, error=str(e))
            return None
    
    def authenticate(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email + password."""
        user = self.db.fetchone(
            "SELECT id, email, password_hash, display_name, role, is_active FROM users WHERE email = %s",
            (email,)
        )
        
        if not user:
            warn("Login failed — user not found", email=email)
            return None
        
        if not user.get('is_active'):
            warn("Login failed — inactive user", email=email)
            return None
        
        if not self._verify_password(password, user['password_hash']):
            warn("Login failed — wrong password", email=email)
            return None
        
        # Update last login
        self.db.execute(
            "UPDATE users SET last_login = %s WHERE id = %s",
            (datetime.now(), user['id'])
        )
        
        info("User authenticated", email=email, role=user['role'])
        return {
            "id": user['id'],
            "email": user['email'],
            "display_name": user['display_name'],
            "role": user['role'],
        }
    
    def generate_token(self, user_id: str, expires_hours: int = 24) -> str:
        """Generate a session token."""
        token = secrets.token_hex(32)
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        self.db.insert('sessions', {
            'token': token,
            'user_id': user_id,
            'expires_at': expires_at,
        })
        
        return token
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate a session token and return user info."""
        session = self.db.fetchone("""
            SELECT s.token, s.user_id, s.expires_at, u.email, u.display_name, u.role
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = %s
        """, (token,))
        
        if not session:
            return None
        
        if session['expires_at'] < datetime.now():
            # Token expired
            self.db.execute("DELETE FROM sessions WHERE token = %s", (token,))
            return None
        
        return {
            "id": session['user_id'],
            "email": session['email'],
            "display_name": session['display_name'],
            "role": session['role'],
        }
    
    def generate_api_key(self, user_id: str, name: str = "default",
                         scopes: List[str] = None, expires_days: int = 365) -> str:
        """Generate an API key for a user."""
        api_key = "ak_" + secrets.token_hex(24)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        expires_at = datetime.now() + timedelta(days=expires_days)
        scopes_json = json.dumps(scopes or [Permission.CHAT_READ])
        
        self.db.insert('api_keys', {
            'id': secrets.token_hex(8),
            'user_id': user_id,
            'key_hash': key_hash,
            'name': name,
            'scopes': scopes_json,
            'expires_at': expires_at,
        })
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key and return user info."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        result = self.db.fetchone("""
            SELECT k.user_id, k.scopes, k.expires_at, u.email, u.display_name, u.role
            FROM api_keys k
            JOIN users u ON k.user_id = u.id
            WHERE k.key_hash = %s AND k.is_active = 1
        """, (key_hash,))
        
        if not result:
            return None
        
        if result['expires_at'] < datetime.now():
            return None
        
        # Update last used
        self.db.execute(
            "UPDATE api_keys SET last_used = %s WHERE key_hash = %s",
            (datetime.now(), key_hash)
        )
        
        return {
            "id": result['user_id'],
            "email": result['email'],
            "display_name": result['display_name'],
            "role": result['role'],
            "scopes": json.loads(result['scopes']),
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
