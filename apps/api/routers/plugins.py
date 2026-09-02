"""V61.0 — Plugins router for Aeryn API."""
from fastapi import APIRouter, Header
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from pydantic import BaseModel
from aeryn_core.platform.plugin_system import get_plugin_manager
from aeryn_core.safety.secrets_runtime import get_plugin_runtime
from aeryn_core.platform.plugin_marketplace import get_plugin_marketplace

router = APIRouter()

# ── Plugin Marketplace Endpoints ──────────────

@router.get("/plugins/installed")
async def list_installed():
    """List installed plugins."""
    pm = get_plugin_manager()
    return {"plugins": pm.list_plugins(), "count": len(pm.list_plugins())}

class PublishPluginRequest(BaseModel):
    name: str
    source_code: str
    display_name: str = None
    description: str = None
    version: str = "0.1.0"
    tags: list = None
    dependencies: list = None
    is_public: bool = True

class RatePluginRequest(BaseModel):
    plugin_id: str
    rating: float

@router.get("/plugins")
async def list_plugins(query: str = None, limit: int = 20, offset: int = 0):
    """List public plugins."""
    try:
        mp = get_plugin_marketplace()
        return {"plugins": mp.search(query=query, limit=limit, offset=offset)}
    except Exception as e:
        # Fallback: return plugin loader discoveries when Postgres unavailable
        from aeryn_core.plugins.loader import get_plugin_loader
        loader = get_plugin_loader()
        plugins = loader.discover()
        return {"plugins": plugins, "count": len(plugins), "fallback": True}

@router.post("/plugins/publish")
async def publish_plugin(req: PublishPluginRequest, authorization: str = Header(None)):
    """Publish a plugin."""
    auth = get_auth()
    mp = get_plugin_marketplace()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    result = mp.publish(
        user["id"], req.name, req.source_code,
        req.display_name, req.description, req.version,
        req.tags, req.dependencies, is_public=req.is_public
    )
    
    if not result:
        return {"error": "Failed to publish plugin"}
    return {"status": "ok", "plugin": result}

@router.get("/plugins/{plugin_id}")
async def get_plugin(plugin_id: str):
    """Get plugin details."""
    mp = get_plugin_marketplace()
    plugin = mp.get(plugin_id)
    if not plugin:
        return {"error": "Plugin not found"}
    return plugin

@router.post("/plugins/rate")
async def rate_plugin(req: RatePluginRequest, authorization: str = Header(None)):
    """Rate a plugin."""
    auth = get_auth()
    mp = get_plugin_marketplace()
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"error": "Authorization required"}
    token = authorization.replace("Bearer ", "")
    user = auth.validate_token(token)
    if not user:
        return {"error": "Invalid token"}
    
    success = mp.rate(req.plugin_id, user["id"], req.rating)
    return {"status": "ok" if success else "error"}

# ── Workspace Endpoints ───────────────────────
