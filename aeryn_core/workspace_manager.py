#!/usr/bin/env python3
"""
V41.0 — Phase 3: Team Workspaces.
Shared memory per team/organization.
"""

import os
import json
import uuid
import re
from typing import Dict, List, Optional
from datetime import datetime

from aeryn_core.neon_db import get_neon
from aeryn_core.logger import info, warn, error


class WorkspaceManager:
    """Manage team workspaces."""
    
    def __init__(self):
        self.db = get_neon()
        self._init_tables()
    
    def _init_tables(self):
        """Inisialisasi tabel workspaces."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT '',
                owner_id TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                settings TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS workspace_members (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(workspace_id, user_id)
            );
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS workspace_invites (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                email TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                role TEXT DEFAULT 'member',
                invited_by TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                accepted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                FOREIGN KEY (invited_by) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_workspaces_owner ON workspaces(owner_id);
            CREATE INDEX IF NOT EXISTS idx_workspace_members_user ON workspace_members(user_id);
            CREATE INDEX IF NOT EXISTS idx_workspace_members_workspace ON workspace_members(workspace_id);
            CREATE INDEX IF NOT EXISTS idx_workspace_invites_token ON workspace_invites(token);
        """)
    
    def _slugify(self, name: str) -> str:
        """Convert name to URL-safe slug."""
        slug = name.lower().strip()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        if not slug:
            slug = f"ws-{uuid.uuid4().hex[:8]}"
        return slug
    
    def create_workspace(self, name: str, owner_id: str,
                         description: str = None) -> Optional[Dict]:
        """Create a new workspace."""
        slug = self._slugify(name)
        
        # Check if slug exists
        existing = self.db.fetchone(
            "SELECT id FROM workspaces WHERE slug = %s",
            (slug,)
        )
        
        if existing:
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        
        workspace_id = f"ws_{uuid.uuid4().hex[:12]}"
        
        self.db.insert('workspaces', {
            'id': workspace_id,
            'name': name,
            'slug': slug,
            'description': description or '',
            'owner_id': owner_id,
        })
        
        # Add owner as admin
        self.db.insert('workspace_members', {
            'id': f"wm_{uuid.uuid4().hex[:12]}",
            'workspace_id': workspace_id,
            'user_id': owner_id,
            'role': 'admin',
        })
        
        info("Workspace created", workspace_id=workspace_id, name=name, owner=owner_id)
        return {
            "id": workspace_id,
            "name": name,
            "slug": slug,
            "owner_id": owner_id,
        }
    
    def get_workspace(self, workspace_id: str) -> Optional[Dict]:
        """Get workspace by ID."""
        return self.db.fetchone(
            "SELECT * FROM workspaces WHERE id = %s",
            (workspace_id,)
        )
    
    def get_workspace_by_slug(self, slug: str) -> Optional[Dict]:
        """Get workspace by slug."""
        return self.db.fetchone(
            "SELECT * FROM workspaces WHERE slug = %s",
            (slug,)
        )
    
    def list_user_workspaces(self, user_id: str) -> List[Dict]:
        """List workspaces where user is a member."""
        return self.db.fetchall("""
            SELECT w.id, w.name, w.slug, w.description, wm.role, w.created_at
            FROM workspaces w
            JOIN workspace_members wm ON w.id = wm.workspace_id
            WHERE wm.user_id = %s AND w.is_active = 1
            ORDER BY w.created_at DESC
        """, (user_id,))
    
    def update_workspace(self, workspace_id: str, name: str = None,
                         description: str = None, settings: Dict = None) -> bool:
        """Update workspace."""
        updates = []
        params = []
        
        if name:
            updates.append("name = %s")
            params.append(name)
        if description:
            updates.append("description = %s")
            params.append(description)
        if settings:
            updates.append("settings = %s")
            params.append(json.dumps(settings))
        
        if not updates:
            return False
        
        updates.append("updated_at = %s")
        params.append(datetime.now())
        params.append(workspace_id)
        
        self.db.execute(
            f"UPDATE workspaces SET {', '.join(updates)} WHERE id = %s",
            tuple(params)
        )
        
        return True
    
    def delete_workspace(self, workspace_id: str) -> bool:
        """Soft delete workspace."""
        self.db.execute(
            "UPDATE workspaces SET is_active = 0 WHERE id = %s",
            (workspace_id,)
        )
        return True
    
    # ── Members ─────────────────────────────────
    
    def add_member(self, workspace_id: str, user_id: str,
                   role: str = "member") -> bool:
        """Add member to workspace."""
        try:
            self.db.insert('workspace_members', {
                'id': f"wm_{uuid.uuid4().hex[:12]}",
                'workspace_id': workspace_id,
                'user_id': user_id,
                'role': role,
            })
            return True
        except Exception:
            return False
    
    def remove_member(self, workspace_id: str, user_id: str) -> bool:
        """Remove member from workspace."""
        self.db.execute("""
            DELETE FROM workspace_members
            WHERE workspace_id = %s AND user_id = %s
        """, (workspace_id, user_id))
        return True
    
    def update_member_role(self, workspace_id: str, user_id: str,
                           role: str) -> bool:
        """Update member role."""
        self.db.execute("""
            UPDATE workspace_members SET role = %s
            WHERE workspace_id = %s AND user_id = %s
        """, (role, workspace_id, user_id))
        return True
    
    def list_members(self, workspace_id: str) -> List[Dict]:
        """List workspace members."""
        return self.db.fetchall("""
            SELECT u.id, u.email, u.display_name, wm.role, wm.joined_at
            FROM workspace_members wm
            JOIN users u ON wm.user_id = u.id
            WHERE wm.workspace_id = %s
            ORDER BY wm.joined_at
        """, (workspace_id,))
    
    def get_member_role(self, workspace_id: str, user_id: str) -> Optional[str]:
        """Get user's role in workspace."""
        result = self.db.fetchone("""
            SELECT role FROM workspace_members
            WHERE workspace_id = %s AND user_id = %s
        """, (workspace_id, user_id))
        return result['role'] if result else None
    
    # ── Invites ─────────────────────────────────
    
    def create_invite(self, workspace_id: str, email: str,
                      invited_by: str, role: str = "member") -> Optional[Dict]:
        """Create workspace invite."""
        token = uuid.uuid4().hex
        expires_at = datetime.now() + __import__('datetime').timedelta(days=7)
        
        invite_id = f"wi_{uuid.uuid4().hex[:12]}"
        
        self.db.insert('workspace_invites', {
            'id': invite_id,
            'workspace_id': workspace_id,
            'email': email,
            'token': token,
            'role': role,
            'invited_by': invited_by,
            'expires_at': expires_at,
        })
        
        return {
            "id": invite_id,
            "token": token,
            "email": email,
            "role": role,
            "expires_at": expires_at.isoformat(),
        }
    
    def accept_invite(self, token: str, user_id: str) -> Optional[Dict]:
        """Accept workspace invite."""
        invite = self.db.fetchone("""
            SELECT * FROM workspace_invites
            WHERE token = %s AND accepted_at IS NULL AND expires_at > %s
        """, (token, datetime.now()))
        
        if not invite:
            return None
        
        # Add member
        self.add_member(invite['workspace_id'], user_id, invite['role'])
        
        # Mark invite as accepted
        self.db.execute("""
            UPDATE workspace_invites SET accepted_at = %s WHERE token = %s
        """, (datetime.now(), token))
        
        return self.get_workspace(invite['workspace_id'])
    
    def list_invites(self, workspace_id: str) -> List[Dict]:
        """List pending invites."""
        return self.db.fetchall("""
            SELECT id, email, role, expires_at, created_at
            FROM workspace_invites
            WHERE workspace_id = %s AND accepted_at IS NULL
            ORDER BY created_at DESC
        """, (workspace_id,))


# Singleton
_workspace_manager = None

def get_workspace_manager() -> WorkspaceManager:
    global _workspace_manager
    if _workspace_manager is None:
        _workspace_manager = WorkspaceManager()
    return _workspace_manager
