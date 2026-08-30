"""V61.0 — Workspaces router for Aeryn API."""
from fastapi import APIRouter, Header
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from pydantic import BaseModel
from aeryn_core.platform.workspace_manager import get_workspace_manager

router = APIRouter()

# ── Workspace Endpoints ───────────────────────

class CreateWorkspaceRequest(BaseModel):
    name: str
    description: str = None

class UpdateWorkspaceRequest(BaseModel):
    name: str = None
    description: str = None

class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "member"

class CreateInviteRequest(BaseModel):
    email: str
    role: str = "member"

@router.post("/workspaces")
async def create_workspace(req: CreateWorkspaceRequest, authorization: str = Header(None)):
    """Create a new workspace."""
    auth = get_auth()
    wm = get_workspace_manager()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    result = wm.create_workspace(req.name, user["id"], req.description)
    if not result:
        return {"error": "Failed to create workspace"}
    return {"status": "ok", "workspace": result}

@router.get("/workspaces")
async def list_workspaces(authorization: str = Header(None)):
    """List user's workspaces."""
    auth = get_auth()
    wm = get_workspace_manager()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    return {"workspaces": wm.list_user_workspaces(user["id"])}

@router.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: str, authorization: str = Header(None)):
    """Get workspace details."""
    auth = get_auth()
    wm = get_workspace_manager()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    workspace = wm.get_workspace(workspace_id)
    if not workspace:
        return {"error": "Workspace not found"}
    
    # Check membership
    role = wm.get_member_role(workspace_id, user["id"])
    if not role:
        return {"error": "Access denied"}
    
    return workspace

@router.put("/workspaces/{workspace_id}")
async def update_workspace(workspace_id: str, req: UpdateWorkspaceRequest, authorization: str = Header(None)):
    """Update workspace."""
    auth = get_auth()
    wm = get_workspace_manager()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    # Check admin role
    role = wm.get_member_role(workspace_id, user["id"])
    if role != "admin":
        return {"error": "Admin access required"}
    
    wm.update_workspace(workspace_id, req.name, req.description)
    return {"status": "ok"}

@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(workspace_id: str, authorization: str = Header(None)):
    """Delete workspace."""
    auth = get_auth()
    wm = get_workspace_manager()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    # Check owner role
    role = wm.get_member_role(workspace_id, user["id"])
    if role != "admin":
        return {"error": "Admin access required"}
    
    wm.delete_workspace(workspace_id)
    return {"status": "ok"}

@router.get("/workspaces/{workspace_id}/members")
async def list_workspace_members(workspace_id: str, authorization: str = Header(None)):
    """List workspace members."""
    auth = get_auth()
    wm = get_workspace_manager()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    # Check membership
    role = wm.get_member_role(workspace_id, user["id"])
    if not role:
        return {"error": "Access denied"}
    
    return {"members": wm.list_members(workspace_id)}

@router.post("/workspaces/{workspace_id}/members")
async def add_workspace_member(workspace_id: str, req: AddMemberRequest, authorization: str = Header(None)):
    """Add member to workspace."""
    auth = get_auth()
    wm = get_workspace_manager()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    # Check admin role
    role = wm.get_member_role(workspace_id, user["id"])
    if role != "admin":
        return {"error": "Admin access required"}
    
    wm.add_member(workspace_id, req.user_id, req.role)
    return {"status": "ok"}

@router.delete("/workspaces/{workspace_id}/members/{user_id_to_remove}")
async def remove_workspace_member(workspace_id: str, user_id_to_remove: str, authorization: str = Header(None)):
    """Remove member from workspace."""
    auth = get_auth()
    wm = get_workspace_manager()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    # Check admin role
    role = wm.get_member_role(workspace_id, user["id"])
    if role != "admin":
        return {"error": "Admin access required"}
    
    wm.remove_member(workspace_id, user_id_to_remove)
    return {"status": "ok"}

@router.post("/workspaces/{workspace_id}/invites")
async def create_workspace_invite(workspace_id: str, req: CreateInviteRequest, authorization: str = Header(None)):
    """Create workspace invite."""
    auth = get_auth()
    wm = get_workspace_manager()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    # Check admin role
    role = wm.get_member_role(workspace_id, user["id"])
    if role != "admin":
        return {"error": "Admin access required"}
    
    result = wm.create_invite(workspace_id, req.email, user["id"], req.role)
    return {"status": "ok", "invite": result}

@router.post("/workspaces/invites/{token}/accept")
async def accept_workspace_invite(token: str, authorization: str = Header(None)):
    """Accept workspace invite."""
    auth = get_auth()
    wm = get_workspace_manager()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    result = wm.accept_invite(token, user["id"])
    if not result:
        return {"error": "Invalid or expired invite"}
    return {"status": "ok", "workspace": result}

# ── SSO Endpoints ─────────────────────────────
