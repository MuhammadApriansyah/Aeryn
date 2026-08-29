#!/usr/bin/env python3
"""
V41.0 — Phase 3: SSO Providers.
Google, GitHub, SAML SSO integration.
"""

import os
import json
import uuid
import urllib.request
from typing import Dict, List, Optional
import urllib.parse
from typing import Dict, Optional
from datetime import datetime

from aeryn_core.database.neon_db import get_neon
from aeryn_core.utils.logger import info, warn, error

# SSO Config dari environment
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:3010/auth/callback/google")

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.environ.get("GITHUB_REDIRECT_URI", "http://localhost:3010/auth/callback/github")


class SSOManager:
    """SSO authentication manager."""
    
    def __init__(self):
        self.db = get_neon()
        self._init_table()
    
    def _init_table(self):
        """Inisialisasi tabel SSO."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS sso_accounts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                provider_user_id TEXT NOT NULL,
                email TEXT,
                name TEXT,
                avatar_url TEXT,
                access_token TEXT,
                refresh_token TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(provider, provider_user_id)
            );
        """)
        
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_sso_user ON sso_accounts(user_id);
            CREATE INDEX IF NOT EXISTS idx_sso_provider ON sso_accounts(provider, provider_user_id);
        """)
    
    # ── Google OAuth ────────────────────────────
    
    def get_google_auth_url(self) -> str:
        """Generate Google OAuth authorization URL."""
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
            "state": uuid.uuid4().hex,
        }
        
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    
    async def handle_google_callback(self, code: str) -> Optional[Dict]:
        """Handle Google OAuth callback."""
        try:
            # Exchange code for token
            token_data = urllib.parse.urlencode({
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            }).encode()
            
            req = urllib.request.Request(
                "https://oauth2.googleapis.com/token",
                data=token_data,
                method="POST",
            )
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            
            response = urllib.request.urlopen(req, timeout=30)
            tokens = json.loads(response.read().decode())
            
            # Get user info
            req = urllib.request.Request(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            
            response = urllib.request.urlopen(req, timeout=30)
            user_info = json.loads(response.read().decode())
            
            # Find or create user
            sso_account = self.db.fetchone(
                "SELECT * FROM sso_accounts WHERE provider = %s AND provider_user_id = %s",
                ("google", user_info["id"])
            )
            
            if sso_account:
                # Update existing
                self.db.execute("""
                    UPDATE sso_accounts SET
                        email = %s, name = %s, avatar_url = %s,
                        access_token = %s, refresh_token = %s, updated_at = %s
                    WHERE id = %s
                """, (
                    user_info.get("email"),
                    user_info.get("name"),
                    user_info.get("picture"),
                    tokens.get("access_token"),
                    tokens.get("refresh_token"),
                    datetime.now(),
                    sso_account["id"],
                ))
                user_id = sso_account["user_id"]
            else:
                # Create new user
                from aeryn_core.auth.auth import get_auth
                auth = get_auth()
                user = auth.create_user(
                    email=user_info["email"],
                    password=uuid.uuid4().hex,  # Random password, can't be used
                    display_name=user_info.get("name"),
                )
                
                if not user:
                    return None
                
                user_id = user["id"]
                
                self.db.insert('sso_accounts', {
                    'id': f"sso_{uuid.uuid4().hex[:12]}",
                    'user_id': user_id,
                    'provider': 'google',
                    'provider_user_id': user_info["id"],
                    'email': user_info.get("email"),
                    'name': user_info.get("name"),
                    'avatar_url': user_info.get("picture"),
                    'access_token': tokens.get("access_token"),
                    'refresh_token': tokens.get("refresh_token"),
                })
            
            info("Google SSO login", user_id=user_id, email=user_info.get("email"))
            
            return {
                "user_id": user_id,
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "avatar": user_info.get("picture"),
            }
            
        except Exception as e:
            error("Google SSO callback failed", error=str(e))
            return None
    
    # ── GitHub OAuth ────────────────────────────
    
    def get_github_auth_url(self) -> str:
        """Generate GitHub OAuth authorization URL."""
        params = {
            "client_id": GITHUB_CLIENT_ID,
            "redirect_uri": GITHUB_REDIRECT_URI,
            "scope": "read:user user:email",
            "state": uuid.uuid4().hex,
        }
        
        return f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"
    
    async def handle_github_callback(self, code: str) -> Optional[Dict]:
        """Handle GitHub OAuth callback."""
        try:
            # Exchange code for token
            data = urllib.parse.urlencode({
                "code": code,
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "redirect_uri": GITHUB_REDIRECT_URI,
            }).encode()
            
            req = urllib.request.Request(
                "https://github.com/login/oauth/access_token",
                data=data,
                method="POST",
            )
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            req.add_header("Accept", "application/json")
            
            response = urllib.request.urlopen(req, timeout=30)
            tokens = json.loads(response.read().decode())
            
            # Get user info
            req = urllib.request.Request(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {tokens['access_token']}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            
            response = urllib.request.urlopen(req, timeout=30)
            user_info = json.loads(response.read().decode())
            
            # Find or create user
            sso_account = self.db.fetchone(
                "SELECT * FROM sso_accounts WHERE provider = %s AND provider_user_id = %s",
                ("github", str(user_info["id"]))
            )
            
            if sso_account:
                self.db.execute("""
                    UPDATE sso_accounts SET
                        email = %s, name = %s, avatar_url = %s,
                        access_token = %s, updated_at = %s
                    WHERE id = %s
                """, (
                    user_info.get("email"),
                    user_info.get("name") or user_info.get("login"),
                    user_info.get("avatar_url"),
                    tokens.get("access_token"),
                    datetime.now(),
                    sso_account["id"],
                ))
                user_id = sso_account["user_id"]
            else:
                from aeryn_core.auth.auth import get_auth
                auth = get_auth()
                user = auth.create_user(
                    email=user_info.get("email") or f"{user_info['login']}@github.com",
                    password=uuid.uuid4().hex,
                    display_name=user_info.get("name") or user_info.get("login"),
                )
                
                if not user:
                    return None
                
                user_id = user["id"]
                
                self.db.insert('sso_accounts', {
                    'id': f"sso_{uuid.uuid4().hex[:12]}",
                    'user_id': user_id,
                    'provider': 'github',
                    'provider_user_id': str(user_info["id"]),
                    'email': user_info.get("email") or f"{user_info['login']}@github.com",
                    'name': user_info.get("name") or user_info.get("login"),
                    'avatar_url': user_info.get("avatar_url"),
                    'access_token': tokens.get("access_token"),
                })
            
            info("GitHub SSO login", user_id=user_id, username=user_info.get("login"))
            
            return {
                "user_id": user_id,
                "email": user_info.get("email") or f"{user_info['login']}@github.com",
                "name": user_info.get("name") or user_info.get("login"),
                "avatar": user_info.get("avatar_url"),
            }
            
        except Exception as e:
            error("GitHub SSO callback failed", error=str(e))
            return None
    
    # ── SAML ────────────────────────────────────
    
    def get_saml_auth_url(self, idp_url: str) -> str:
        """Generate SAML auth URL (redirect to IdP)."""
        return idp_url
    
    async def handle_saml_callback(self, saml_response: str) -> Optional[Dict]:
        """Handle SAML callback."""
        # TODO: Implement SAML parsing
        warn("SAML callback not yet implemented")
        return None
    
    # ─ Helper ─────────────────────────────────
    
    def get_user_sso_accounts(self, user_id: str) -> List[Dict]:
        """Get user's linked SSO accounts."""
        return self.db.fetchall("""
            SELECT provider, email, name, avatar_url, created_at
            FROM sso_accounts
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
    
    def unlink_sso(self, user_id: str, provider: str) -> bool:
        """Unlink SSO account."""
        self.db.execute(
            "DELETE FROM sso_accounts WHERE user_id = %s AND provider = %s",
            (user_id, provider)
        )
        return True


# Singleton
_sso_manager = None

def get_sso_manager() -> SSOManager:
    global _sso_manager
    if _sso_manager is None:
        _sso_manager = SSOManager()
    return _sso_manager
