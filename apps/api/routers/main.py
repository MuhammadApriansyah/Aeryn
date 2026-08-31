#!/usr/bin/env python3
"""Aeryn API V61.0 — Modular FastAPI Application."""

import os, sys, json, asyncio, time

# Ensure project root is on sys.path (4 levels up: apps/api/routers/main.py -> /home/sen/aeryn-core-agent)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, _PROJECT_ROOT)
if not os.path.exists(os.path.join(_PROJECT_ROOT, "aeryn_core")):
    # Fallback: try cwd
    sys.path.insert(0, os.getcwd())
import aeryn_core.utils.patch_sqlite  # noqa

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
from contextlib import asynccontextmanager

# Import shared state modules
from aeryn_core.utils.logger import info, warn, error, log_exception
from aeryn_core.utils.llm_client import get_mode_router
from aeryn_core.auth.rate_limiter import get_rate_limiter
from aeryn_core.utils.error_recovery import get_error_recovery
from aeryn_core.platform.realtime import get_emitter
from aeryn_core.platform.adaptive_gateway import get_gateway
from aeryn_core.observability.tracer import get_tracer

# Import routers
from apps.api.routers.chat import router as chat_router
from apps.api.routers.dashboard import router as dashboard_router
from apps.api.routers.notifications import router as notifications_router
from apps.api.routers.tools import router as tools_router
from apps.api.routers.auth import router as auth_router
from apps.api.routers.plugins import router as plugins_router
from apps.api.routers.workspaces import router as workspaces_router
from apps.api.routers.admin import router as admin_router
from apps.api.routers.phase4 import router as phase4_router
from apps.api.routers.shared import router as shared_router
from apps.api.routers.web_routes import router as web_routes_router

# --- Background tasks ---
async def broadcast_loop():
    """Broadcast dashboard data periodically."""
    while True:
        await asyncio.sleep(5)
        try:
            emitter = get_emitter()
            # Broadcast system health
            await emitter.broadcast("health_update", {"timestamp": time.time(), "status": "healthy"})
        except Exception as e:
            log_exception(e, "broadcast_loop")

# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage background tasks."""
    info("Aeryn API starting", version="61.0")
    task = asyncio.create_task(broadcast_loop())
    # Start Agent Daemon (autonomy loop)
    from aeryn_core.platform.agent_daemon import get_agent_daemon
    daemon = get_agent_daemon()
    await daemon.start()
    yield
    task.cancel()
    await daemon.stop()

# --- App ---
app = FastAPI(
    title="Aeryn API",
    description="Aeryn — Personal Assistant AI Agent SaaS for Developer and Enterprise",
    version="61.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Exception Handler ---
@app.middleware("http")
async def global_exception_handler(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        log_exception(e, context=f"{request.method} {request.url.path}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)},
        )

# --- Rate Limiting Middleware ---
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    from aeryn_core.auth.auth import get_auth, ROLE_PERMISSIONS
    try:
        if request.url.path == "/health":
            return await call_next(request)
        
        auth_header = request.headers.get("authorization", "")
        user_id = "anonymous"
        role = "free"
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            user = get_auth().validate_token(token)
            if user:
                user_id = user["id"]
                role = user.get("role", "free")
        
        limiter = get_rate_limiter()
        result = limiter.check(
            user_id=user_id,
            endpoint=request.url.path,
            method=request.method,
            ip=request.client.host if request.client else None,
            ua=request.headers.get("user-agent"),
        )
        
        if not result["allowed"]:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": result.get("retry_after", 60),
                    "limit": result["limit"],
                    "window": result["window"],
                },
                headers={"Retry-After": str(int(result.get("retry_after", 60)))},
            )
        
        return await call_next(request)
    except Exception as e:
        log_exception(e, "rate_limit_middleware")
        return await call_next(request)

# --- Request Tracking ---
@app.middleware("http")
async def track_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    # Track in memory for metrics
    try:
        from aeryn_core.utils.performance import get_optimizer
        get_optimizer().record_request(request.url.path, duration)
    except Exception:
        pass
    return response

# --- Include all routers ---
app.include_router(chat_router)        # Chat, Run, Compile, Digest, Search, Health
app.include_router(dashboard_router)   # SSE, WebSocket, Dashboard Stats
app.include_router(notifications_router)  # Notification endpoints
app.include_router(tools_router)       # Tools + Proactive
app.include_router(auth_router)         # Auth endpoints
app.include_router(plugins_router)     # Plugin marketplace
app.include_router(workspaces_router)   # Workspace endpoints
app.include_router(admin_router)        # Admin, SSO, SOC2
app.include_router(phase4_router)     # Phase 4 + Browser + Vector + Monitoring
app.include_router(shared_router)     # Shared DB, Vault, Reminders, Tasks
app.include_router(web_routes_router) # SPA, redirects, static

# --- API Versioning: /v1/ alias for all routers (backward-compatible) ---
# Mount all routers under /v1 prefix as well (old paths still work)
_V1 = APIRouter()
_V1.include_router(chat_router)
_V1.include_router(dashboard_router)
_V1.include_router(notifications_router)
_V1.include_router(tools_router)
_V1.include_router(auth_router)
_V1.include_router(plugins_router)
_V1.include_router(workspaces_router)
_V1.include_router(admin_router)
_V1.include_router(phase4_router)
_V1.include_router(shared_router)
app.include_router(_V1, prefix="/v1")

# --- Adaptive Gateway Endpoint ---
@app.get("/gateway/env")
async def gateway_env():
    """Expose detected environment + gateway status."""
    gw = get_gateway()
    return {
        "environment": gw.get_env_info(),
        "auth_enabled": gw.auth is not None,
        "rate_limiter_enabled": gw.rate_limiter is not None,
        "error_recovery_enabled": gw.error_recovery is not None,
        "circuit_breakers": {
            "chat": gw.get_circuit_breaker_state("chat"),
            "llm": gw.get_circuit_breaker_state("llm"),
        },
    }

# --- Agent Daemon Endpoints ---
@app.post("/daemon/tasks")
async def submit_task(request: Request):
    """Submit a task for autonomous execution."""
    from aeryn_core.platform.background_queue import get_task_queue
    body = await request.json()
    name = body.get("goal") or body.get("name") or "untitled"
    queue = get_task_queue()
    # Wrap as async no-op func (daemon executes via _tick)
    task_id = await queue.submit(name, lambda: None)
    return {"task_id": task_id, "status": "pending", "name": name}

@app.get("/daemon/tasks")
async def list_tasks():
    """List all daemon tasks."""
    from aeryn_core.platform.background_queue import get_task_queue
    queue = get_task_queue()
    return {"tasks": queue.get_all_tasks(), "pending": queue.get_pending_count()}

# --- Capability Bridge Endpoints (Hermes-style skills + memory tier) ---
@app.get("/capabilities/skills")
async def list_capabilities_skills():
    """List dynamically loaded skills (canonical, no conflict)."""
    import os
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.abspath(os.path.join(_here, "..", "..", ".."))
    skills_dir = os.path.join(_root, "aeryn_core", "skills")
    skills = []
    if os.path.isdir(skills_dir):
        for name in os.listdir(skills_dir):
            full = os.path.join(skills_dir, name)
            if os.path.isdir(full) and os.path.exists(os.path.join(full, "SKILL.md")):
                skills.append(name)
    return {"skills": skills, "count": len(skills), "dir": skills_dir}

@app.get("/memory/recall")
async def memory_recall(q: str = "", k: int = 3):
    """Semantic memory recall for context."""
    from aeryn_core.platform.capability_bridge import get_memory_bridge
    bridge = get_memory_bridge()
    results = bridge.recall_context(q, k=k)
    return {"query": q, "results": results, "count": len(results)}

# --- Observability Endpoints ---
@app.get("/observability/traces")
async def list_traces(limit: int = 10):
    """List recent traces."""
    tracer = get_tracer()
    return {"traces": tracer.get_recent_traces(limit=limit)}

@app.get("/observability/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Get trace by ID."""
    tracer = get_tracer()
    trace = tracer.get_trace(trace_id)
    if not trace:
        return {"error": "Trace not found"}
    return trace.to_dict()

@app.get("/observability/stats")
async def observability_stats():
    """Get observability statistics."""
    tracer = get_tracer()
    return tracer.get_stats()

# --- Plugin Registry Endpoints ---
@app.get("/plugins")
async def list_plugins():
    """List all registered plugins/tools."""
    from aeryn_core.platform.plugin_registry import get_registry
    reg = get_registry()
    return {"tools": reg.list_tools(), **reg.get_stats()}

@app.get("/plugins/discover")
async def discover_plugins(q: str = "", limit: int = 5):
    """Discover plugins matching a query."""
    from aeryn_core.platform.plugin_registry import get_registry
    reg = get_registry()
    return {"query": q, "tools": reg.discover_tools(q, limit=limit)}

@app.get("/plugins/{name}")
async def get_plugin(name: str):
    """Get plugin details."""
    from aeryn_core.platform.plugin_registry import get_registry
    reg = get_registry()
    tool = reg.get(name)
    if not tool:
        return {"error": "Plugin not found"}
    return tool.to_dict()

# --- Health Check ---
@app.get("/health")
async def health():
    """Health check endpoint."""
    import psutil
    process = psutil.Process()
    mem_mb = process.memory_info().rss / 1024 / 1024
    return {"status": "healthy", "memory_mb": round(mem_mb, 1), "version": "61.0"}

# --- Main Entry ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("AERYN_HOST", "127.0.0.1"),
        port=int(os.getenv("AERYN_PORT", "3010")),
        log_level="info",
    )
