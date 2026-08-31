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
from contextlib import asynccontextmanager

# Import shared state modules
from aeryn_core.utils.logger import info, warn, error, log_exception
from aeryn_core.utils.llm_client import get_mode_router
from aeryn_core.auth.rate_limiter import get_rate_limiter
from aeryn_core.utils.error_recovery import get_error_recovery
from aeryn_core.platform.realtime import get_emitter

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
            emitter.emit("health_update", {"timestamp": time.time(), "status": "healthy"})
        except Exception as e:
            log_exception(e, "broadcast_loop")

# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage background tasks."""
    info("Aeryn API starting", version="61.0")
    task = asyncio.create_task(broadcast_loop())
    yield
    task.cancel()

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
