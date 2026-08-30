"""V61.0 — Auth router for Aeryn API."""
from fastapi import APIRouter, Header
import os, sys, time, json, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from pydantic import BaseModel
from aeryn_core.auth.auth import get_auth, ROLE_PERMISSIONS
from aeryn_core.auth.api_keys import get_api_key_manager
from aeryn_core.auth.email_verification import get_email_verification, get_password_reset
from aeryn_core.safety.secrets_runtime import get_secrets_manager
from aeryn_core.utils.data_encryption import get_encryption
from aeryn_core.auth.sso_manager import get_sso_manager
from aeryn_core.billing.usage_metering import get_usage_metering
from aeryn_core.billing.billing import get_billing, PRICING, PLANS
from aeryn_core.auth.rate_limiter import get_rate_limiter
from aeryn_core.utils.logger import warn, log_exception

router = APIRouter()

class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str = None

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenRequest(BaseModel):
    token: str

class ApiKeyRequest(BaseModel):
    name: str = "default"
    scopes: list = None
    expires_days: int = 365

@router.post("/auth/register")
async def auth_register(req: RegisterRequest):
    """Register a new user."""
    auth = get_auth()
    user = auth.create_user(req.email, req.password, req.display_name)
    if not user:
        return {"error": "User already exists or invalid data"}
    return {"status": "ok", "user": user}

@router.post("/auth/login")
async def auth_login(req: LoginRequest):
    """Login and get session token."""
    auth = get_auth()
    user = auth.authenticate(req.email, req.password)
    if not user:
        return {"error": "Invalid credentials"}
    token = auth.generate_token(user["id"])
    return {"status": "ok", "token": token, "user": user}

@router.post("/auth/validate")
async def auth_validate(req: TokenRequest):
    """Validate a session token."""
    auth = get_auth()
    user = auth.validate_token(req.token)
    if not user:
        return {"error": "Invalid or expired token"}
    return {"status": "ok", "user": user}

@router.post("/auth/api-keys")
async def auth_create_api_key(req: ApiKeyRequest, authorization: str = Header(None)):
    """Create an API key for authenticated user."""
    auth = get_auth()
    # Get user from token in Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required. Format: Bearer <token>"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    api_key = auth.generate_api_key(user["id"], req.name, req.scopes, req.expires_days)
    return {"status": "ok", "api_key": api_key}

# ── Billing Endpoints ─────────────────────────

class TrackUsageRequest(BaseModel):
    event_type: str
    endpoint: str = None
    tokens_input: int = 0
    tokens_output: int = 0

class CreateChargeRequest(BaseModel):
    amount: float
    description: str = ""

@router.post("/billing/track")
async def billing_track(req: TrackUsageRequest, authorization: str = Header(None)):
    """Track usage and calculate cost automatically."""
    auth = get_auth()
    billing = get_billing()
    metering = get_usage_metering()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    # Calculate cost
    cost = billing.calculate_cost(req.event_type, req.tokens_input, req.tokens_output)
    
    # Track event
    metering.track(user["id"], req.event_type, req.endpoint, 
                   req.tokens_input, req.tokens_output, cost)
    
    return {"status": "ok", "cost": cost}

@router.get("/billing/quota")
async def billing_quota(authorization: str = Header(None)):
    """Check quota status."""
    auth = get_auth()
    billing = get_billing()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    # Check quota (default plan: user's role)
    quota = billing.check_quota(user["id"], user.get("role", "free"))
    return quota

@router.get("/billing/pricing")
async def pricing():
    """Get pricing info."""
    return {"plans": PLANS, "usage_rates": PRICING}

@router.post("/billing/charge")
async def billing_charge(req: CreateChargeRequest, authorization: str = Header(None)):
    """Create a manual charge (admin only)."""
    auth = get_auth()
    billing = get_billing()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    if not auth.has_permission(user, "billing:write"):
        return {"error": "Permission denied"}
    
    result = billing.track_charge(user["id"], req.amount, req.description)
    return {"status": "ok", "charge": result}

# ── Webhook Endpoints ─────────────────────────

class RegisterWebhookRequest(BaseModel):
    url: str
    events: list = None
    secret: str = None

@router.post("/webhooks/register")
async def register_webhook(req: RegisterWebhookRequest, authorization: str = Header(None)):
    """Register a webhook endpoint."""
    auth = get_auth()
    ws = get_webhook_system()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    result = ws.register(user["id"], req.url, req.events, req.secret)
    return {"status": "ok", "webhook": result}

@router.delete("/webhooks/unregister")
async def unregister_webhook(webhook_id: str, authorization: str = Header(None)):
    """Unregister a webhook endpoint."""
    auth = get_auth()
    ws = get_webhook_system()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    ws.unregister(webhook_id)
    return {"status": "ok"}

@router.get("/webhooks")
async def list_webhooks(authorization: str = Header(None)):
    """List user's webhooks."""
    auth = get_auth()
    ws = get_webhook_system()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    return {"webhooks": ws.list_webhooks(user["id"])}

# ── Plugin Marketplace Endpoints ──────────────
