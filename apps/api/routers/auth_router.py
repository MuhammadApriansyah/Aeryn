"""Auth Router — API key management + identity endpoints."""

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class IssueKeyRequest(BaseModel):
    user_id: str
    allowed_tools: Optional[List[str]] = None
    role: str = "user"


@router.post("/issue-key")
async def issue_key(req: IssueKeyRequest):
    """Issue a new API key (raw key shown only once)."""
    from aeryn_core.auth.identity import get_auth_manager
    manager = get_auth_manager()
    api_key = manager.issue_key(req.user_id, req.allowed_tools, req.role)
    return {"user_id": req.user_id, "api_key": api_key, "note": "Store this key securely — shown only once."}


@router.post("/validate")
async def validate_key(api_key: str = ""):
    """Validate an API key."""
    from aeryn_core.auth.identity import get_auth_manager
    manager = get_auth_manager()
    identity = manager.validate_key(api_key)
    if not identity:
        return {"valid": False}
    return {"valid": True, "identity": identity.to_dict()}


@router.get("/identity/{user_id}")
async def get_identity(user_id: str):
    """Get identity (without key) for a user."""
    from aeryn_core.auth.identity import get_auth_manager
    manager = get_auth_manager()
    identity = manager.get_identity(user_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    return identity.to_dict()


@router.get("/tool-permission")
async def check_permission(tool_name: str, user_id: str = "default"):
    """Check if a user is allowed to use a tool."""
    from aeryn_core.auth.identity import get_auth_manager
    manager = get_auth_manager()
    identity = manager.get_identity(user_id)
    if not identity:
        return {"allowed": False, "reason": "no identity"}
    allowed = manager.check_tool_permission(identity, tool_name)
    return {"tool": tool_name, "allowed": allowed, "user_id": user_id}


@router.delete("/revoke/{user_id}")
async def revoke_key(user_id: str):
    """Revoke a user's API key."""
    from aeryn_core.auth.identity import get_auth_manager
    manager = get_auth_manager()
    manager.revoke_key(user_id)
    return {"status": "revoked", "user_id": user_id}