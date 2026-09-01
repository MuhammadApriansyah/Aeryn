"""V61.0 — Admin endpoints router for Aeryn API."""
from fastapi import APIRouter, Header
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from pydantic import BaseModel
from aeryn_core.auth.auth import get_auth, ROLE_PERMISSIONS
from aeryn_core.billing.billing import get_billing, PRICING, PLANS
from aeryn_core.billing.usage_metering import get_usage_metering
from aeryn_core.auth.email_verification import get_email_verification, get_password_reset
from aeryn_core.safety.soc2_compliance import get_soc2_compliance
from aeryn_core.safety.secrets_runtime import get_secrets_manager, get_plugin_runtime
from aeryn_core.utils.data_encryption import get_encryption
from aeryn_core.platform.telegram_bot import get_telegram_bot
from aeryn_core.auth.sso_manager import get_sso_manager
from aeryn_core.utils.logger import warn

router = APIRouter()


# ── Admin Dashboard Endpoints ─────────────────

@router.get("/admin/users")
async def admin_list_users(authorization: str = Header(None)):
    """List all users (admin only)."""
    auth = get_auth()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    if not auth.has_permission(user, "admin:read"):
        return {"error": "Admin access required"}
    
    db = get_neon()
    return {"users": db.fetchall("SELECT id, email, display_name, role, is_active, created_at FROM users ORDER BY created_at DESC LIMIT 100")}

@router.get("/admin/stats")
async def admin_stats(authorization: str = Header(None)):
    """Get system stats (admin only)."""
    auth = get_auth()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    if not auth.has_permission(user, "admin:read"):
        return {"error": "Admin access required"}
    
    db = get_neon()
    
    user_count = db.fetchone("SELECT COUNT(*) as cnt FROM users")["cnt"]
    workspace_count = db.fetchone("SELECT COUNT(*) as cnt FROM workspaces")["cnt"]
    plugin_count = db.fetchone("SELECT COUNT(*) as cnt FROM plugins")["cnt"]
    
    return {
        "users": user_count,
        "workspaces": workspace_count,
        "plugins": plugin_count,
    }

# ── SOC2 Compliance Endpoints ─────────────────

@router.get("/admin/compliance/report")
async def compliance_report(authorization: str = Header(None)):
    """Generate SOC2 compliance report (admin only)."""
    auth = get_auth()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    if not auth.has_permission(user, "admin:read"):
        return {"error": "Admin access required"}
    
    soc2 = get_soc2_compliance()
    return soc2.generate_compliance_report()

@router.get("/admin/compliance/regions")
async def data_residency_regions(authorization: str = Header(None)):
    """Get available data residency regions."""
    soc2 = get_soc2_compliance()
    return {"regions": soc2.get_data_residency_regions()}

@router.post("/admin/compliance/cleanup")
async def run_data_cleanup(authorization: str = Header(None)):
    """Run data cleanup (admin only)."""
    auth = get_auth()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    if not auth.has_permission(user, "admin:write"):
        return {"error": "Admin access required"}
    
    soc2 = get_soc2_compliance()
    return soc2.run_data_cleanup()

# ── Email Verification & Password Reset ───────

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class VerifyEmailRequest(BaseModel):
    token: str

@router.post("/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    """Request password reset."""
    auth = get_auth()
    pw_reset = get_password_reset()
    
    # Find user by email
    user = auth.db.fetchone("SELECT id, email FROM users WHERE email = %s", (req.email,))
    if not user:
        # Don't reveal if email exists
        return {"status": "ok", "message": "If the email exists, a reset link has been sent"}
    
    # Create reset token
    token = pw_reset.create_token(user["id"], user["email"])
    
    # Send email
    pw_reset.send_reset_email(user["email"], token)
    
    return {"status": "ok", "message": "If the email exists, a reset link has been sent"}

@router.post("/auth/reset-password")
async def reset_password(req: ResetPasswordRequest):
    """Reset password with token."""
    pw_reset = get_password_reset()
    auth = get_auth()
    
    # Verify token
    result = pw_reset.verify_token(req.token)
    if not result:
        return {"error": "Invalid or expired token"}
    
    # Update password
    password_hash = auth._hash_password(req.new_password)
    auth.db.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, result["user_id"]))
    
    # Mark token as used
    pw_reset.mark_used(req.token)
    
    return {"status": "ok", "message": "Password has been reset"}

@router.post("/auth/verify-email")
async def verify_email(req: VerifyEmailRequest):
    """Verify email with token."""
    ev = get_email_verification()
    
    result = ev.verify_token(req.token)
    if not result:
        return {"error": "Invalid or expired token"}
    
    return {"status": "ok", "message": "Email verified"}

@router.post("/auth/resend-verification")
async def resend_verification(authorization: str = Header(None)):
    """Resend verification email."""
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    
    auth = get_auth()
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    ev = get_email_verification()
    
    # Check if already verified
    user_data = auth.db.fetchone("SELECT email_verified FROM users WHERE id = %s", (user["id"],))
    if user_data and user_data["email_verified"]:
        return {"error": "Email already verified"}
    
    # Create new token
    verify_token = ev.create_token(user["id"], user["email"])
    
    # Send email
    ev.send_verification_email(user["email"], verify_token)
    
    return {"status": "ok", "message": "Verification email sent"}

# ── Secrets & Plugins ─────────────────────────

@router.post("/secrets/set")
async def set_secret(user_id: str, name: str, value: str, description: str = None):
    """Store a secret."""
    sm = get_secrets_manager()
    sm.set(user_id, name, value, description)
    return {"status": "stored"}

@router.get("/secrets/get")
async def get_secret(user_id: str, name: str):
    """Get a secret."""
    sm = get_secrets_manager()
    value = sm.get(user_id, name)
    return {"value": value} if value else {"error": "Not found"}

@router.get("/secrets/list")
async def list_secrets(user_id: str):
    """List user's secrets."""
    sm = get_secrets_manager()
    return {"secrets": sm.list(user_id)}

@router.get("/plugins/list")
async def list_plugins():
    """List installed plugins."""
    rt = get_plugin_runtime()
    return {"plugins": rt.list_plugins()}

@router.post("/plugins/run")
async def run_plugin(body: dict = None):
    """Run a plugin. Accepts {plugin_name, action, params} or {name, input} formats."""
    if not body:
        body = {}
    
    # Normalize: support both formats
    actual_name = body.get("plugin_name") or body.get("name")
    actual_action = body.get("action") or "analyze_code"
    actual_params = body.get("params") or {}
    if "input" in body:
        actual_params["code"] = body["input"]
    
    if not actual_name:
        return {"error": "Plugin name required (plugin_name or name field)"}
    
    rt = get_plugin_runtime()
    result = rt.run_plugin(actual_name, actual_action, actual_params)
    # Normalize response: always include status
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    return {"status": "ok", **result}

# ── Phase 4 Endpoints ─────────────────────────

# ── SSO Endpoints ─────────────────────────────

@router.get("/auth/sso/google")
async def google_sso_url():
    """Get Google SSO URL."""
    sso = get_sso_manager()
    return {"url": sso.get_google_auth_url()}

@router.get("/auth/sso/github")
async def github_sso_url():
    """Get GitHub SSO URL."""
    sso = get_sso_manager()
    return {"url": sso.get_github_auth_url()}

@router.get("/auth/callback/google")
async def google_callback(code: str):
    """Google OAuth callback."""
    sso = get_sso_manager()
    result = await sso.handle_google_callback(code)
    if not result:
        return {"error": "Authentication failed"}
    return {"status": "ok", "user": result}

@router.get("/auth/callback/github")
async def github_callback(code: str):
    """GitHub OAuth callback."""
    sso = get_sso_manager()
    result = await sso.handle_github_callback(code)
    if not result:
        return {"error": "Authentication failed"}
    return {"status": "ok", "user": result}

@router.get("/auth/sso/accounts")
async def list_sso_accounts(authorization: str = Header(None)):
    """List user's linked SSO accounts."""
    auth = get_auth()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    sso = get_sso_manager()
    return {"accounts": sso.get_user_sso_accounts(user["id"])}

@router.delete("/auth/sso/{provider}")
async def unlink_sso_account(provider: str, authorization: str = Header(None)):
    """Unlink SSO account."""
    auth = get_auth()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    sso = get_sso_manager()
    sso.unlink_sso(user["id"], provider)
    return {"status": "ok"}
