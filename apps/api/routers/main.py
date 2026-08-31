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
from fastapi.staticfiles import StaticFiles
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

# PostgreSQL Memory Plugin (optional)
try:
    from plugins.postgres_memory.api import router as pg_memory_router
    app.include_router(pg_memory_router, prefix="/v1")
    import logging
    logging.info("PostgreSQL Memory Plugin loaded at /v1/postgres-memory/*")
except ImportError as e:
    import logging
    logging.warning(f"PostgreSQL Memory Plugin not loaded: {e}")

# Messaging Gateway (optional)
try:
    from plugins.messaging_gateway.api import router as messaging_router
    app.include_router(messaging_router, prefix="/v1")
    import logging
    logging.info("Messaging Gateway loaded at /v1/messaging/*")
except ImportError as e:
    import logging
    logging.warning(f"Messaging Gateway not loaded: {e}")

# Experience Transfer (optional)
try:
    from plugins.experience_transfer.api import router as experience_router
    app.include_router(experience_router, prefix="/v1")
    import logging
    logging.info("Experience Transfer loaded at /v1/experience/*")
except ImportError as e:
    import logging
    logging.warning(f"Experience Transfer not loaded: {e}")


# Mount static files for dashboard
import os as _os
_STATIC_DIR = _os.path.join(_os.getcwd(), "apps", "web", "static")
if _os.path.isdir(_STATIC_DIR):
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

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

# --- Self-Improvement Endpoints ---
@app.get("/self-improvement/stats")
async def self_improvement_stats():
    """Get self-improvement statistics."""
    from aeryn_core.self_improvement.engine import get_self_improvement
    si = get_self_improvement()
    return si.generate_improvement_report()

@app.get("/self-improvement/patterns")
async def self_improvement_patterns(pattern_type: str = "tool_selection", min_rate: float = 0.7):
    """Get reliable or problematic patterns."""
    from aeryn_core.self_improvement.engine import get_self_improvement
    si = get_self_improvement()
    if min_rate >= 0.5:
        return {"patterns": si.get_reliable_patterns(pattern_type, min_rate)}
    return {"patterns": si.get_problematic_patterns(pattern_type, min_rate)}

@app.post("/self-improvement/adapt")
async def trigger_adaptation():
    """Trigger self-improvement adaptation cycle."""
    from aeryn_core.self_improvement.engine import get_self_improvement
    si = get_self_improvement()
    result = si.adapt()
    return result

# --- Tool Registry Endpoints (from plugin_registry, not plugins_router) ---
# Note: /plugins is handled by plugins_router from plugins.py
# We prefix these to avoid operation ID collision

@app.get("/plugins/discover")
async def discover_plugins(q: str = "", limit: int = 5):
    """Discover tools matching a query."""
    from aeryn_core.platform.plugin_registry import get_registry
    reg = get_registry()
    return {"query": q, "tools": reg.discover_tools(q, limit=limit)}

# --- Division Management Endpoints (D8) ---
@app.get("/divisions")
async def list_divisions():
    """List all 5 Aeryn divisions."""
    from aeryn_core.orchestration.crew_orchestrator import get_division_manager
    dm = get_division_manager()
    return {"divisions": dm.list_divisions(), **dm.get_status()}

@app.post("/divisions/{name}/execute")
async def execute_division(name: str, request: Request):
    """Execute tasks on a division. Accepts {tasks: [...]} or {goal: "..."} formats."""
    from aeryn_core.orchestration.crew_orchestrator import get_division_manager
    body = await request.json()
    
    # Normalize: accept both {tasks: [...]} and {goal: "..."}
    if "tasks" in body:
        tasks = body["tasks"]
    elif "goal" in body:
        tasks = [{"goal": body["goal"], "model": body.get("model", "default"), "timeout": body.get("timeout", 30)}]
    else:
        tasks = [{"goal": str(body), "model": "default", "timeout": 30}]
    
    dm = get_division_manager()
    result = await dm.execute_division(name, tasks)
    return {"division": name, **result}

# --- Connector Management Endpoints (D9) ---
@app.get("/connectors")
async def list_connectors():
    """List all registered connectors."""
    from aeryn_core.connectors.vault_connector import get_connector_manager
    cm = get_connector_manager()
    return {"connectors": cm.list_connectors()}

@app.post("/connectors/{name}/sync")
async def sync_connector(name: str):
    """Sync a connector."""
    from aeryn_core.connectors.vault_connector import get_connector_manager
    cm = get_connector_manager()
    return cm.sync_one(name)

@app.post("/connectors/sync-all")
async def sync_all_connectors():
    """Sync all connectors."""
    from aeryn_core.connectors.vault_connector import get_connector_manager
    cm = get_connector_manager()
    return cm.sync_all()

# --- Workflow Endpoints (D11) ---
@app.post("/workflows")
async def create_workflow(request: Request):
    """Create a new workflow."""
    from aeryn_core.workflow.phase_workflow import create_workflow
    body = await request.json()
    name = body.get("name", "saas")
    idea = body.get("idea", "")
    wf = create_workflow(name, idea)
    return wf.to_dict()

@app.get("/workflows")
async def list_workflows():
    """List all workflows."""
    from aeryn_core.workflow.phase_workflow import list_workflows
    return {"workflows": list_workflows()}

@app.get("/workflows/{wf_id}")
async def get_workflow(wf_id: str):
    """Get workflow status."""
    from aeryn_core.workflow.phase_workflow import get_workflow
    wf = get_workflow(wf_id)
    if not wf:
        return {"error": "Workflow not found"}
    return wf.to_dict()

@app.post("/workflows/{wf_id}/step")
async def execute_workflow_step(wf_id: str):
    """Execute next step in workflow."""
    from aeryn_core.workflow.phase_workflow import get_workflow
    wf = get_workflow(wf_id)
    if not wf:
        return {"error": "Workflow not found"}
    return wf.execute_next()

@app.post("/workflows/{wf_id}/approve")
async def approve_checkpoint(wf_id: str, request: Request):
    """Approve a checkpoint."""
    from aeryn_core.workflow.phase_workflow import get_workflow
    body = await request.json()
    step_name = body.get("step_name", "")
    option = body.get("option", "approve")
    wf = get_workflow(wf_id)
    if not wf:
        return {"error": "Workflow not found"}
    wf.approve_checkpoint(step_name, option)
    return {"status": "approved", "workflow": wf.to_dict()}

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
