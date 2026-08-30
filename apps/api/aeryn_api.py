#!/usr/bin/env python3
"""V61.0 — Aeryn Daemon :3010 — Full Feature Set."""

import os, sys, time, json, uuid, sqlite3, asyncio
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Patch sqlite3.connect for WAL + busy_timeout — must be before any other imports
import aeryn_core.utils.patch_sqlite  # noqa

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Header
from fastapi.responses import Response, FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from aeryn_core.safety.safety_engine import get_safety_engine, sanitize_output
from aeryn_core.utils.adapters import get_active_adapter, render_adapter_context
from aeryn_core.reasoning.reasoning_style import needs_research
from aeryn_core.memory.vault import AerynVault, VaultEntry, LAYER_WIKI
from aeryn_core.memory.social_memory import SocialMemory
from aeryn_core.memory.hybrid_search import get_search_engine
from aeryn_core.utils.persona_engine import load_persona
from aeryn_core.database.shared_db import get_shared_db
from aeryn_core.utils.config import ensure_dirs
from aeryn_core.reasoning.dream_synthesis import get_dream_synthesizer
from aeryn_core.memory.enhanced_memory import get_entity_extractor, get_preference_learner, get_cross_session_recall
from aeryn_core.safety.enhanced_guardrails import get_enhanced_guardrails
from aeryn_core.safety.enhanced_sandbox import get_enhanced_sandbox, SandboxLimits
from aeryn_core.platform.multi_agent import get_multi_agent_orchestrator, AgentRole, TaskPriority as AgentTaskPriority
from aeryn_core.memory.memory_decay import get_memory_decay_engine
from aeryn_core.memory.entity_resolution import get_entity_resolver
from aeryn_core.safety.owasp_security import get_owasp_security
from aeryn_core.platform.plugin_system import get_plugin_manager
from aeryn_core.reasoning.long_horizon import get_long_horizon_planner, TaskPriority
from aeryn_core.utils.llm_client import get_mode_router, AerynLLMClient
from aeryn_core.platform.notification_system import get_notification_manager, get_scheduler, Notification
from aeryn_core.database.semantic_indexer import get_semantic_indexer
from aeryn_core.utils.error_recovery import get_error_recovery, with_retry, with_fallback, with_circuit_breaker
from aeryn_core.platform.tool_runtime import get_tool_runtime
from aeryn_core.platform.background_queue import get_task_queue
from aeryn_core.reasoning.proactive_engine import get_proactive_engine
from aeryn_core.reasoning.proactive_v2 import get_daily_briefing, get_proactive_v2
from aeryn_core.platform.auto_task import get_auto_task
from aeryn_core.reasoning.context_manager import get_context_manager
from aeryn_core.auth.api_keys import get_api_key_manager
from aeryn_core.billing.usage_metering import get_usage_metering
from aeryn_core.billing.billing import get_billing, PRICING, PLANS
from aeryn_core.safety.secrets_runtime import get_secrets_manager, get_plugin_runtime
from aeryn_core.memory.temporal_memory import get_temporal_memory
from aeryn_core.reasoning.self_improvement import get_self_improvement_engine
from aeryn_core.platform.skill_crystallization import get_skill_crystallizer
from aeryn_core.platform.cloud_sync import get_cloud_sync
from aeryn_core.reasoning.constitutional_ai import get_constitutional_ai
from aeryn_core.reasoning.emotional_intelligence import get_emotional_intelligence
from aeryn_core.auth.auth import get_auth, ROLE_PERMISSIONS
from aeryn_core.adaptive import get_adaptive_system
from aeryn_core.auth.rate_limiter import get_rate_limiter
from aeryn_core.auth.email_verification import get_email_verification, get_password_reset
from aeryn_core.platform.webhook_system import get_webhook_system
from aeryn_core.platform.plugin_marketplace import get_plugin_marketplace
from aeryn_core.platform.workspace_manager import get_workspace_manager
from aeryn_core.auth.sso_manager import get_sso_manager
from aeryn_core.safety.soc2_compliance import get_soc2_compliance
from aeryn_core.platform.telegram_bot import get_telegram_bot
from aeryn_core.platform.email_agent import get_email_agent
from aeryn_core.platform.calendar_integration import get_calendar
from aeryn_core.platform.github_integration import get_github
from aeryn_core.utils.data_encryption import get_encryption

from aeryn_core.platform.realtime import get_emitter
from aeryn_core.utils.performance import get_optimizer, get_uptime
from aeryn_core.utils.logger import info, warn, error, log_exception

from contextlib import asynccontextmanager

@asynccontextmanager
async def app_lifespan(app):
    """Manage background tasks."""
    info("Aeryn API starting", version="41.0")
    task = asyncio.create_task(broadcast_loop())
    scheduler_task = asyncio.create_task(get_scheduler().start())
    queue_task = asyncio.create_task(get_task_queue().start())
    yield
    task.cancel()
    scheduler_task.cancel()
    queue_task.cancel()

app = FastAPI(
    title="Aeryn API",
    description="""
## Aeryn — Personal Assistant Agent SaaS

### Authentication
- **Bearer Token**: Use `/auth/login` to get a token, then include `Authorization: Bearer <token>` header
- **API Keys**: Use `/auth/api-keys` to create API keys for programmatic access

### Rate Limits
- **Free**: 60 req/min, 500 req/hour, 200 req/day
- **Pro**: 100 req/min, 1000 req/hour, 5000 req/day
- **Admin**: 200 req/min, 5000 req/hour, 50000 req/day

### Features
- **Chat**: Natural language conversation with Aeryn
- **Search**: Hybrid search (keyword + semantic)
- **Tasks**: Task management with priorities
- **Notifications**: Scheduled notifications
- **Vault**: Obsidian-style memory architecture
- **Proactive**: Daily briefings and suggestions
- **Multi-tenant**: Per-user data isolation
    """,
    version="41.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.router.lifespan_context = app_lifespan

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Global exception handler
@app.middleware("http")
async def global_exception_handler(request: Request, call_next):
    """Global HTTP exception handler with structured logging."""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        log_exception(e, context=f"{request.method} {request.url.path}")
        return Response(
            content=json.dumps({"error": "Internal server error", "detail": str(e)}),
            status_code=500,
            media_type="application/json",
        )

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    try:
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)
        
        # Get user from authorization header
        auth_header = request.headers.get("authorization", "")
        user_id = "anonymous"
        role = "free"
        
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            auth = get_auth()
            user = auth.validate_token(token)
            if user:
                user_id = user["id"]
                role = user.get("role", "user")
        
        # Check rate limit
        limiter = get_rate_limiter()
        result = limiter.check(
            user_id=user_id,
            endpoint=request.url.path,
            method=request.method,
            ip=request.client.host if request.client else None,
            ua=request.headers.get("user-agent"),
        )
        
        if not result["allowed"]:
            warn("Rate limit exceeded", user_id=user_id, endpoint=request.url.path)
            return Response(
                content=json.dumps({
                    "error": "Rate limit exceeded",
                    "retry_after": result.get("retry_after", 60),
                    "limit": result["limit"],
                    "window": result["window"],
                }),
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(int(result.get("retry_after", 60)))},
            )
        
        response = await call_next(request)
        return response
        
    except Exception as e:
        log_exception(e, context="rate_limit_middleware")
        return await call_next(request)

async def broadcast_loop():
    """Broadcast 15 data types every 5 seconds."""
    while True:
        await asyncio.sleep(5)
        emitter = get_emitter()
        try:
            # Get memory stats
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            mem_total = mem_available = 0
            for line in lines:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1])
            mem_used_mb = round((mem_total - mem_available) / 1024, 1) if mem_total else 0
            mem_total_mb = round(mem_total / 1024, 1) if mem_total else 0
            mem_pct = round(mem_used_mb / mem_total_mb * 100, 1) if mem_total_mb else 0

            try:
                import shutil
                disk = shutil.disk_usage("/")
                disk_free_gb = round(disk.free / (1024**3), 2)
                disk_pct = round((disk.total - disk.free) / disk.total * 100, 1)
            except Exception:
                disk_free_gb = 0
                disk_pct = 0

            # 1. Stats
            await emitter.broadcast("stats", {
                "memory_used_mb": mem_used_mb, "memory_total_mb": mem_total_mb,
                "memory_percent": mem_pct, "disk_free_gb": disk_free_gb, "disk_percent": disk_pct,
                "uptime_s": round(time.time() - _start_time, 0)
            })
            # 2. Tasks
            try:
                from aeryn_core.database.shared_db import get_shared_db
                db = get_shared_db()
                tasks = db.get_all_tasks()
                await emitter.broadcast("tasks", {"tasks": tasks, "count": len(tasks)})
            except Exception:
                await emitter.broadcast("tasks", {"tasks": [], "count": 0})
            # 3. Notifications
            try:
                notif_mgr = get_notification_manager()
                notifs = notif_mgr.get_pending()
                await emitter.broadcast("notifications", {"notifications": notifs})
            except Exception:
                await emitter.broadcast("notifications", {"notifications": []})
            # 4. Vault
            try:
                vault = AerynVault()
                entries = vault.list_entries(limit=20)
                counts = vault.count_entries()
                await emitter.broadcast("vault", {"entries": entries, "total_entries": sum(counts.values())})
            except Exception:
                await emitter.broadcast("vault", {"entries": [], "total_entries": 0})
            # 5. Tools
            try:
                rt = get_tool_runtime()
                await emitter.broadcast("tools", {"tools": rt.list_tools()})
            except Exception:
                await emitter.broadcast("tools", {"tools": []})
            # 6. Performance
            await emitter.broadcast("performance", {
                "cpu_percent": 0, "memory_percent": mem_pct,
                "memory_used_mb": mem_used_mb, "memory_total_mb": mem_total_mb,
                "disk_percent": disk_pct, "disk_free_gb": disk_free_gb
            })
            # 7. Uptime
            await emitter.broadcast("uptime", {
                "uptime": str(round(time.time() - _start_time, 0)) + "s",
                "uptime_s": round(time.time() - _start_time, 0)
            })
            # 8. Queue
            try:
                queue = get_task_queue()
                await emitter.broadcast("queue", {"pending": queue.get_pending_count(), "running": queue.get_running_count()})
            except Exception:
                await emitter.broadcast("queue", {"pending": 0, "running": 0})
            # 9. API Keys
            try:
                km = get_api_key_manager()
                await emitter.broadcast("api_keys", {"keys": km.list_keys("dashboard")})
            except Exception:
                await emitter.broadcast("api_keys", {"keys": []})
            # 10. Usage
            try:
                um = get_usage_metering()
                await emitter.broadcast("usage", um.get_summary("dashboard"))
            except Exception:
                await emitter.broadcast("usage", {"total_events": 0, "total_cost": 0})
            # 11. Secrets
            try:
                sm = get_secrets_manager()
                await emitter.broadcast("secrets", {"secrets": sm.list("dashboard")})
            except Exception:
                await emitter.broadcast("secrets", {"secrets": []})
            # 12. Circuit Breakers
            try:
                recovery = get_error_recovery()
                await emitter.broadcast("circuit_breakers", {"circuit_breakers": recovery.get_circuit_breaker_states()})
            except Exception:
                await emitter.broadcast("circuit_breakers", {"circuit_breakers": []})
            # 13. Briefing
            try:
                briefing = get_daily_briefing()
                await emitter.broadcast("briefing", briefing.generate_morning("dashboard"))
            except Exception:
                await emitter.broadcast("briefing", {"content": "Error generating briefing"})
            # 14. Suggestions
            try:
                engine = get_proactive_v2()
                await emitter.broadcast("suggestions", {"suggestions": engine.detect_patterns("dashboard")})
            except Exception:
                await emitter.broadcast("suggestions", {"suggestions": []})
            # 15. Constitutional
            try:
                cai = get_constitutional_ai()
                await emitter.broadcast("constitutional", {"principles": cai.get_principles()})
            except Exception:
                await emitter.broadcast("constitutional", {"principles": []})
        except Exception:
            pass

_start_time = time.time()
_request_count = 0
_error_count = 0

@app.middleware("http")
async def track_requests(request: Request, call_next):
    global _request_count, _error_count
    _request_count += 1
    try:
        response = await call_next(request)
        return response
    except Exception:
        _error_count += 1
        raise

class CompileRequest(BaseModel):
    session_id: str = "default"
    base_prompt: str = ""
    user_prompt: str = ""
    history: list = []
    tasks: list = []

class DigestRequest(BaseModel):
    session_id: str = "default"
    user_prompt: str = ""
    response: str = ""

class RunRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])

@app.get("/health")
async def health():
    try:
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        return {"status": "healthy", "memory_mb": round(mem_mb, 1), "version": "61.0"}
    except ImportError:
        return {"status": "healthy", "version": "61.0"}

@app.post("/compile")
async def compile(req: CompileRequest):
    eng = get_safety_engine()
    safety = eng.check_input(req.user_prompt)
    research = needs_research(req.user_prompt)
    adapter = get_active_adapter(req.user_prompt)
    persona = load_persona()
    emotional_tensor = {"safety_risk": safety.risk, "needs_research": research, "adapter": adapter.name if adapter else None, "safe": safety.safe}
    sm = SocialMemory()
    facts = sm.get_facts(req.session_id)
    prompt_parts = []
    if req.base_prompt: prompt_parts.append(req.base_prompt[:500])
    prompt_parts.append(f"\n[User: {req.user_prompt}]")
    if facts: prompt_parts.append(f"\n[Context: {', '.join(str(f) for f in facts[:5])}]")
    if adapter:
        ctx = render_adapter_context(req.user_prompt)
        if ctx: prompt_parts.append(f"\n{ctx}")
    gate_mode = "blocked" if not safety.safe else ("research" if research else ("adapter" if adapter else "standard"))
    return {"ok": True, "gate_mode": gate_mode, "blackboard": {"emotional_tensor_snapshot": emotional_tensor}, "memories": facts[:10] if facts else [], "compiled_prompt": "\n".join(prompt_parts), "safety": safety.to_dict()}

@app.post("/digest")
async def digest(req: DigestRequest):
    eng = get_safety_engine()
    clean_response = sanitize_output(req.response)
    vault = AerynVault()
    if len(req.user_prompt) > 10 and len(clean_response) > 10:
        try:
            vault.write(VaultEntry(layer=LAYER_WIKI, title=f"Conversation {req.session_id[:8]}", body=f"User: {req.user_prompt[:200]}\n\nResponse: {clean_response[:500]}", tags=["conversation", "auto"]))
        except Exception: pass
    return {"ok": True, "status": "digested", "accounting_ledger_audit": {"audit_payload": {"session_id": req.session_id, "timestamp": time.time()}}, "cog_mem_lifecycle_telemetry": {"focus_segment_retained": len(req.user_prompt) > 10}}

@app.post("/run")
async def run(req: RunRequest):
    eng = get_safety_engine()
    safety = eng.check_input(req.goal)
    if not safety.safe: return {"status": "blocked", "safety": safety.to_dict()}
    
    research = needs_research(req.goal)
    adapter = get_active_adapter(req.goal)
    persona = load_persona()
    
    # Build prompt
    prompt = f"{persona}\n\nUser: {req.goal}"
    if adapter: prompt += f"\n{render_adapter_context(req.goal)}"
    
    # Get mode router
    router = get_mode_router()
    
    if router.is_standalone():
        # Standalone mode: call LLM directly
        try:
            messages = [
                {"role": "system", "content": persona},
                {"role": "user", "content": req.goal},
            ]
            result = await router.llm.chat(messages)
            response = result["content"]
            return {
                "status": "ok",
                "session_id": req.session_id,
                "safety": safety.to_dict(),
                "adapter": adapter.name if adapter else None,
                "needs_research": research,
                "response": sanitize_output(response),
                "provider": result.get("provider"),
                "model": result.get("model"),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "session_id": req.session_id,
            }
    else:
        # Plugin mode: return prompt for Hermes to process
        response = f"Processing: {req.goal[:200]}"
        if adapter: response += f"\n[Adapter: {adapter.name}]"
        if research: response += "\n[Research needed]"
        return {
            "status": "ok",
            "session_id": req.session_id,
            "safety": safety.to_dict(),
            "adapter": adapter.name if adapter else None,
            "needs_research": research,
            "response": sanitize_output(response),
        }


@app.post("/chat")
async def chat(req: RunRequest):
    """Full chat endpoint with session + LLM (standalone mode)."""
    router = get_mode_router()
    
    if router.is_plugin():
        return await run(req)
    
    # Get or create session
    session = router.get_or_create_session(req.session_id)
    
    # Safety check
    eng = get_safety_engine()
    safety = eng.check_input(req.goal)
    if not safety.safe:
        return {"status": "blocked", "safety": safety.to_dict()}
    
    # Add user message
    session.add_message("user", req.goal)
    
    # Get context window
    messages = [
        {"role": "system", "content": load_persona()},
    ] + session.get_context_window()
    
    # Call LLM
    try:
        result = await router.llm.chat(messages)
        response = result["content"]
        reasoning = result.get("reasoning", [])

        # Store response
        session.add_message("assistant", response, json.dumps(reasoning))
        
        return {
            "status": "ok",
            "session_id": req.session_id,
            "response": response,
            "provider": result.get("provider"),
            "model": result.get("model"),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/search")
async def search(q: str, limit: int = 10):
    hse = get_search_engine()
    results = hse.search(q, limit=limit)
    return {"query": q, "results": results, "count": len(results)}

@app.get("/dashboard")
async def dashboard():
    """Serve monitoring dashboard HTML."""
    return FileResponse("apps/api/dashboard.html")

@app.get("/chat")
async def web_chat():
    """Serve web chat interface."""
    return Response(
        content=WEB_CHAT_HTML,
        media_type="text/html",
    )

WEB_CHAT_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aeryn Chat</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: system-ui; background:#09090b; color:#fafafa; height:100vh; display:flex; flex-direction:column; }
#header { padding:16px 24px; background:#18181b; border-bottom:1px solid #27272a; display:flex; align-items:center; gap:12px; }
#header h1 { font-size:18px; }
#status { width:8px; height:8px; border-radius:50%; background:#f87171; }
#status.online { background:#4ade80; }
#messages { flex:1; overflow-y:auto; padding:24px; display:flex; flex-direction:column; gap:16px; }
.message { max-width:70%; padding:12px 16px; border-radius:12px; line-height:1.5; }
.message.user { align-self:flex-end; background:#22d3ee; color:#09090b; }
.message.assistant { align-self:flex-start; background:#27272a; }
.message .role { font-size:11px; opacity:0.7; margin-bottom:4px; }
#input-area { padding:16px 24px; background:#18181b; border-top:1px solid #27272a; display:flex; gap:12px; }
#input { flex:1; padding:12px 16px; border:none; border-radius:8px; background:#27272a; color:#fafafa; font-size:14px; outline:none; }
#send { padding:12px 24px; border:none; border-radius:8px; background:#22d3ee; color:#09090b; font-weight:600; cursor:pointer; }
#send:hover { background:#06b6d4; }
</style>
</head>
<body>
<div id="header">
    <div id="status"></div>
    <h1>Aeryn Chat</h1>
</div>
<div id="messages"></div>
<div id="input-area">
    <input id="input" placeholder="Type a message..." autocomplete="off">
    <button id="send" onclick="send()">Send</button>
</div>
<script>
const messages = document.getElementById('messages');
const input = document.getElementById('input');
const status = document.getElementById('status');
let sessionId = 'web_' + Date.now();

function addMessage(role, content) {
    const div = document.createElement('div');
    div.className = 'message ' + role;
    div.innerHTML = '<div class="role">' + role + '</div>' + content.replace(/\\n/g, '<br>');
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

async function send() {
    const text = input.value.trim();
    if (!text) return;
    addMessage('user', text);
    input.value = '';
    
    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({goal: text, session_id: sessionId})
        });
        const data = await res.json();
        addMessage('assistant', data.response || JSON.stringify(data));
    } catch(e) {
        addMessage('assistant', 'Error: ' + e.message);
    }
}

input.addEventListener('keypress', (e) => { if(e.key === 'Enter') send(); });

// Check status
fetch('/health').then(r => r.json()).then(d => {
    if(d.status === 'healthy') status.className = 'online';
}).catch(() => {});
</script>
</body>
</html>"""

# ── SSE + WebSocket Endpoints ─────────────────────────────────

from sse_starlette.sse import EventSourceResponse

@app.get("/dashboard/stream")
async def dashboard_stream():
    """SSE endpoint for real-time dashboard updates."""
    emitter = get_emitter()
    queue = asyncio.Queue()
    client_id = f"dashboard_{id(queue)}_{int(time.time())}"
    emitter.register_sse(client_id, queue)
    
    async def event_generator():
        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield {"event": event["type"], "data": json.dumps(event)}
        except asyncio.TimeoutError:
            yield {"event": "ping", "data": json.dumps({"timestamp": time.time()})}
        finally:
            emitter.unregister_sse(client_id)
    
    return EventSourceResponse(event_generator())


@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket endpoint for two-way dashboard commands."""
    emitter = get_emitter()
    client_id = f"ws_{int(time.time())}"
    await websocket.accept()
    emitter.register_ws(client_id, websocket)
    
    try:
        await websocket.send_json({"type": "connected", "data": {}})
        
        while True:
            msg = await websocket.receive_text()
            try:
                cmd = json.loads(msg)
                cmd_type = cmd.get("type", "")
                cmd_data = cmd.get("data", {})
                if isinstance(cmd_data, str):
                    try:
                        cmd_data = json.loads(cmd_data)
                    except (json.JSONDecodeError, TypeError):
                        cmd_data = {}
                
                if cmd_type == "ping":
                    await websocket.send_json({"type": "pong", "data": {}})
                elif cmd_type == "chat":
                    try:
                        from aeryn_core.safety.safety_engine import get_safety_engine
                        from aeryn_core.utils.persona_engine import load_persona
                        eng = get_safety_engine()
                        text = cmd_data.get("message", "")
                        safety = eng.check_input(text)
                        if not safety.safe:
                            await websocket.send_json({"type": "error", "data": {"message": "Blocked"}})
                        else:
                            persona = load_persona()
                            router = get_mode_router()
                            sid = cmd_data.get("session_id", "default")
                            session = router.get_or_create_session(sid)
                            session.add_message("user", text)
                            messages = [{"role": "system", "content": persona}] + session.get_context_window()
                            result = await router.llm.chat(messages, sid)
                            response = result["content"]
                            session.add_message("assistant", response, json.dumps(result.get("reasoning", [])))
                            reasoning = result.get("reasoning", [])
                            await websocket.send_json({"type": "chat_response", "data": {"response": response, "session_id": sid, "reasoning": reasoning}})
                            # Small delay to ensure chat_response is received before broadcast
                            await asyncio.sleep(0.5)
                    except Exception as e:
                        await websocket.send_json({"type": "error", "data": {"message": str(e)}})
                elif cmd_type == "parse_tasks":
                    try:
                        auto_task = get_auto_task()
                        tasks = auto_task.parse(cmd_data.get("user_id", "default"), cmd_data.get("text", ""))
                        await websocket.send_json({"type": "task_parsed", "data": {"tasks": tasks, "count": len(tasks)}})
                    except Exception as e:
                        await websocket.send_json({"type": "error", "data": {"message": str(e)}})
                elif cmd_type == "execute_tool":
                    try:
                        rt = get_tool_runtime()
                        result = await rt.execute(cmd_data.get("tool", ""), cmd_data.get("params", {}))
                        await websocket.send_json({"type": "tool_result", "data": result.to_dict()})
                    except Exception as e:
                        await websocket.send_json({"type": "error", "data": {"message": str(e)}})
                elif cmd_type == "create_notification":
                    try:
                        from aeryn_core.platform.notification_system import Notification
                        mgr = get_notification_manager()
                        notif = Notification(user_id=cmd_data.get("user_id", "default"), title=cmd_data.get("title", ""), message=cmd_data.get("message", ""), priority=cmd_data.get("priority", "normal"))
                        nid = mgr.create(notif)
                        await websocket.send_json({"type": "notif_created", "data": {"id": nid}})
                    except Exception as e:
                        await websocket.send_json({"type": "error", "data": {"message": str(e)}})
                elif cmd_type == "check_safety":
                    try:
                        eng = get_safety_engine()
                        result = eng.check_input(cmd_data.get("text", ""))
                        await websocket.send_json({"type": "safety_result", "data": {"valid": result.safe, "risk": result.risk}})
                    except Exception as e:
                        await websocket.send_json({"type": "error", "data": {"message": str(e)}})
                elif cmd_type == "create_api_key":
                    try:
                        km = get_api_key_manager()
                        result = km.create(cmd_data.get("user_id", "default"), cmd_data.get("name", "key"))
                        await websocket.send_json({"type": "api_key_created", "data": result})
                    except Exception as e:
                        await websocket.send_json({"type": "error", "data": {"message": str(e)}})
                elif cmd_type == "set_secret":
                    try:
                        sm = get_secrets_manager()
                        sm.set(cmd_data.get("user_id", "default"), cmd_data.get("name", ""), cmd_data.get("value", ""))
                        await websocket.send_json({"type": "secret_stored", "data": {}})
                    except Exception as e:
                        await websocket.send_json({"type": "error", "data": {"message": str(e)}})
                elif cmd_type == "search":
                    try:
                        idx = get_semantic_indexer()
                        results = idx.search(cmd_data.get("user_id", ""), limit=10)
                        await websocket.send_json({"type": "search_results", "data": {"results": results}})
                    except Exception as e:
                        await websocket.send_json({"type": "error", "data": {"message": str(e)}})
                elif cmd_type == "get_history":
                    history = emitter.get_history(50)
                    await websocket.send_json({"type": "history", "data": history})
                elif cmd_type == "get_stats":
                    stats = emitter.get_stats()
                    await websocket.send_json({"type": "stats", "data": stats})
                elif cmd_type == "action":
                    action = cmd_data.get("action", "")
                    # Handle actions
                    if action == "backup":
                        await websocket.send_json({"type": "action_result", "data": {"action": action, "status": "started"}})
                    elif action == "dream":
                        await websocket.send_json({"type": "action_result", "data": {"action": action, "status": "started"}})
                    elif action == "cache-clear":
                        await websocket.send_json({"type": "action_result", "data": {"action": action, "status": "done"}})
                    elif action == "restart":
                        await websocket.send_json({"type": "action_result", "data": {"action": action, "status": "started"}})
                    else:
                        await websocket.send_json({"type": "error", "data": {"message": f"Unknown action: {action}"}})
                else:
                    await websocket.send_json({"type": "error", "data": {"message": f"Unknown command: {cmd_type}"}})
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "data": {"message": "Invalid JSON"}})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        emitter.unregister_ws(client_id)

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aeryn Dashboard — V40.55</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #09090b;
  --bg-card: #18181b;
  --bg-hover: #27272a;
  --border: #27272a;
  --text: #fafafa;
  --text-muted: #a1a1aa;
  --accent: #22d3ee;
  --green: #4ade80;
  --yellow: #facc15;
  --red: #f87171;
  --purple: #c084fc;
  --orange: #fb923c;
}

* { margin:0; padding:0; box-sizing:border-box; }

body {
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  padding: 24px;
  line-height: 1.5;
}

/* ── Header ──────────────────────────────── */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}

.header .brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand .logo {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.brand h1 {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.brand .version {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--bg-card);
  padding: 2px 8px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
}

.header .clock {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  color: var(--text-muted);
}

/* ── Grid ────────────────────────────────── */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  transition: border-color 0.2s, transform 0.2s;
}

.card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
}

.card .label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  margin-bottom: 8px;
  font-weight: 600;
}

.card .value {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
  font-family: 'JetBrains Mono', monospace;
}

.card .unit {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 400;
  margin-left: 4px;
}

.card .detail {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* ── Progress Bar ────────────────────────── */
.progress-track {
  height: 4px;
  background: var(--bg);
  border-radius: 2px;
  margin-top: 12px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--green), var(--accent));
  border-radius: 2px;
  transition: width 0.5s ease;
}

.progress-fill.warn { background: linear-gradient(90deg, var(--yellow), var(--orange)); }
.progress-fill.danger { background: linear-gradient(90deg, var(--orange), var(--red)); }

/* ── Section ─────────────────────────────── */
.section {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}

.section h2 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ── Service Status ──────────────────────── */
.service-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.service-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg);
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-family: 'JetBrains Mono', monospace;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.online { background: var(--green); box-shadow: 0 0 6px var(--green); }
.dot.offline { background: var(--red); }

/* ── Table ───────────────────────────────── */
table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}

th {
  color: var(--text-muted);
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

td { font-family: 'JetBrains Mono', monospace; }
td:last-child { text-align: right; }

tr:last-child td { border-bottom: none; }

/* ── Endpoints ───────────────────────────── */
.endpoint-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
}

.endpoint-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg);
  border-radius: 6px;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  border: 1px solid transparent;
}

.endpoint-chip:hover {
  border-color: var(--accent);
}

.method {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
}

.method.get { background: rgba(74, 222, 128, 0.15); color: var(--green); }
.method.post { background: rgba(34, 211, 238, 0.15); color: var(--accent); }
.method.delete { background: rgba(248, 113, 113, 0.15); color: var(--red); }

/* ── Live indicator ──────────────────────── */
.live {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.live .pulse {
  width: 6px;
  height: 6px;
  background: var(--green);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── Sparkline ──────────────────────────────── */
.sparkline-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.sparkline-card {
  background: var(--bg);
  border-radius: 8px;
  padding: 16px;
}

.sparkline-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sparkline {
  width: 100%;
  height: 40px;
}

.sparkline-lg {
  width: 100%;
  height: 60px;
}

/* ── Quick Actions ──────────────────────────── */
.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text);
  font-family: inherit;
}

.action-btn:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  background: var(--bg-hover);
}

.action-btn:active {
  transform: translateY(0);
}

.action-icon {
  font-size: 24px;
}

.action-label {
  font-size: 12px;
  font-weight: 500;
}

/* ── Activity Feed ──────────────────────────── */
.activity-feed {
  max-height: 200px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.activity-empty {
  color: var(--text-muted);
  text-align: center;
  padding: 20px;
  font-size: 13px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg);
  border-radius: 8px;
  font-size: 13px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-10px); }
  to { opacity: 1; transform: translateX(0); }
}

.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.activity-dot.info { background: var(--accent); }
.activity-dot.success { background: var(--green); }
.activity-dot.warning { background: var(--yellow); }
.activity-dot.error { background: var(--red); }

.activity-text {
  flex: 1;
}

.activity-time {
  font-size: 11px;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}

/* ── Notifications ──────────────────────────── */
.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notification-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: var(--bg);
  border-radius: 8px;
  border-left: 3px solid var(--yellow);
  font-size: 13px;
}

.notification-item.critical {
  border-left-color: var(--red);
}

.notification-dismiss {
  margin-left: auto;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
}

.notification-dismiss:hover {
  color: var(--text);
}

/* ── Toast ──────────────────────────────────── */
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.toast {
  padding: 12px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 13px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  animation: toastIn 0.3s ease;
  max-width: 300px;
}

.toast.success { border-left: 3px solid var(--green); }
.toast.error { border-left: 3px solid var(--red); }
.toast.warning { border-left: 3px solid var(--yellow); }
.toast.info { border-left: 3px solid var(--accent); }

@keyframes toastIn {
  from { opacity: 0; transform: translateX(100%); }
  to { opacity: 1; transform: translateX(0); }
}
/* ── Light Theme ───────────────────────────── */
body.light {
  --bg: #fafafa;
  --bg-card: #ffffff;
  --bg-hover: #f4f4f5;
  --border: #e4e4e7;
  --text: #18181b;
  --text-muted: #71717a;
}

/* ── Task Queue ─────────────────────────────── */
.task-count {
  background: var(--accent);
  color: var(--bg);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  margin-left: 8px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-empty {
  color: var(--text-muted);
  text-align: center;
  padding: 16px;
  font-size: 13px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg);
  border-radius: 8px;
}

.task-info {
  flex: 1;
}

.task-title {
  font-size: 13px;
  font-weight: 500;
}

.task-status {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
}

.task-progress {
  width: 60px;
  height: 4px;
  background: var(--bg-hover);
  border-radius: 2px;
  overflow: hidden;
}

.task-progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s;
}

/* ── Memory Browser ────────────────────────── */
.search-box {
  position: relative;
  margin-bottom: 16px;
}

.search-box input {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 14px;
  font-family: inherit;
  outline: none;
}

.search-box input:focus {
  border-color: var(--accent);
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
  display: none;
}

.search-results.active {
  display: block;
}

.search-result-item {
  padding: 10px 14px;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}

.search-result-item:hover {
  background: var(--bg-hover);
}

.memory-table-wrap {
  max-height: 300px;
  overflow-y: auto;
}

.memory-table {
  width: 100%;
}

.memory-table th {
  position: sticky;
  top: 0;
  background: var(--bg-card);
}

.memory-table td {
  font-size: 12px;
}

.memory-table .view-btn {
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
}

.memory-table .view-btn:hover {
  border-color: var(--accent);
}

.pagination {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 12px;
}

.pagination button {
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.pagination button:hover:not(:disabled) {
  border-color: var(--accent);
}

.pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pagination .page-info {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: var(--text-muted);
}

/* ── Modal ──────────────────────────────────── */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 24px;
  cursor: pointer;
  padding: 4px;
}

.modal-close:hover {
  color: var(--text);
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  max-height: 60vh;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* ── Collapsible ────────────────────────────── */
.section.collapsible .section-header {
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section.collapsible .section-header::after {
  content: '▾';
  font-size: 14px;
  transition: transform 0.2s;
}

.section.collapsed .section-header::after {
  transform: rotate(-90deg);
}

.section.collapsed .section-content {
  display: none;
}

/* ── Phase 4: UX Polish ────────────────────── */

/* Skeleton Loading */
.skeleton {
  background: linear-gradient(90deg, var(--bg) 25%, var(--bg-hover) 50%, var(--bg) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton-text {
  height: 14px;
  margin-bottom: 8px;
}

.skeleton-card {
  height: 80px;
}

/* Card Expand */
.card.expandable {
  cursor: pointer;
  transition: all 0.2s;
}

.card.expandable:hover {
  transform: translateY(-2px);
  border-color: var(--accent);
}

/* Live Logs */
.log-viewer {
  max-height: 150px;
  overflow-y: auto;
  background: var(--bg);
  border-radius: 8px;
  padding: 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  line-height: 1.6;
}

.log-entry {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid var(--border);
}

.log-entry:last-child {
  border-bottom: none;
}

.log-time {
  color: var(--text-muted);
  flex-shrink: 0;
}

.log-level {
  flex-shrink: 0;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 10px;
  text-transform: uppercase;
}

.log-level.info { background: rgba(34, 211, 238, 0.15); color: var(--accent); }
.log-level.warn { background: rgba(250, 204, 21, 0.15); color: var(--yellow); }
.log-level.error { background: rgba(248, 113, 113, 0.15); color: var(--red); }

.log-message {
  flex: 1;
  word-break: break-all;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  body { padding: 16px; }
  
  .header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .header .live {
    width: 100%;
    justify-content: space-between;
  }
  
  .grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .sparkline-grid {
    grid-template-columns: 1fr;
  }
  
  .action-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .service-list {
    flex-direction: column;
  }
  
  .service-chip {
    width: 100%;
  }
  
  .endpoint-grid {
    grid-template-columns: 1fr;
  }
  
  .card .value {
    font-size: 22px;
  }
  
  .modal {
    width: 95%;
    max-width: none;
  }
  
  .memory-table-wrap {
    max-height: 200px;
  }
}

/* Touch-friendly */
@media (hover: none) {
  .action-btn:hover {
    transform: none;
  }
  
  .card:hover {
    transform: none;
  }
  
  .action-btn:active {
    background: var(--bg-hover);
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Offline indicator */
.offline-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: var(--red);
  color: white;
  text-align: center;
  padding: 8px;
  font-size: 12px;
  z-index: 9999;
  display: none;
}

body.offline .offline-banner {
  display: block;
}

body.offline .header {
  margin-top: 36px;
}

.footer {
  text-align: center;
  padding: 24px 0;
  color: var(--text-muted);
  font-size: 12px;
}
</style>
</head>
<body>

<div class="header">
  <div class="brand">
    <div class="logo">✦</div>
    <div>
      <h1>Aeryn</h1>
      <span class="version" id="version">v40.54</span>
    </div>
  </div>
  <div class="live">
    <div class="pulse" id="sse-dot"></div>
    <span id="conn-status">LIVE</span>
    <span class="clock" id="clock">--:--:--</span>
  </div>
</div>

<!-- ── System Cards ────────────────────────── -->
<div class="grid">
  <div class="card">
    <div class="label">🧠 Memory</div>
    <div class="value" id="mem">--<span class="unit">MB</span></div>
    <div class="detail" id="mem-detail">--% used</div>
    <div class="progress-track"><div class="progress-fill" id="mem-bar" style="width:0%"></div></div>
  </div>

  <div class="card">
    <div class="label">💾 Disk</div>
    <div class="value" id="disk">--<span class="unit">GB</span></div>
    <div class="detail" id="disk-detail">-- used</div>
    <div class="progress-track"><div class="progress-fill" id="disk-bar" style="width:0%"></div></div>
  </div>

  <div class="card">
    <div class="label">⚡ Process</div>
    <div class="value" id="proc-mem">--<span class="unit">MB</span></div>
    <div class="detail" id="uptime">-- uptime</div>
  </div>

  <div class="card">
    <div class="label">📊 Requests</div>
    <div class="value" id="req-total">--</div>
    <div class="detail" id="err-detail">-- errors</div>
    <canvas id="sparkline-reqs" class="sparkline" width="200" height="40"></canvas>
  </div>
</div>

<!-- ── Sparkline Charts ──────────────────────── -->
<div class="section">
  <h2>📈 Trends (60s)</h2>
  <div class="sparkline-grid">
    <div class="sparkline-card">
      <div class="sparkline-label">Memory</div>
      <canvas id="sparkline-mem" class="sparkline-lg" width="300" height="60"></canvas>
    </div>
    <div class="sparkline-card">
      <div class="sparkline-label">Disk</div>
      <canvas id="sparkline-disk" class="sparkline-lg" width="300" height="60"></canvas>
    </div>
  </div>
</div>

<!-- ── Quick Actions ─────────────────────────── -->
<div class="section">
  <h2>⚡ Quick Actions</h2>
  <div class="action-grid">
    <button class="action-btn" onclick="runAction('backup')">
      <span class="action-icon">💾</span>
      <span class="action-label">Backup</span>
    </button>
    <button class="action-btn" onclick="runAction('dream')">
      <span class="action-icon">💭</span>
      <span class="action-label">Dream</span>
    </button>
    <button class="action-btn" onclick="runAction('cache-clear')">
      <span class="action-icon">🗑️</span>
      <span class="action-label">Clear Cache</span>
    </button>
    <button class="action-btn" onclick="runAction('restart')">
      <span class="action-icon">🔄</span>
      <span class="action-label">Restart</span>
    </button>
  </div>
</div>

<!-- ── Activity Feed ─────────────────────────── -->
<div class="section">
  <h2>🔔 Activity Feed</h2>
  <div class="activity-feed" id="activity-feed">
    <div class="activity-empty">Waiting for events...</div>
  </div>
</div>

<!-- ── Notifications Panel ───────────────────── -->
<div class="section" id="notifications-section" style="display:none">
  <h2>🚨 Alerts</h2>
  <div class="notifications-list" id="notifications-list"></div>
</div>

<!-- ── Task Queue Monitor ─────────────────────── -->
<div class="section" id="task-monitor-section">
  <h2>📋 Task Queue <span class="task-count" id="task-count">0</span></h2>
  <div class="task-list" id="task-list">
    <div class="task-empty">No pending tasks</div>
  </div>
</div>

<!-- ── Memory Browser ────────────────────────── -->
<div class="section" id="memory-browser-section">
  <h2>🧠 Memory Browser</h2>
  <div class="search-box">
    <input type="text" id="memory-search" placeholder="Search memories..." autocomplete="off">
    <div class="search-results" id="search-results"></div>
  </div>
  <div class="memory-table-wrap">
    <table class="memory-table">
      <thead><tr><th>Title</th><th>Layer</th><th>Tags</th><th></th></tr></thead>
      <tbody id="memory-table-body"></tbody>
    </table>
  </div>
  <div class="pagination" id="memory-pagination"></div>
</div>

<!-- ── Memory Detail Modal ───────────────────── -->
<div class="modal-overlay" id="memory-modal" style="display:none">
  <div class="modal">
    <div class="modal-header">
      <h3 id="modal-title">Memory Detail</h3>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>
<div class="section">
  <h2>🖥️ Services</h2>
  <div class="service-list" id="services">
    <div class="service-chip"><div class="dot online"></div><span>aeryn-api</span></div>
    <div class="service-chip"><div class="dot online"></div><span>n8n</span></div>
    <div class="service-chip"><div class="dot online"></div><span>webnovel-api</span></div>
    <div class="service-chip"><div class="dot online"></div><span>webnovel-web</span></div>
    <div class="service-chip"><div class="dot offline"></div><span>hermes-gw</span></div>
  </div>
</div>

<!-- ── Aeryn Stats ─────────────────────────── -->
<div class="section">
  <h2>📈 Aeryn Metrics</h2>
  <table>
    <thead><tr><th>Metric</th><th style="text-align:right">Value</th></tr></thead>
    <tbody>
      <tr><td>Vault Entries</td><td id="vault-total">--</td></tr>
      <tr><td>Search Documents</td><td id="search-docs">--</td></tr>
      <tr><td>Social People</td><td id="social-ppl">--</td></tr>
      <tr><td>Safety Engine</td><td style="color:var(--green)">● OK</td></tr>
    </tbody>
  </table>
</div>

<!-- ── Vault Layers ────────────────────────── -->
<div class="section">
  <h2>📁 Vault Layers</h2>
  <table>
    <thead><tr><th>Layer</th><th style="text-align:right">Entries</th></tr></thead>
    <tbody id="vault-table"><tr><td colspan="2" style="text-align:center;color:var(--text-muted)">...</td></tr></tbody>
  </table>
</div>

<!-- ── Endpoints ───────────────────────────── -->
<div class="section">
  <h2>🔌 Quick Endpoints</h2>
  <div class="endpoint-grid">
    <div class="endpoint-chip"><span class="method get">GET</span>/health</div>
    <div class="endpoint-chip"><span class="method get">GET</span>/search</div>
    <div class="endpoint-chip"><span class="method post">POST</span>/run</div>
    <div class="endpoint-chip"><span class="method post">POST</span>/compile</div>
    <div class="endpoint-chip"><span class="method post">POST</span>/digest</div>
    <div class="endpoint-chip"><span class="method get">GET</span>/agents</div>
    <div class="endpoint-chip"><span class="method post">POST</span>/dream/synthesize</div>
    <div class="endpoint-chip"><span class="method get">GET</span>/dashboard/stats</div>
  </div>
</div>

<!-- ── Live Logs Viewer ───────────────────────── -->
<div class="section" id="logs-section">
  <h2>📜 Live Logs</h2>
  <div class="log-viewer" id="log-viewer">
    <div class="log-entry"><span class="log-message">Connecting...</span></div>
  </div>
</div>

<div class="offline-banner" id="offline-banner">
  ⚠️ Connection lost. Reconnecting...
</div>

<div class="toast-container" id="toast-container"></div>

<div class="footer">
  Aeryn V40.54 — Built with ❤️ by Hermes + Aeryn
</div>

<script>
function updateClock() {
  const now = new Date();
  document.getElementById('clock').textContent = now.toLocaleTimeString('id-ID', { hour12: false });
}

// ── Sparkline Charts ────────────────────────
const sparklineData = {
  mem: [],
  disk: [],
  reqs: [],
  maxPoints: 60
};

function drawSparkline(canvasId, data, color) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  
  ctx.clearRect(0, 0, w, h);
  
  if (data.length < 2) return;
  
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  
  for (let i = 0; i < data.length; i++) {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((data[i] - min) / range) * (h - 4) - 2;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
  
  // Fill under curve
  ctx.lineTo(w, h);
  ctx.lineTo(0, h);
  ctx.closePath();
  ctx.fillStyle = color.replace(')', ', 0.1)').replace('rgb', 'rgba');
  ctx.fill();
}

// ── Activity Feed ────────────────────────────
const activityFeed = [];

function addActivity(type, text) {
  const feed = document.getElementById('activity-feed');
  if (!feed) return;
  
  const empty = feed.querySelector('.activity-empty');
  if (empty) empty.remove();
  
  const item = document.createElement('div');
  item.className = 'activity-item';
  item.innerHTML = `
    <div class="activity-dot ${type}"></div>
    <span class="activity-text">${text}</span>
    <span class="activity-time">${new Date().toLocaleTimeString('id-ID', {hour12:false})}</span>
  `;
  
  feed.insertBefore(item, feed.firstChild);
  
  // Keep max 20 items
  while (feed.children.length > 20) {
    feed.removeChild(feed.lastChild);
  }
}

// ── Notifications ────────────────────────────
const notifications = [];

function addNotification(type, message) {
  const section = document.getElementById('notifications-section');
  const list = document.getElementById('notifications-list');
  if (!section || !list) return;
  
  section.style.display = 'block';
  
  const item = document.createElement('div');
  item.className = 'notification-item' + (type === 'critical' ? ' critical' : '');
  item.innerHTML = `
    <span>${type === 'critical' ? '🚨' : '⚠️'}</span>
    <span>${message}</span>
    <button class="notification-dismiss" onclick="this.parentElement.remove()">×</button>
  `;
  
  list.insertBefore(item, list.firstChild);
  
  // Show toast
  showToast(type, message);
}

function showToast(type, message) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  
  const toast = document.createElement('div');
  toast.className = 'toast ' + type;
  toast.textContent = message;
  
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 5000);
}

// ── Quick Actions ────────────────────────────
function runAction(action) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    showToast('error', 'WebSocket not connected');
    return;
  }
  
  ws.send(JSON.stringify({type: 'action', data: {action: action}}));
  addActivity('info', `Action: ${action}`);
  showToast('info', `Running: ${action}`);
}

// ── SSE: Real-time stats ──────────────────────
function connectSSE() {
  const evtSource = new EventSource('/dashboard/stream');
  
  evtSource.onopen = function() {
    document.getElementById('sse-dot').style.background = 'var(--green)';
    document.getElementById('conn-status').textContent = 'LIVE';
  };
  
  evtSource.addEventListener('stats', function(e) {
    const d = JSON.parse(e.data);
    const s = d.data;
    
    // Update sparkline data
    sparklineData.mem.push(s.memory_percent);
    if (sparklineData.mem.length > sparklineData.maxPoints) sparklineData.mem.shift();
    
    sparklineData.disk.push(s.disk_percent);
    if (sparklineData.disk.length > sparklineData.maxPoints) sparklineData.disk.shift();
    
    sparklineData.reqs.push(s.requests_total);
    if (sparklineData.reqs.length > sparklineData.maxPoints) sparklineData.reqs.shift();
    
    // Draw sparklines
    drawSparkline('sparkline-mem', sparklineData.mem, 'rgb(74, 222, 128)');
    drawSparkline('sparkline-disk', sparklineData.disk, 'rgb(34, 211, 238)');
    drawSparkline('sparkline-reqs', sparklineData.reqs, 'rgb(192, 132, 252)');
    
    // Memory
    document.getElementById('mem').innerHTML = s.memory_used_mb + '<span class="unit">MB</span>';
    document.getElementById('mem-detail').textContent = s.memory_percent + '% of ' + s.memory_total_mb + ' MB';
    const memBar = document.getElementById('mem-bar');
    memBar.style.width = s.memory_percent + '%';
    memBar.className = 'progress-fill' + (s.memory_percent > 85 ? ' warn' : '') + (s.memory_percent > 95 ? ' danger' : '');

    // Disk
    document.getElementById('disk').innerHTML = s.disk_free_gb + '<span class="unit">GB</span>';
    document.getElementById('disk-detail').textContent = s.disk_percent + '% used';
    const diskBar = document.getElementById('disk-bar');
    diskBar.style.width = s.disk_percent + '%';
    diskBar.className = 'progress-fill' + (s.disk_percent > 85 ? ' warn' : '') + (s.disk_percent > 95 ? ' danger' : '');

    // Process
    document.getElementById('proc-mem').innerHTML = s.process_mem_mb + '<span class="unit">MB</span>';
    const hrs = Math.floor(s.uptime_s / 3600);
    const mins = Math.floor((s.uptime_s % 3600) / 60);
    document.getElementById('uptime').textContent = hrs + 'h ' + mins + 'm uptime';

    // Requests
    document.getElementById('req-total').textContent = s.requests_total;
    document.getElementById('err-detail').textContent = s.errors_total + ' errors';
    
    // Threshold alerts
    if (s.memory_percent > 90) {
      addNotification('critical', `Memory usage critical: ${s.memory_percent}%`);
    } else if (s.memory_percent > 80) {
      addNotification('warning', `Memory usage high: ${s.memory_percent}%`);
    }
    
    if (s.disk_percent > 90) {
      addNotification('critical', `Disk usage critical: ${s.disk_percent}%`);
    }
  });
  
  evtSource.onerror = function() {
    document.getElementById('sse-dot').style.background = 'var(--red)';
    document.getElementById('conn-status').textContent = 'RECONNECTING';
    evtSource.close();
    setTimeout(connectSSE, 3000);
  };
}

// ── WebSocket: Commands ───────────────────────
let ws = null;

function connectWS() {
  ws = new WebSocket('ws://' + window.location.host + '/ws/dashboard');
  
  ws.onopen = function() {
    console.log('WS connected');
  };
  
  ws.onmessage = function(e) {
    const msg = JSON.parse(e.data);
    if (msg.type === 'connected') {
      console.log('WS ready');
    } else if (msg.type === 'action_result') {
      addActivity('success', `Action ${msg.data.action}: ${msg.data.status}`);
      showToast('success', `${msg.data.action} → ${msg.data.status}`);
    }
  };
  
  ws.onclose = function() {
    console.log('WS disconnected, reconnecting...');
    setTimeout(connectWS, 3000);
  };
}

// ── Theme Toggle ─────────────────────────────
function toggleTheme() {
  document.body.classList.toggle('light');
  localStorage.setItem('aeryn-theme', document.body.classList.contains('light') ? 'light' : 'dark');
}

function loadTheme() {
  if (localStorage.getItem('aeryn-theme') === 'light') {
    document.body.classList.add('light');
  }
}

// ── Task Queue Monitor ────────────────────────
async function loadTasks() {
  try {
    const r = await fetch('/shared/tasks/all');
    const d = await r.json();
    const list = document.getElementById('task-list');
    const count = document.getElementById('task-count');
    
    if (!list || !count) return;
    
    count.textContent = d.count;
    
    if (d.count === 0) {
      list.innerHTML = '<div class="task-empty">No pending tasks</div>';
      return;
    }
    
    list.innerHTML = '';
    d.tasks.forEach(task => {
      const item = document.createElement('div');
      item.className = 'task-item';
      const progress = task.progress || 0;
      const statusClass = task.status === 'completed' ? 'success' : 
                          task.status === 'failed' ? 'error' : 'info';
      
      item.innerHTML = `
        <div class="task-dot ${statusClass}"></div>
        <div class="task-info">
          <div class="task-title">${task.title || 'Untitled'}</div>
          <div class="task-status">${task.status} • Priority ${task.priority || 5}</div>
        </div>
        <div class="task-progress">
          <div class="task-progress-fill" style="width: ${progress * 100}%"></div>
        </div>
      `;
      list.appendChild(item);
    });
  } catch(e) {
    console.error('Task load failed:', e);
  }
}

// ── Memory Browser ────────────────────────────
let memoryPage = 1;
const memoryPerPage = 10;
let searchTimeout = null;

async function loadMemory(page = 1) {
  try {
    const r = await fetch(`/vault/entries?page=${page}&per_page=${memoryPerPage}`);
    const d = await r.json();
    const tbody = document.getElementById('memory-table-body');
    const pagination = document.getElementById('memory-pagination');
    
    if (!tbody || !pagination) return;
    
    if (d.entries.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted)">No entries found</td></tr>';
      pagination.innerHTML = '';
      return;
    }
    
    tbody.innerHTML = '';
    d.entries.forEach(entry => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${entry.title?.substring(0, 40) || 'Untitled'}</td>
        <td>${entry.layer || 'wiki'}</td>
        <td>${(entry.tags || []).join(', ')}</td>
        <td><button class="view-btn" onclick="viewEntry('${entry.id}')">View</button></td>
      `;
      tbody.appendChild(tr);
    });
    
    // Pagination
    pagination.innerHTML = '';
    if (d.total_pages > 1) {
      const prevBtn = document.createElement('button');
      prevBtn.textContent = '← Prev';
      prevBtn.disabled = page <= 1;
      prevBtn.onclick = () => loadMemory(page - 1);
      
      const pageInfo = document.createElement('span');
      pageInfo.className = 'page-info';
      pageInfo.textContent = `Page ${page} of ${d.total_pages}`;
      
      const nextBtn = document.createElement('button');
      nextBtn.textContent = 'Next →';
      nextBtn.disabled = page >= d.total_pages;
      nextBtn.onclick = () => loadMemory(page + 1);
      
      pagination.appendChild(prevBtn);
      pagination.appendChild(pageInfo);
      pagination.appendChild(nextBtn);
    }
  } catch(e) {
    console.error('Memory load failed:', e);
  }
}

async function viewEntry(id) {
  try {
    const r = await fetch(`/vault/entry/${id}`);
    const entry = await r.json();
    
    const modal = document.getElementById('memory-modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');
    
    if (!modal || !title || !body) return;
    
    title.textContent = entry.title || 'Untitled';
    body.textContent = entry.body || 'No content';
    
    modal.style.display = 'flex';
  } catch(e) {
    console.error('Entry load failed:', e);
  }
}

function closeModal() {
  const modal = document.getElementById('memory-memory');
  if (modal) modal.style.display = 'none';
}

// ── Search Box ────────────────────────────────
function setupSearch() {
  const input = document.getElementById('memory-search');
  const results = document.getElementById('search-results');
  
  if (!input || !results) return;
  
  input.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    const q = input.value.trim();
    
    if (q.length < 2) {
      results.classList.remove('active');
      return;
    }
    
    searchTimeout = setTimeout(async () => {
      try {
        const r = await fetch(`/vault/search?q=${encodeURIComponent(q)}&limit=10`);
        const d = await r.json();
        
        results.innerHTML = '';
        
        if (d.results.length === 0) {
          results.innerHTML = '<div class="search-result-item">No results</div>';
        } else {
          d.results.forEach(item => {
            const div = document.createElement('div');
            div.className = 'search-result-item';
            div.textContent = item.title;
            div.onclick = () => {
              results.classList.remove('active');
              viewEntry(item.id);
            };
            results.appendChild(div);
          });
        }
        
        results.classList.add('active');
      } catch(e) {
        console.error('Search failed:', e);
      }
    }, 300);
  });
  
  input.addEventListener('blur', () => {
    setTimeout(() => results.classList.remove('active'), 200);
  });
  
  input.addEventListener('focus', () => {
    if (input.value.trim().length >= 2) {
      results.classList.add('active');
    }
  });
}

// ── Keyboard Shortcuts ────────────────────────
function setupKeyboard() {
  document.addEventListener('keydown', (e) => {
    // R - Refresh
    if (e.key === 'r' && !e.ctrlKey && !e.metaKey && !e.altKey) {
      if (document.activeElement.tagName !== 'INPUT') {
        loadTasks();
        loadMemory();
        loadVaultData();
        showToast('info', 'Refreshed');
      }
    }
    
    // T - Toggle theme
    if (e.key === 't' && !e.ctrlKey && !e.metaKey && !e.altKey) {
      if (document.activeElement.tagName !== 'INPUT') {
        toggleTheme();
      }
    }
    
    // / - Focus search
    if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault();
      const input = document.getElementById('memory-search');
      if (input) input.focus();
    }
    
    // Esc - Close modal / blur
    if (e.key === 'Escape') {
      closeModal();
      const input = document.getElementById('memory-search');
      if (input && document.activeElement === input) {
        input.blur();
      }
    }
  });
}

// ── Collapsible Sections ──────────────────────
function setupCollapsible() {
  document.querySelectorAll('.section h2').forEach(header => {
    header.style.cursor = 'pointer';
    header.addEventListener('click', () => {
      const section = header.closest('.section');
      if (section.id === 'task-monitor-section' || section.id === 'memory-browser-section') {
        section.classList.toggle('collapsed');
        localStorage.setItem(`aeryn-collapse-${section.id}`, section.classList.contains('collapsed'));
      }
    });
  });
  
  // Restore collapse state
  ['task-monitor-section', 'memory-browser-section'].forEach(id => {
    const section = document.getElementById(id);
    if (section && localStorage.getItem(`aeryn-collapse-${id}`) === 'true') {
      section.classList.add('collapsed');
    }
  });
}

// ── Fetch vault data (one-time) ────────────────
async function loadVaultData() {
  try {
    const r = await fetch('/dashboard/stats');
    const d = await r.json();
    if (d.error) return;
    
    const a = d.aeryn;
    document.getElementById('vault-total').textContent = a.vault_total_entries;
    document.getElementById('search-docs').textContent = a.search_docs;
    document.getElementById('social-ppl').textContent = a.social_people;

    const tbody = document.getElementById('vault-table');
    tbody.innerHTML = '';
    for (const [layer, count] of Object.entries(a.vault_layers)) {
      tbody.innerHTML += '<tr><td>' + layer + '</td><td>' + count + '</td></tr>';
    }
  } catch(e) {
    console.error('Vault load failed:', e);
  }
}

// ── Live Logs Viewer ──────────────────────────
const logViewer = document.getElementById('log-viewer');
let logLines = [];

function addLogLine(level, message) {
  if (!logViewer) return;
  
  const entry = document.createElement('div');
  entry.className = 'log-entry';
  entry.innerHTML = `
    <span class="log-time">${new Date().toLocaleTimeString('id-ID', {hour12:false})}</span>
    <span class="log-level ${level}">${level}</span>
    <span class="log-message">${message}</span>
  `;
  
  logViewer.appendChild(entry);
  
  // Keep max 50 lines
  while (logViewer.children.length > 50) {
    logViewer.removeChild(logViewer.firstChild);
  }
  
  // Auto-scroll
  logViewer.scrollTop = logViewer.scrollHeight;
}

// SSE for logs
function connectLogStream() {
  const evtSource = new EventSource('/dashboard/stream');
  
  evtSource.addEventListener('log', function(e) {
    const data = JSON.parse(e.data);
    addLogLine(data.level || 'info', data.message);
  });
  
  return evtSource;
}

// ── Error Handling + Fallback ─────────────────
let sseRetries = 0;
const maxSseRetries = 3;
let fallbackToPolling = false;

function startFallbackPolling() {
  if (fallbackToPolling) return;
  fallbackToPolling = true;
  showToast('warning', 'Using fallback polling mode');
  
  setInterval(async () => {
    try {
      const r = await fetch('/dashboard/stats');
      const d = await r.json();
      if (!d.error && d.system) {
        const s = d.system;
        document.getElementById('mem').innerHTML = s.memory_used_mb + '<span class="unit">MB</span>';
        document.getElementById('mem-detail').textContent = s.memory_percent + '% of ' + s.memory_total_mb + ' MB';
        const memBar = document.getElementById('mem-bar');
        memBar.style.width = s.memory_percent + '%';
        memBar.className = 'progress-fill' + (s.memory_percent > 85 ? ' warn' : '') + (s.memory_percent > 95 ? ' danger' : '');
        
        document.getElementById('disk').innerHTML = s.disk_free_gb + '<span class="unit">GB</span>';
        document.getElementById('disk-detail').textContent = s.disk_percent + '% used';
        const diskBar = document.getElementById('disk-bar');
        diskBar.style.width = s.disk_percent + '%';
        diskBar.className = 'progress-fill' + (s.disk_percent > 85 ? ' warn' : '') + (s.disk_percent > 95 ? ' danger' : '');
        
        document.getElementById('proc-mem').innerHTML = s.process_mem_mb + '<span class="unit">MB</span>';
        const hrs = Math.floor(s.uptime_s / 3600);
        const mins = Math.floor((s.uptime_s % 3600) / 60);
        document.getElementById('uptime').textContent = hrs + 'h ' + mins + 'm uptime';
        
        document.getElementById('req-total').textContent = s.requests_total;
        document.getElementById('err-detail').textContent = s.errors_total + ' errors';
      }
    } catch(e) {
      console.error('Fallback poll failed:', e);
    }
  }, 5000);
}

// ── Offline Detection ─────────────────────────
window.addEventListener('offline', () => {
  document.body.classList.add('offline');
  document.getElementById('offline-banner').style.display = 'block';
});

window.addEventListener('online', () => {
  document.body.classList.remove('offline');
  document.getElementById('offline-banner').style.display = 'none';
  showToast('success', 'Connection restored');
});

// ── Card Expand ───────────────────────────────
function setupCardExpand() {
  document.querySelectorAll('.card').forEach(card => {
    card.classList.add('expandable');
    card.addEventListener('click', () => {
      const label = card.querySelector('.label')?.textContent || 'Detail';
      const value = card.querySelector('.value')?.textContent || '';
      const detail = card.querySelector('.detail')?.textContent || '';
      
      const modal = document.getElementById('memory-modal');
      const title = document.getElementById('modal-title');
      const body = document.getElementById('modal-body');
      
      if (modal && title && body) {
        title.textContent = label;
        body.innerHTML = `<strong>${value}</strong><br><br>${detail}`;
        modal.style.display = 'flex';
      }
    });
  });
}

// ── Performance: Throttle sparkline redraw ────
let sparklineThrottle = null;

function throttledSparklineUpdate() {
  if (sparklineThrottle) return;
  sparklineThrottle = setTimeout(() => {
    sparklineThrottle = null;
  }, 1000); // Max 1 update per second
}

// ── Init ──────────────────────────────────────
loadTheme();
updateClock();
setInterval(updateClock, 1000);
connectSSE();
connectWS();
connectLogStream();
loadVaultData();
loadTasks();
loadMemory();
setupSearch();
setupKeyboard();
setupCollapsible();
setupCardExpand();
setInterval(loadTasks, 30000);
setInterval(loadMemory, 60000); // Refresh vault data every 60s
</script>
</body>
</html>"""

@app.get("/dashboard/stats")
async def dashboard_stats():
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        mem_total = mem_available = 0
        for line in lines:
            if line.startswith("MemTotal:"): mem_total = int(line.split()[1])
            elif line.startswith("MemAvailable:"): mem_available = int(line.split()[1])
        mem_used_mb = (mem_total - mem_available) / 1024 if mem_total else 0
        mem_total_mb = mem_total / 1024 if mem_total else 0
        mem_pct = round(mem_used_mb / mem_total_mb * 100, 1) if mem_total_mb else 0
        import shutil
        disk = shutil.disk_usage("/")
        process_mem = 0
        try:
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"): process_mem = int(line.split()[1]) / 1024; break
        except Exception: pass
        vault = AerynVault()
        vault_counts = vault.count_entries()
        total_vault = sum(vault_counts.values())
        hse = get_search_engine()
        doc_count = hse._doc_count if hasattr(hse, '_doc_count') else 0
        sm = SocialMemory()
        person_count = len(sm._data.get("people", {})) if hasattr(sm, '_data') else 0
        return {"timestamp": time.time(), "system": {"memory_total_mb": round(mem_total_mb, 1), "memory_used_mb": round(mem_used_mb, 1), "memory_percent": mem_pct, "disk_free_gb": round(disk.free / (1024**3), 2), "disk_percent": round((disk.total - disk.free) / disk.total * 100, 1), "process_mem_mb": round(process_mem, 1), "uptime_s": round(time.time() - _start_time, 0)}, "aeryn": {"vault_total_entries": total_vault, "vault_layers": vault_counts, "search_docs": doc_count, "social_people": person_count, "requests_total": _request_count, "errors_total": _error_count, "safety_engine": True}}
    except Exception as e:
        return {"error": str(e)}

@app.get("/shared/reminders/due")
async def get_due_reminders():
    db = get_shared_db()
    reminders = db.get_due_reminders()
    return {"reminders": reminders, "count": len(reminders)}

@app.get("/shared/reminders")
async def get_all_reminders():
    db = get_shared_db()
    reminders = db.get_all_reminders()
    return {"reminders": reminders, "count": len(reminders)}

@app.post("/shared/reminders/add")
async def add_reminder(text: str, when: str, source: str = "n8n", target: str = "all"):
    db = get_shared_db()
    rid = db.add_reminder(text, when, source, target)
    return {"id": rid, "status": "ok"}

@app.post("/shared/reminders/mark-sent")
async def mark_reminder_sent(reminder_id: str):
    db = get_shared_db()
    db.mark_reminder_sent(reminder_id)
    return {"status": "ok"}

@app.get("/shared/tasks")
async def get_pending_tasks():
    db = get_shared_db()
    tasks = db.get_pending_tasks()
    return {"tasks": tasks, "count": len(tasks)}

@app.get("/shared/tasks/all")
async def get_all_tasks():
    db = get_shared_db()
    tasks = db.get_all_tasks()
    return {"tasks": tasks, "count": len(tasks)}

@app.get("/vault/entries")
async def get_vault_entries(layer: str = None, page: int = 1, per_page: int = 10):
    """Get vault entries with pagination."""
    vault = AerynVault()
    entries = vault.list_entries(layer=layer, limit=per_page, offset=(page - 1) * per_page)
    counts = vault.count_entries()
    total = counts.get(layer, sum(counts.values())) if layer else sum(counts.values())
    return {
        "entries": entries,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }

@app.get("/vault/entry/{entry_id}")
async def get_vault_entry(entry_id: str):
    """Get single vault entry."""
    vault = AerynVault()
    entry = vault.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@app.get("/vault/search")
async def search_vault(q: str, limit: int = 10):
    """Search vault entries."""
    vault = AerynVault()
    results = vault.search(q, limit=limit)
    return {"results": results, "count": len(results)}

@app.post("/shared/tasks/add")
async def add_task(title: str, description: str = "", priority: int = 5):
    db = get_shared_db()
    tid = db.add_task(title, description, priority)
    return {"id": tid, "status": "ok"}

@app.post("/shared/tasks/update")
async def update_task(task_id: str, status: str = None, progress: float = None, result: str = None, error: str = None):
    db = get_shared_db()
    db.update_task(task_id, status, progress, result, error)
    return {"status": "ok"}

# ── Notification Endpoints ─────────────────────

@app.post("/notifications/create")
async def create_notification(user_id: str, title: str, message: str,
                               scheduled_for: str = None, priority: str = "normal",
                               channel: str = "all", metadata: dict = None):
    manager = get_notification_manager()
    notif = Notification(user_id=user_id, title=title, message=message,
                         scheduled_for=scheduled_for, priority=priority,
                         channel=channel, metadata=metadata)
    nid = manager.create(notif)
    return {"id": nid, "status": "created"}

@app.get("/notifications/due")
async def get_due_notifications(user_id: str = None, limit: int = 10):
    manager = get_notification_manager()
    return {"notifications": manager.get_due(user_id, limit)}

@app.get("/notifications/pending")
async def get_pending_notifications(user_id: str = None):
    manager = get_notification_manager()
    return {"notifications": manager.get_pending(user_id)}

@app.post("/notifications/cancel")
async def cancel_notification(notification_id: str):
    manager = get_notification_manager()
    success = manager.cancel(notification_id)
    return {"success": success}

@app.post("/search/index")
async def index_vault(force: bool = False):
    """Index all vault entries into semantic search."""
    indexer = get_semantic_indexer()
    result = indexer.index_vault(force=force)
    return result

@app.get("/search/advanced")
async def advanced_search(q: str, limit: int = 10):
    """Semantic search across indexed documents."""
    indexer = get_semantic_indexer()
    results = indexer.search(q, limit=limit)
    return {"query": q, "results": results, "count": len(results)}

@app.get("/search/stats")
async def search_stats():
    """Get semantic search statistics."""
    indexer = get_semantic_indexer()
    return indexer.get_stats()

# ── Error Recovery Endpoints ──────────────────

@app.get("/errors/recovery/stats")
async def error_recovery_stats():
    """Get error recovery statistics."""
    recovery = get_error_recovery()
    return recovery.get_stats()

@app.get("/errors/recovery/log")
async def error_log(limit: int = 50):
    """Get recent error log."""
    recovery = get_error_recovery()
    return {"errors": recovery.get_error_log(limit)}

@app.get("/errors/recovery/circuit-breakers")
async def circuit_breaker_states():
    """Get circuit breaker states."""
    recovery = get_error_recovery()
    return {"circuit_breakers": recovery.get_circuit_breaker_states()}

# ── Tool Runtime Endpoints ────────────────────

@app.get("/tools/list")
async def list_tools():
    """List available tools."""
    runtime = get_tool_runtime()
    return {"tools": runtime.list_tools()}

@app.post("/tools/execute")
async def execute_tool(tool: str, params: dict = None):
    """Execute a tool natively."""
    runtime = get_tool_runtime()
    result = await runtime.execute(tool, params or {})
    return result.to_dict()

# ── Background Task Queue Endpoints ───────────

@app.post("/queue/submit")
async def submit_task(name: str, tool: str, params: dict = None):
    """Submit a task to the background queue."""
    queue = get_task_queue()
    runtime = get_tool_runtime()
    
    async def task_wrapper():
        return await runtime.execute(tool, params or {})
    
    task_id = await queue.submit(name, task_wrapper)
    return {"task_id": task_id, "status": "submitted"}

@app.get("/queue/task/{task_id}")
async def get_task_status(task_id: str):
    """Get task status."""
    queue = get_task_queue()
    task = queue.get_task(task_id)
    return task or {"error": "Task not found"}

@app.get("/queue/tasks")
async def list_queue_tasks():
    """List all tasks."""
    queue = get_task_queue()
    return {"tasks": queue.get_all_tasks()}

@app.get("/queue/stats")
async def queue_stats():
    """Get queue statistics."""
    queue = get_task_queue()
    return {
        "pending": queue.get_pending_count(),
        "running": queue.get_running_count(),
    }

# ── Proactive Engine Endpoints ────────────────

@app.get("/proactive/suggestions")
async def get_suggestions(user_id: str = "default"):
    """Get proactive suggestions."""
    engine = get_proactive_engine()
    return {"suggestions": engine.get_unread(user_id)}

@app.post("/proactive/generate")
async def generate_suggestions(user_id: str = "default"):
    """Generate new suggestions."""
    engine = get_proactive_engine()
    suggestions = engine.generate_all(user_id)
    return {"suggestions": suggestions}

@app.post("/proactive/mark-read")
async def mark_suggestion_read(suggestion_id: str):
    """Mark suggestion as read."""
    engine = get_proactive_engine()
    engine.mark_read(suggestion_id)
    return {"status": "ok"}

# ── Phase 2 Endpoints ─────────────────────────

@app.post("/briefing/morning")
async def morning_briefing(user_id: str = "default"):
    """Generate morning briefing."""
    briefing = get_daily_briefing()
    return briefing.generate_morning(user_id)

@app.post("/briefing/evening")
async def evening_briefing(user_id: str = "default"):
    """Generate evening briefing."""
    briefing = get_daily_briefing()
    return briefing.generate_evening(user_id)

@app.post("/auto-task/parse")
async def parse_tasks(user_id: str, text: str):
    """Parse natural language into tasks."""
    auto_task = get_auto_task()
    tasks = auto_task.parse(user_id, text)
    return {"tasks": tasks, "count": len(tasks)}

@app.get("/proactive/v2/patterns")
async def detect_patterns(user_id: str = "default"):
    """Detect usage patterns."""
    engine = get_proactive_v2()
    return {"patterns": engine.detect_patterns(user_id)}

@app.get("/proactive/v2/anomalies")
async def detect_anomalies(user_id: str = "default"):
    """Detect anomalies."""
    engine = get_proactive_v2()
    return {"anomalies": engine.detect_anomalies(user_id)}

# ── Phase 3 Endpoints ─────────────────────────

@app.post("/api-keys/create")
async def create_api_key(user_id: str, name: str, permissions: list = None):
    """Create new API key."""
    manager = get_api_key_manager()
    return manager.create(user_id, name, permissions)

@app.get("/api-keys/list")
async def list_api_keys(user_id: str):
    """List user's API keys."""
    manager = get_api_key_manager()
    return {"keys": manager.list_keys(user_id)}

@app.post("/api-keys/revoke")
async def revoke_api_key(key_id: str):
    """Revoke an API key."""
    manager = get_api_key_manager()
    return {"success": manager.revoke(key_id)}

@app.get("/usage/summary")
async def usage_summary(user_id: str = None, days: int = 30):
    """Get usage summary."""
    metering = get_usage_metering()
    return metering.get_summary(user_id, days)

@app.post("/usage/track")
async def track_usage(user_id: str, event_type: str, endpoint: str = None,
                      tokens_input: int = 0, tokens_output: int = 0, cost: float = 0.0):
    """Track a usage event."""
    metering = get_usage_metering()
    metering.track(user_id, event_type, endpoint, tokens_input, tokens_output, cost)
    return {"status": "tracked"}

# ── Auth Endpoints ────────────────────────────

from pydantic import BaseModel, Field

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

@app.post("/auth/register")
async def auth_register(req: RegisterRequest):
    """Register a new user."""
    auth = get_auth()
    user = auth.create_user(req.email, req.password, req.display_name)
    if not user:
        return {"error": "User already exists or invalid data"}
    return {"status": "ok", "user": user}

@app.post("/auth/login")
async def auth_login(req: LoginRequest):
    """Login and get session token."""
    auth = get_auth()
    user = auth.authenticate(req.email, req.password)
    if not user:
        return {"error": "Invalid credentials"}
    token = auth.generate_token(user["id"])
    return {"status": "ok", "token": token, "user": user}

@app.post("/auth/validate")
async def auth_validate(req: TokenRequest):
    """Validate a session token."""
    auth = get_auth()
    user = auth.validate_token(req.token)
    if not user:
        return {"error": "Invalid or expired token"}
    return {"status": "ok", "user": user}

@app.post("/auth/api-keys")
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

@app.post("/billing/track")
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

@app.get("/billing/quota")
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

@app.get("/billing/pricing")
async def pricing():
    """Get pricing info."""
    return {"plans": PLANS, "usage_rates": PRICING}

@app.post("/billing/charge")
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

@app.post("/webhooks/register")
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

@app.delete("/webhooks/unregister")
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

@app.get("/webhooks")
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

@app.get("/plugins")
async def list_plugins(query: str = None, limit: int = 20, offset: int = 0):
    """List public plugins."""
    mp = get_plugin_marketplace()
    return {"plugins": mp.search(query=query, limit=limit, offset=offset)}

@app.post("/plugins/publish")
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

@app.get("/plugins/{plugin_id}")
async def get_plugin(plugin_id: str):
    """Get plugin details."""
    mp = get_plugin_marketplace()
    plugin = mp.get(plugin_id)
    if not plugin:
        return {"error": "Plugin not found"}
    return plugin

@app.post("/plugins/rate")
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

@app.post("/workspaces")
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

@app.get("/workspaces")
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

@app.get("/workspaces/{workspace_id}")
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

@app.put("/workspaces/{workspace_id}")
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

@app.delete("/workspaces/{workspace_id}")
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

@app.get("/workspaces/{workspace_id}/members")
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

@app.post("/workspaces/{workspace_id}/members")
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

@app.delete("/workspaces/{workspace_id}/members/{user_id_to_remove}")
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

@app.post("/workspaces/{workspace_id}/invites")
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

@app.post("/workspaces/invites/{token}/accept")
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

@app.get("/auth/sso/google")
async def google_sso_url():
    """Get Google SSO URL."""
    sso = get_sso_manager()
    return {"url": sso.get_google_auth_url()}

@app.get("/auth/sso/github")
async def github_sso_url():
    """Get GitHub SSO URL."""
    sso = get_sso_manager()
    return {"url": sso.get_github_auth_url()}

@app.get("/auth/callback/google")
async def google_callback(code: str):
    """Google OAuth callback."""
    sso = get_sso_manager()
    result = await sso.handle_google_callback(code)
    if not result:
        return {"error": "Authentication failed"}
    return {"status": "ok", "user": result}

@app.get("/auth/callback/github")
async def github_callback(code: str):
    """GitHub OAuth callback."""
    sso = get_sso_manager()
    result = await sso.handle_github_callback(code)
    if not result:
        return {"error": "Authentication failed"}
    return {"status": "ok", "user": result}

@app.get("/auth/sso/accounts")
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

@app.delete("/auth/sso/{provider}")
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

# ── Admin Dashboard Endpoints ─────────────────

@app.get("/admin/users")
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

@app.get("/admin/stats")
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

@app.get("/admin/compliance/report")
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

@app.get("/admin/compliance/regions")
async def data_residency_regions(authorization: str = Header(None)):
    """Get available data residency regions."""
    soc2 = get_soc2_compliance()
    return {"regions": soc2.get_data_residency_regions()}

@app.post("/admin/compliance/cleanup")
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

@app.post("/auth/forgot-password")
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

@app.post("/auth/reset-password")
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

@app.post("/auth/verify-email")
async def verify_email(req: VerifyEmailRequest):
    """Verify email with token."""
    ev = get_email_verification()
    
    result = ev.verify_token(req.token)
    if not result:
        return {"error": "Invalid or expired token"}
    
    return {"status": "ok", "message": "Email verified"}

@app.post("/auth/resend-verification")
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

@app.post("/secrets/set")
async def set_secret(user_id: str, name: str, value: str, description: str = None):
    """Store a secret."""
    sm = get_secrets_manager()
    sm.set(user_id, name, value, description)
    return {"status": "stored"}

@app.get("/secrets/get")
async def get_secret(user_id: str, name: str):
    """Get a secret."""
    sm = get_secrets_manager()
    value = sm.get(user_id, name)
    return {"value": value} if value else {"error": "Not found"}

@app.get("/secrets/list")
async def list_secrets(user_id: str):
    """List user's secrets."""
    sm = get_secrets_manager()
    return {"secrets": sm.list(user_id)}

@app.get("/plugins/list")
async def list_plugins():
    """List installed plugins."""
    rt = get_plugin_runtime()
    return {"plugins": rt.list_plugins()}

@app.post("/plugins/run")
async def run_plugin(plugin_name: str, action: str, params: dict = None):
    """Run a plugin."""
    rt = get_plugin_runtime()
    return rt.run_plugin(plugin_name, action, params)

# ── Phase 4 Endpoints ─────────────────────────

@app.get("/performance/stats")
async def performance_stats():
    """Get performance statistics."""
    opt = get_optimizer()
    return opt.get_system_stats()

@app.get("/uptime")
async def uptime():
    """Get uptime information."""
    ut = get_uptime()
    return {
        "uptime_s": ut.uptime_seconds,
        "uptime": ut.uptime_formatted,
        "restart_count": ut._restart_count,
    }

@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check."""
    ut = get_uptime()
    return ut.health_check()

@app.get("/docs/swagger")
async def swagger_ui():
    """Serve Swagger UI."""
    from fastapi.openapi.docs import get_swagger_ui_html
    from fastapi.responses import HTMLResponse
    html = get_swagger_ui_html(openapi_url="/openapi.json", title="Aeryn API")
    return HTMLResponse(content=html.body.decode())

@app.get("/openapi.json")
async def openapi_schema():
    """Serve OpenAPI schema."""
    from fastapi.openapi.utils import get_openapi
    return get_openapi(
        title="Aeryn API",
        version="41.0",
        description="Aeryn Cognitive Agent Platform API",
        routes=app.routes,
    )

@app.get("/shared/daily-log")
async def get_daily_log():
    db = get_shared_db()
    return db.get_or_create_daily_log()

@app.post("/shared/daily-log/update")
async def update_daily_log(date: str = None, **kwargs):
    db = get_shared_db()
    db.update_daily_log(date, **kwargs)
    return {"status": "ok"}

@app.get("/shared/stats")
async def get_stats():
    db = get_shared_db()
    return db.get_stats()

@app.post("/dream/synthesize")
async def dream_synthesize(user_id: str = "default", days: int = 7):
    synthesizer = get_dream_synthesizer()
    return synthesizer.synthesize(user_id, days)

@app.get("/dream/insights")
async def get_dream_insights(user_id: str = "default", limit: int = 20):
    synthesizer = get_dream_synthesizer()
    return synthesizer.get_insights(user_id, limit)

@app.post("/memory/extract-entities")
async def extract_entities(text: str):
    extractor = get_entity_extractor()
    return extractor.extract(text)

@app.post("/memory/preference/learn")
async def learn_preference(user_id: str, category: str, key: str, value: str, confidence: float = 0.5):
    learner = get_preference_learner()
    learner.learn(user_id, category, key, value, confidence)
    return {"status": "ok"}

@app.get("/memory/preferences/{user_id}")
async def get_preferences(user_id: str, min_confidence: float = 0.0):
    learner = get_preference_learner()
    return learner.get_preferences(user_id, min_confidence)

@app.get("/guardrails/validators")
async def list_validators(category: str = None):
    guardrails = get_enhanced_guardrails()
    if category: return {"validators": guardrails.get_validators_by_category(category)}
    return {"validators": guardrails.get_all_validators()}

@app.post("/guardrails/validate-input")
async def validate_input(text: str = None, context: str = "general", body: dict = None):
    if body and not text:
        text = body.get("text", "")
        context = body.get("context", "general")
    guardrails = get_enhanced_guardrails()
    result = guardrails.validate_input(text, context)
    return {"valid": result.valid, "risk": result.risk, "issues": result.issues, "fallback": result.fallback}

@app.post("/guardrails/validate-output")
async def validate_output(text: str = None, expected_format: str = "text", body: dict = None):
    if body and not text:
        text = body.get("text", "")
        expected_format = body.get("expected_format", "text")
    guardrails = get_enhanced_guardrails()
    result = guardrails.validate_output(text, expected_format)
    return {"valid": result.valid, "risk": result.risk, "issues": result.issues, "sanitized": result.sanitized, "fallback": result.fallback}

@app.post("/sandbox/create")
async def create_sandbox(user_id: str = "default", allow_network: bool = False, max_time: int = 30):
    sandbox = get_enhanced_sandbox()
    limits = SandboxLimits(max_execution_time=max_time, allow_network=allow_network)
    session_id = sandbox.create_session(user_id=user_id, limits=limits)
    return {"session_id": session_id, "status": "created"}

@app.post("/sandbox/execute")
async def sandbox_execute(session_id: str, command: str, user_id: str = "default"):
    sandbox = get_enhanced_sandbox()
    return sandbox.execute(session_id, command, user_id)

@app.get("/sandbox/session/{session_id}")
async def get_sandbox_session(session_id: str):
    sandbox = get_enhanced_sandbox()
    info = sandbox.get_session_info(session_id)
    history = sandbox.audit.get_session_history(session_id)
    return {"info": info, "history": history}

@app.delete("/sandbox/session/{session_id}")
async def cleanup_sandbox(session_id: str):
    sandbox = get_enhanced_sandbox()
    sandbox.cleanup_session(session_id)
    return {"status": "cleaned"}

@app.post("/agents/register")
async def register_agent(name: str, role: str = "worker", capabilities: str = "[]"):
    orchestrator = get_multi_agent_orchestrator()
    caps = json.loads(capabilities) if capabilities.startswith("[") else []
    try: agent_role = AgentRole(role)
    except ValueError: agent_role = AgentRole.WORKER
    agent_id = orchestrator.register_agent(name, agent_role, caps)
    return {"agent_id": agent_id, "status": "registered"}

@app.get("/agents")
async def list_agents():
    orchestrator = get_multi_agent_orchestrator()
    return {"agents": orchestrator.get_active_agents()}

@app.post("/agents/tasks/create")
async def create_agent_task(title: str, description: str = "", assigned_to: str = None, assigned_by: str = None, priority: int = 5):
    orchestrator = get_multi_agent_orchestrator()
    try: task_priority = AgentTaskPriority(priority)
    except ValueError: task_priority = AgentTaskPriority.MEDIUM
    task_id = orchestrator.create_task(title, description, assigned_to, assigned_by, task_priority)
    return {"task_id": task_id, "status": "created"}

@app.get("/agents/tasks")
async def list_agent_tasks(status: str = None):
    orchestrator = get_multi_agent_orchestrator()
    return {"tasks": orchestrator.get_tasks(status=status)}

@app.post("/memory/decay")
async def run_decay(user_id: str = "default"):
    engine = get_memory_decay_engine()
    return engine.decay_all(user_id)

@app.get("/memory/decay/stats")
async def get_decay_stats():
    engine = get_memory_decay_engine()
    return engine.get_decay_stats()

@app.post("/memory/entities/register")
async def register_entity(name: str, entity_type: str, properties: str = "{}"):
    resolver = get_entity_resolver()
    props = json.loads(properties)
    entity_id = resolver.register_entity(name, entity_type, props)
    return {"entity_id": entity_id}

@app.get("/memory/entities/resolve")
async def resolve_entity(name: str, entity_type: str = None):
    resolver = get_entity_resolver()
    result = resolver.resolve(name, entity_type)
    return {"entity": result}

@app.get("/memory/entities")
async def list_entities(entity_type: str = None):
    resolver = get_entity_resolver()
    return {"entities": resolver.get_all_entities(entity_type)}

@app.post("/plugins/install")
async def install_plugin(source_dir: str):
    manager = get_plugin_manager()
    plugin = manager.install_plugin(source_dir)
    if plugin: return {"status": "installed", "plugin": plugin.name}
    return {"status": "error", "error": "Failed to install plugin"}

@app.get("/plugins/installed")
async def list_plugins():
    manager = get_plugin_manager()
    return {"plugins": manager.list_plugins()}

@app.delete("/plugins/{name}")
async def uninstall_plugin(name: str):
    manager = get_plugin_manager()
    if manager.uninstall_plugin(name): return {"status": "uninstalled"}
    return {"status": "error", "error": "Plugin not found"}

@app.post("/security/scan")
async def security_scan(text: str, context: str = "general"):
    security = get_owasp_security()
    return security.scan(text, context)

@app.get("/security/controls")
async def list_controls():
    security = get_owasp_security()
    return {"controls": list(security._controls.keys())}

@app.get("/discord/commands")
async def discord_commands():
    from aeryn_core.platform.discord_bot import DiscordBotHandler
    handler = DiscordBotHandler()
    return {"commands": handler.get_commands()}

@app.post("/discord/interaction")
async def discord_interaction(interaction: dict):
    from aeryn_core.platform.discord_bot import DiscordBotHandler
    handler = DiscordBotHandler()
    result = await handler.handle_interaction(interaction)
    return result

@app.post("/planning/tasks/create")
async def create_plan(title: str, description: str = "", priority: int = 5):
    planner = get_long_horizon_planner()
    try: task_priority = TaskPriority(priority)
    except ValueError: task_priority = TaskPriority.MEDIUM
    task_id = planner.create_task(title, description, task_priority)
    return {"task_id": task_id}

@app.post("/planning/tasks/{task_id}/decompose")
async def decompose_task(task_id: str, subtasks: list):
    planner = get_long_horizon_planner()
    subtask_ids = planner.decompose_task(task_id, subtasks)
    return {"subtask_ids": subtask_ids}

@app.post("/planning/tasks/{task_id}/execute")
async def execute_plan(task_id: str):
    planner = get_long_horizon_planner()
    result = planner.execute_task(task_id)
    return result

@app.get("/planning/tasks/{task_id}")
async def get_task(task_id: str):
    planner = get_long_horizon_planner()
    task = planner.get_task(task_id)
    subtasks = planner.get_subtasks(task_id)
    return {"task": task, "subtasks": subtasks}

@app.get("/planning/tasks")
async def list_plans(status: str = None):
    planner = get_long_horizon_planner()
    return {"tasks": planner.get_all_tasks(status)}

@app.post("/temporal/store")
async def store_temporal(user_id: str, memory_type: str, title: str, content: str, timestamp: str = None):
    temporal = get_temporal_memory()
    mem_id = temporal.store(user_id, memory_type, title, content, timestamp)
    return {"memory_id": mem_id}

@app.get("/temporal/query")
async def temporal_query(user_id: str, query: str):
    temporal = get_temporal_memory()
    return temporal.query_time(user_id, query)

@app.get("/temporal/timeline/{user_id}")
async def get_timeline(user_id: str, days: int = 30):
    temporal = get_temporal_memory()
    return {"timeline": temporal.get_timeline(user_id, days)}

@app.get("/temporal/trends/{user_id}")
async def get_trends(user_id: str, days: int = 30):
    temporal = get_temporal_memory()
    return {"trends": temporal.detect_trends(user_id, days)}

@app.post("/improvement/feedback")
async def submit_feedback(user_id: str, interaction_type: str, input_text: str, output_text: str, rating: int = None, feedback_text: str = ""):
    engine = get_self_improvement_engine()
    fid = engine.feedback.record_interaction(user_id, interaction_type, input_text, output_text)
    if rating is not None: engine.feedback.submit_feedback(fid, rating, feedback_text)
    return {"feedback_id": fid, "status": "recorded"}

@app.get("/improvement/report")
async def get_improvement_report(user_id: str = "default"):
    engine = get_self_improvement_engine()
    return engine.get_improvement_report(user_id)

@app.post("/skills/detect-patterns")
async def detect_patterns(user_id: str = "default", min_frequency: int = 3):
    crystallizer = get_skill_crystallizer()
    patterns = crystallizer.detector.get_frequent_patterns(user_id, min_frequency)
    return {"patterns": patterns}

@app.post("/skills/crystallize")
async def crystallize_skill(user_id: str, pattern_id: str, skill_name: str, description: str = ""):
    crystallizer = get_skill_crystallizer()
    skill_id = crystallizer.crystallize(user_id, pattern_id, skill_name, description)
    return {"skill_id": skill_id}

@app.get("/skills")
async def list_skills(active_only: bool = True):
    crystallizer = get_skill_crystallizer()
    return {"skills": crystallizer.get_skills(active_only=active_only)}

@app.post("/sync/backup")
async def create_backup(backup_name: str = None):
    sync = get_cloud_sync()
    return sync.create_backup(backup_name)

@app.get("/sync/backups")
async def list_backups():
    sync = get_cloud_sync()
    return {"backups": sync.list_backups()}

@app.post("/sync/restore")
async def restore_backup(backup_name: str, dry_run: bool = False):
    sync = get_cloud_sync()
    return sync.restore_backup(backup_name, dry_run)

@app.get("/constitutional/principles")
async def get_principles():
    cai = get_constitutional_ai()
    conn = sqlite3.connect(cai.db_path)
    rows = conn.execute("SELECT id, name, description, priority FROM principles WHERE is_active=1 ORDER BY priority DESC").fetchall()
    conn.close()
    return {"principles": [{"id": r[0], "name": r[1], "description": r[2], "priority": r[3]} for r in rows]}

@app.post("/constitutional/check")
async def constitutional_check(action: str, context: str = ""):
    cai = get_constitutional_ai()
    return cai.check_action(action, context)

@app.post("/emotion/detect")
async def detect_emotion(text: str, user_id: str = "default"):
    ei = get_emotional_intelligence()
    result = ei.detect_mood(text)
    ei.record_mood(user_id, text)
    result["empathy_response"] = ei.get_empathy_response(result["mood"])
    return result

@app.post("/telegram/webhook")
async def telegram_webhook(update: dict):
    bot = get_telegram_bot()
    return bot.handle_update(update)

@app.get("/telegram/commands")
async def telegram_commands():
    bot = get_telegram_bot()
    return {"commands": bot.get_commands()}

@app.post("/email/triage")
async def email_triage(sender: str, subject: str, body: str):
    agent = get_email_agent()
    return agent.triage_email(sender, subject, body)

@app.post("/email/generate-reply")
async def email_reply(sender: str, subject: str, body: str):
    agent = get_email_agent()
    return {"reply": agent.generate_reply(sender, subject, body)}

@app.post("/calendar/events")
async def create_event(user_id: str, title: str, start_time: str, end_time: str = None, description: str = "", location: str = ""):
    cal = get_calendar()
    event_id = cal.create_event(user_id, title, start_time, end_time, description, location)
    return {"event_id": event_id}

@app.get("/calendar/events/{user_id}")
async def get_events(user_id: str, start: str = None, end: str = None):
    cal = get_calendar()
    return {"events": cal.get_events(user_id, start, end)}

@app.get("/github/status")
async def github_status():
    gh = get_github()
    return {"status": "ready", "token": "configured" if gh.token else "not set"}

@app.post("/encrypt")
async def encrypt_data(data: str):
    enc = get_encryption()
    return {"encrypted": enc.encrypt(data)}

@app.post("/decrypt")
async def decrypt_data(encrypted_data: str):
    enc = get_encryption()
    return {"decrypted": enc.decrypt(encrypted_data)}

@app.post("/auth/register")
async def register_user(username: str, password: str, role: str = "user"):
    auth = get_auth()
    user_id = auth.create_user(username, password, role)
    return {"user_id": user_id, "status": "created"}

@app.post("/auth/login")
async def login(username: str, password: str):
    auth = get_auth()
    token = auth.authenticate(username, password)
    return {"token": token, "status": "success" if token else "failed"}

@app.get("/metrics")
async def get_metrics():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from monitor import ProductionMonitor
    monitor = ProductionMonitor()
    return monitor.get_metrics()

@app.get("/alerts")
async def get_alerts():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from monitor import ProductionMonitor
    monitor = ProductionMonitor()
    return {"alerts": monitor.get_alerts()}


# ── Browser Automation ──────────────────────────────────────────

@app.post("/browser/task")
async def browser_task(url: str, actions: list, user_id: str = "default"):
    from aeryn_core.platform.browser_vector import get_browser
    browser = get_browser()
    return browser.run_task(url, actions, user_id)

# ── Vector DB ──────────────────────────────────────────────────

@app.post("/vectordb/collections")
async def create_collection(name: str, dimension: int = 384, description: str = ""):
    from aeryn_core.platform.browser_vector import get_vector_db
    vdb = get_vector_db()
    return {"collection": vdb.create_collection(name, dimension, description)}

@app.post("/vectordb/{collection}/add")
async def add_vectors(collection: str, texts: list, embeddings: list = None, metadatas: list = None):
    from aeryn_core.platform.browser_vector import get_vector_db
    vdb = get_vector_db()
    ids = vdb.add(collection, texts, embeddings, metadatas)
    return {"ids": ids}

@app.post("/vectordb/{collection}/search")
async def search_vectors(collection: str, query_embedding: list, limit: int = 5):
    from aeryn_core.platform.browser_vector import get_vector_db
    vdb = get_vector_db()
    return {"results": vdb.search(collection, query_embedding, limit)}

@app.delete("/vectordb/{collection}")
async def delete_collection(collection: str):
    from aeryn_core.platform.browser_vector import get_vector_db
    vdb = get_vector_db()
    vdb.delete_collection(collection)
    return {"status": "deleted"}


# ── Monitoring Endpoints ──────────────────────

@app.get("/api/monitoring/sessions")
async def monitoring_sessions():
    """Get all chat sessions."""
    try:
        from pathlib import Path
        import sqlite3
        db_path = Path("Personalisasi/Database/conversations.db")
        if not db_path.exists():
            return {"sessions": []}
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT session_id, COUNT(*) as messages, MAX(created_at) as last_active "
            "FROM conversations GROUP BY session_id ORDER BY last_active DESC LIMIT 50"
        ).fetchall()
        conn.close()
        return {"sessions": [dict(r) for r in rows]}
    except Exception as e:
        return {"sessions": [], "error": str(e)}

@app.get("/api/monitoring/history")
async def monitoring_history(session_id: str, limit: int = 50):
    """Get conversation history for a session."""
    try:
        from pathlib import Path
        import sqlite3
        db_path = Path("Personalisasi/Database/conversations.db")
        if not db_path.exists():
            return {"session_id": session_id, "history": []}
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT role, content, reasoning, created_at FROM conversations "
            "WHERE session_id = ? ORDER BY id ASC LIMIT ?",
            (session_id, limit)
        ).fetchall()
        conn.close()
        return {"session_id": session_id, "history": [dict(r) for r in rows]}
    except Exception as e:
        return {"session_id": session_id, "history": [], "error": str(e)}

@app.get("/api/adaptive/health")
async def adaptive_health():
    """Get adaptive system health report."""
    try:
        system = get_adaptive_system()
        return system.get_health_report()
    except Exception as e:
        return {"error": str(e), "status": "unknown"}


@app.get("/api/adaptive/errors")
async def adaptive_errors(hours: int = 24):
    """Get adaptive error summary."""
    try:
        system = get_adaptive_system()
        return system.get_error_summary(hours)
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/adaptive/adaptations")
async def adaptive_adaptations(hours: int = 24):
    """Get adaptive adaptation summary."""
    try:
        system = get_adaptive_system()
        return system.get_adaptation_summary(hours)
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/adaptive/run-cycle")
async def adaptive_run_cycle():
    """Manually run a self-improvement cycle."""
    try:
        system = get_adaptive_system()
        return system.run_self_improvement_cycle()
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/monitoring/stats")
async def monitoring_stats():
    """Get monitoring statistics."""
    try:
        router = get_mode_router()
        llm = router.llm
        return {
            "total_requests": llm._request_count,
            "total_errors": llm._error_count,
            "active_sessions": len(router.sessions),
            "mode": router.mode,
        }
    except Exception as e:
        return {"error": str(e)}


# Dashboard web routes
from apps.web.server import router as dashboard_router
app.include_router(dashboard_router, prefix="/web")

# SPA routes — serve dashboard HTML for client-side routing routes
@app.get("/", response_class=HTMLResponse)
async def spa_root():
    """Serve dashboard HTML for client-side routing pages."""
    from apps.web.server import _serve_dashboard
    return _serve_dashboard()

# Redirect all old SPA routes to single dashboard
for _route in ["/projects", "/workspaces", "/chat", "/audit", "/settings", "/notifications"]:
    def make_redirect():
        async def redirect():
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/")
        return redirect
    _handler = make_redirect()
    _handler.__name__ = f"redirect_{_route.strip('/')}"
    app.add_api_route(_route, endpoint=_handler)

@app.get("/app/{spa:path}", response_class=HTMLResponse)
async def spa_fallback(spa: str):
    """Serve dashboard HTML for client-side routing routes."""
    SPA_ROUTES = {"/", "/projects", "/workspaces", "/chat", "/plugins", "/audit", "/settings", "/notifications"}
    from apps.web.server import _serve_dashboard
    if "/" + spa in SPA_ROUTES:
        return _serve_dashboard()
    return JSONResponse({"error": "Not found"}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    ensure_dirs()
    uvicorn.run(app, host="127.0.0.1", port=3010, log_level="info")
