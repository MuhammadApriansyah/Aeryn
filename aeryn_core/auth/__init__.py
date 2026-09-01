"""Auth & Tenancy — Workspace Isolation, RBAC, API Keys, JWT.

Diadaptasi dari:
- Dify: Workspace isolation, member management, API key rotation
- Aeryn v61.5: JWT auth, rate limiting, SSO
"""

import os
import json
import hashlib
import secrets
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Permission constants."""
    CHAT_READ = "chat:read"
    CHAT_WRITE = "chat:write"
    BRAIN_READ = "brain:read"
    BRAIN_WRITE = "brain:write"
    AGENT_READ = "agent:read"
    AGENT_WRITE = "agent:write"
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_WRITE = "workflow:write"
    PLUGIN_READ = "plugin:read"
    PLUGIN_WRITE = "plugin:write"
    ANALYTICS_READ = "analytics:read"
    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    WORKSPACE_READ = "workspace:read"
    WORKSPACE_WRITE = "workspace:write"
    MEMBER_READ = "member:read"
    MEMBER_WRITE = "member:write"
    API_KEY_READ = "api_key:read"
    API_KEY_WRITE = "api_key:write"


class Role(Enum):
    """Workspace roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.OWNER: {
        Permission.CHAT_READ, Permission.CHAT_WRITE,
        Permission.BRAIN_READ, Permission.BRAIN_WRITE,
        Permission.AGENT_READ, Permission.AGENT_WRITE,
        Permission.WORKFLOW_READ, Permission.WORKFLOW_WRITE,
        Permission.PLUGIN_READ, Permission.PLUGIN_WRITE,
        Permission.ANALYTICS_READ,
        Permission.BILLING_READ, Permission.BILLING_WRITE,
        Permission.ADMIN_READ, Permission.ADMIN_WRITE,
        Permission.WORKSPACE_READ, Permission.WORKSPACE_WRITE,
        Permission.MEMBER_READ, Permission.MEMBER_WRITE,
        Permission.API_KEY_READ, Permission.API_KEY_WRITE,
    },
    Role.ADMIN: {
        Permission.CHAT_READ, Permission.CHAT_WRITE,
        Permission.BRAIN_READ, Permission.BRAIN_WRITE,
        Permission.AGENT_READ, Permission.AGENT_WRITE,
        Permission.WORKFLOW_READ, Permission.WORKFLOW_WRITE,
        Permission.PLUGIN_READ, Permission.PLUGIN_WRITE,
        Permission.ANALYTICS_READ,
        Permission.BILLING_READ,
        Permission.WORKSPACE_READ,
        Permission.MEMBER_READ, Permission.MEMBER_WRITE,
        Permission.API_KEY_READ, Permission.API_KEY_WRITE,
    },
    Role.MEMBER: {
        Permission.CHAT_READ, Permission.CHAT_WRITE,
        Permission.BRAIN_READ, Permission.BRAIN_WRITE,
        Permission.AGENT_READ, Permission.AGENT_WRITE,
        Permission.WORKFLOW_READ, Permission.WORKFLOW_WRITE,
        Permission.PLUGIN_READ,
        Permission.ANALYTICS_READ,
        Permission.BILLING_READ,
        Permission.WORKSPACE_READ,
        Permission.MEMBER_READ,
        Permission.API_KEY_READ,
    },
    Role.VIEWER: {
        Permission.CHAT_READ,
        Permission.BRAIN_READ,
        Permission.AGENT_READ,
        Permission.WORKFLOW_READ,
        Permission.ANALYTICS_READ,
        Permission.WORKSPACE_READ,
        Permission.MEMBER_READ,
    },
}


@dataclass
class WorkspaceMember:
    """A member of a workspace."""
    user_id: str
    workspace_id: str
    role: Role
    joined_at: datetime = field(default_factory=datetime.utcnow)
    invited_by: Optional[str] = None
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if member has a permission."""
        return permission in ROLE_PERMISSIONS.get(self.role, set())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "role": self.role.value,
            "joined_at": self.joined_at.isoformat(),
            "invited_by": self.invited_by,
        }


@dataclass
class Workspace:
    """A workspace — isolated environment for a team."""
    id: str
    name: str
    description: str = ""
    owner_id: str = ""
    members: List[WorkspaceMember] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_member(self, user_id: str, role: Role, invited_by: str = None):
        """Add a member to the workspace."""
        # Check if already a member
        if any(m.user_id == user_id for m in self.members):
            raise ValueError(f"User {user_id} is already a member")
        
        member = WorkspaceMember(
            user_id=user_id,
            workspace_id=self.id,
            role=role,
            invited_by=invited_by,
        )
        self.members.append(member)
        self.updated_at = datetime.utcnow()
    
    def remove_member(self, user_id: str):
        """Remove a member from the workspace."""
        self.members = [m for m in self.members if m.user_id != user_id]
        self.updated_at = datetime.utcnow()
    
    def get_member(self, user_id: str) -> Optional[WorkspaceMember]:
        """Get a member by user ID."""
        return next((m for m in self.members if m.user_id == user_id), None)
    
    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if a user has a permission in this workspace."""
        member = self.get_member(user_id)
        if not member:
            return False
        return member.has_permission(permission)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "members": [m.to_dict() for m in self.members],
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WorkspaceManager:
    """Manages workspaces — diadaptasi dari Dify."""
    
    def __init__(self, storage_path: str = "./workspaces"):
        self._workspaces: Dict[str, Workspace] = {}
        self._user_workspaces: Dict[str, List[str]] = {}
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
    
    def create_workspace(
        self,
        name: str,
        owner_id: str,
        description: str = "",
    ) -> Workspace:
        """Create a new workspace."""
        workspace_id = f"ws_{secrets.token_hex(8)}"
        
        workspace = Workspace(
            id=workspace_id,
            name=name,
            description=description,
            owner_id=owner_id,
        )
        
        # Add owner as member
        workspace.add_member(owner_id, Role.OWNER)
        
        self._workspaces[workspace_id] = workspace
        
        # Track user's workspaces
        if owner_id not in self._user_workspaces:
            self._user_workspaces[owner_id] = []
        self._user_workspaces[owner_id].append(workspace_id)
        
        logger.info(f"Created workspace: {workspace_id} for user: {owner_id}")
        return workspace
    
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get a workspace by ID."""
        return self._workspaces.get(workspace_id)
    
    def delete_workspace(self, workspace_id: str, user_id: str):
        """Delete a workspace."""
        workspace = self._workspaces.get(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        if workspace.owner_id != user_id:
            raise PermissionError("Only owner can delete workspace")
        
        # Remove from user's workspaces
        for member in workspace.members:
            if member.user_id in self._user_workspaces:
                self._user_workspaces[member.user_id] = [
                    wid for wid in self._user_workspaces[member.user_id]
                    if wid != workspace_id
                ]
        
        del self._workspaces[workspace_id]
        logger.info(f"Deleted workspace: {workspace_id}")
    
    def get_user_workspaces(self, user_id: str) -> List[Workspace]:
        """Get all workspaces for a user."""
        workspace_ids = self._user_workspaces.get(user_id, [])
        return [self._workspaces[wid] for wid in workspace_ids if wid in self._workspaces]
    
    def invite_member(
        self,
        workspace_id: str,
        inviter_id: str,
        invitee_id: str,
        role: Role = Role.MEMBER,
    ):
        """Invite a member to a workspace."""
        workspace = self._workspaces.get(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        # Check inviter has permission
        if not workspace.check_permission(inviter_id, Permission.MEMBER_WRITE):
            raise PermissionError("No permission to invite members")
        
        workspace.add_member(invitee_id, role, invited_by=inviter_id)
        
        # Track user's workspaces
        if invitee_id not in self._user_workspaces:
            self._user_workspaces[invitee_id] = []
        self._user_workspaces[invitee_id].append(workspace_id)
    
    def remove_member(self, workspace_id: str, remover_id: str, target_id: str):
        """Remove a member from a workspace."""
        workspace = self._workspaces.get(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        # Check remover has permission
        if not workspace.check_permission(remover_id, Permission.MEMBER_WRITE):
            raise PermissionError("No permission to remove members")
        
        # Cannot remove owner
        if workspace.owner_id == target_id:
            raise PermissionError("Cannot remove workspace owner")
        
        workspace.remove_member(target_id)
        
        # Update user's workspaces
        if target_id in self._user_workspaces:
            self._user_workspaces[target_id] = [
                wid for wid in self._user_workspaces[target_id]
                if wid != workspace_id
            ]
    
    def update_member_role(
        self,
        workspace_id: str,
        updater_id: str,
        target_id: str,
        new_role: Role,
    ):
        """Update a member's role."""
        workspace = self._workspaces.get(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        # Check updater has permission
        if not workspace.check_permission(updater_id, Permission.MEMBER_WRITE):
            raise PermissionError("No permission to update roles")
        
        # Cannot change owner role
        if workspace.owner_id == target_id:
            raise PermissionError("Cannot change owner role")
        
        member = workspace.get_member(target_id)
        if not member:
            raise ValueError(f"Member not found: {target_id}")
        
        member.role = new_role
        workspace.updated_at = datetime.utcnow()
    
    def check_access(self, workspace_id: str, user_id: str, permission: Permission) -> bool:
        """Check if a user has access to a workspace with a specific permission."""
        workspace = self._workspaces.get(workspace_id)
        if not workspace:
            return False
        return workspace.check_permission(user_id, permission)
    
    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List all workspaces."""
        return [w.to_dict() for w in self._workspaces.values()]


@dataclass
class APIKey:
    """API key for workspace access."""
    id: str
    workspace_id: str
    user_id: str
    name: str
    key_hash: str
    key_prefix: str
    scopes: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "name": self.name,
            "key_prefix": self.key_prefix,
            "scopes": self.scopes,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "is_active": self.is_active,
        }


class APIKeyManager:
    """Manages API keys — diadaptasi dari Dify."""
    
    def __init__(self):
        self._keys: Dict[str, APIKey] = {}
        self._key_index: Dict[str, str] = {}  # key_hash -> key_id
    
    def create_api_key(
        self,
        workspace_id: str,
        user_id: str,
        name: str,
        scopes: List[str] = None,
        expires_in_days: int = 365,
    ) -> Tuple[APIKey, str]:
        """Create a new API key. Returns (key, plain_text)."""
        # Generate key
        plain_key = f"sk-{secrets.token_hex(32)}"
        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
        key_prefix = plain_key[:12]
        
        api_key = APIKey(
            id=f"key_{secrets.token_hex(8)}",
            workspace_id=workspace_id,
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes=scopes or ["*"],
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
        )
        
        self._keys[api_key.id] = api_key
        self._key_index[key_hash] = api_key.id
        
        logger.info(f"Created API key: {api_key.id} for workspace: {workspace_id}")
        return api_key, plain_key
    
    def validate_api_key(self, plain_key: str) -> Optional[APIKey]:
        """Validate an API key."""
        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
        key_id = self._key_index.get(key_hash)
        
        if not key_id:
            return None
        
        api_key = self._keys.get(key_id)
        if not api_key or not api_key.is_active:
            return None
        
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None
        
        # Update last used
        api_key.last_used_at = datetime.utcnow()
        
        return api_key
    
    def revoke_api_key(self, key_id: str, user_id: str):
        """Revoke an API key."""
        api_key = self._keys.get(key_id)
        if not api_key:
            raise ValueError(f"API key not found: {key_id}")
        
        if api_key.user_id != user_id:
            raise PermissionError("Cannot revoke another user's key")
        
        api_key.is_active = False
        del self._key_index[api_key.key_hash]
        
        logger.info(f"Revoked API key: {key_id}")
    
    def list_api_keys(self, workspace_id: str, user_id: str) -> List[Dict[str, Any]]:
        """List API keys for a workspace."""
        return [
            k.to_dict()
            for k in self._keys.values()
            if k.workspace_id == workspace_id and k.user_id == user_id
        ]
    
    def cleanup_expired(self):
        """Remove expired keys."""
        now = datetime.utcnow()
        expired = [
            k.id for k in self._keys.values()
            if k.expires_at and k.expires_at < now
        ]
        for key_id in expired:
            key = self._keys.pop(key_id, None)
            if key:
                self._key_index.pop(key.key_hash, None)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired API keys")


class JWTManager:
    """JWT token management — diadaptasi dari Aeryn v61.5."""
    
    def __init__(self, secret: str = None, algorithm: str = "HS256"):
        self._secret = secret or os.environ.get("AERYN_JWT_SECRET", "dev-secret-change-in-production")
        self._algorithm = algorithm
    
    def generate_token(
        self,
        user_id: str,
        workspace_id: str = None,
        role: str = None,
        expires_hours: int = 24,
    ) -> str:
        """Generate a JWT token."""
        try:
            import jwt
        except ImportError:
            # Fallback without PyJWT
            return self._generate_simple_token(user_id, workspace_id, role, expires_hours)
        
        payload = {
            "sub": user_id,
            "wid": workspace_id,
            "role": role,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=expires_hours),
        }
        
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a JWT token."""
        try:
            import jwt
        except ImportError:
            return self._validate_simple_token(token)
        
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def _generate_simple_token(self, user_id: str, workspace_id: str, role: str, expires_hours: int) -> str:
        """Simple token without PyJWT."""
        import base64
        
        payload = {
            "sub": user_id,
            "wid": workspace_id,
            "role": role,
            "exp": (datetime.utcnow() + timedelta(hours=expires_hours)).timestamp(),
        }
        
        payload_json = json.dumps(payload)
        payload_b64 = base64.b64encode(payload_json.encode()).decode()
        
        signature = hashlib.sha256(f"{payload_b64}{self._secret}".encode()).hexdigest()
        
        return f"{payload_b64}.{signature}"
    
    def _validate_simple_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate simple token without PyJWT."""
        import base64
        
        try:
            parts = token.split(".")
            if len(parts) != 2:
                return None
            
            payload_b64, signature = parts
            
            # Verify signature
            expected_sig = hashlib.sha256(f"{payload_b64}{self._secret}".encode()).hexdigest()
            if signature != expected_sig:
                return None
            
            # Decode payload
            payload_json = base64.b64decode(payload_b64).decode()
            payload = json.loads(payload_json)
            
            # Check expiration
            if payload.get("exp", 0) < datetime.utcnow().timestamp():
                return None
            
            return payload
        except Exception:
            return None


class AuthManager:
    """Main authentication manager."""
    
    def __init__(self):
        self.workspace_manager = WorkspaceManager()
        self.api_key_manager = APIKeyManager()
        self.jwt_manager = JWTManager()
    
    def authenticate(self, token: str = None, api_key: str = None) -> Optional[Dict[str, Any]]:
        """Authenticate via JWT token or API key."""
        if token:
            return self.jwt_manager.validate_token(token)
        
        if api_key:
            key = self.api_key_manager.validate_api_key(api_key)
            if key:
                return {
                    "sub": key.user_id,
                    "wid": key.workspace_id,
                    "scopes": key.scopes,
                }
        
        return None
    
    def authorize(
        self,
        user_id: str,
        workspace_id: str,
        permission: Permission,
    ) -> bool:
        """Check if user is authorized for an action."""
        return self.workspace_manager.check_access(workspace_id, user_id, permission)
    
    def require_auth(self, token: str = None, api_key: str = None) -> Dict[str, Any]:
        """Require authentication, raise if invalid."""
        auth = self.authenticate(token, api_key)
        if not auth:
            raise PermissionError("Authentication required")
        return auth
    
    def require_permission(
        self,
        user_id: str,
        workspace_id: str,
        permission: Permission,
    ):
        """Require permission, raise if unauthorized."""
        if not self.authorize(user_id, workspace_id, permission):
            raise PermissionError(f"Permission denied: {permission.value}")
