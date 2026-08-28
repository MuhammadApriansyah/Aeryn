#!/usr/bin/env python3
"""V41.0 — Dashboard V4: Frontend Test + Real-time.

Fixes:
1. POST endpoints accept JSON body
2. Sidebar toggle works (open/close)
3. Real-time via WebSocket + SSE
4. All endpoints accessible
"""

import os, sys, json, uuid, sqlite3, asyncio, time, shutil, re
from typing import Optional, Dict, List, Any
from datetime import datetime

# Ensure aeryn_core can be found
_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# _SCRIPT_DIR is apps/api/.. = apps/, but aeryn_core is in parent
_AERYN_ROOT = os.path.dirname(_SCRIPT_DIR)
if _AERYN_ROOT not in sys.path:
    sys.path.insert(0, _AERYN_ROOT)

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Aeryn Daemon", version="41.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Helpers ───────────────────────────────────

async def get_json_body(request: Request) -> Dict:
    """Get JSON body from request, fallback to query params."""
    try:
        body = await request.json()
        if body:
            return body
    except Exception:
        pass
    
    # Fallback to query params
    return dict(request.query_params)

def success(data: Any = None) -> JSONResponse:
    return JSONResponse({"status": "ok", "data": data})

def error(message: str, code: int = 400) -> JSONResponse:
    return JSONResponse({"status": "error", "message": message}, status_code=code)

# ── System Stats ─────────────────────────────

def get_system_stats() -> Dict:
    try:
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
        
        stat = os.statvfs('/')
        disk_total = stat.f_blocks * stat.f_frsize
        disk_free = stat.f_bavail * stat.f_frsize
        disk_used = disk_total - disk_free
        
        process_mem = 0
        try:
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        process_mem = int(line.split()[1]) / 1024
                        break
        except Exception:
            pass
        
        return {
            "memory_used_mb": mem_used_mb,
            "memory_total_mb": mem_total_mb,
            "memory_percent": mem_pct,
            "disk_total_gb": round(disk_total / (1024**3), 1),
            "disk_used_gb": round(disk_used / (1024**3), 1),
            "disk_free_gb": round(disk_free / (1024**3), 1),
            "disk_percent": round(disk_used / disk_total * 100, 1) if disk_total else 0,
            "process_mem_mb": round(process_mem, 1),
        }
    except Exception:
        return {}

# ── Real-time Broadcast ──────────────────────

_clients: Dict[str, Any] = {}  # ws connections
_sse_queues: Dict[str, asyncio.Queue] = {}

async def broadcast(event_type: str, data: Any):
    """Broadcast to all WebSocket + SSE clients."""
    message = json.dumps({"type": event_type, "data": data, "timestamp": time.time()})
    
    # WebSocket
    dead = []
    for cid, ws in _clients.items():
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(cid)
    for cid in dead:
        _clients.pop(cid, None)
    
    # SSE
    dead = []
    for cid, queue in _sse_queues.items():
        try:
            await asyncio.wait_for(queue.put({"event": event_type, "data": message}), timeout=1)
        except Exception:
            dead.append(cid)
    for cid in dead:
        _sse_queues.pop(cid, None)

async def broadcast_loop():
    """Broadcast all data every 5 seconds."""
    while True:
        await asyncio.sleep(5)
        
        # Stats
        await broadcast("stats", get_system_stats())
        
        # Tasks
        try:
            from aeryn_core.shared_db import get_shared_db
            db = get_shared_db()
            tasks = db.get_all_tasks()
            await broadcast("tasks", {"tasks": tasks, "count": len(tasks)})
        except Exception:
            pass
        
        # Notifications
        try:
            from aeryn_core.notification_system import get_notification_manager
            mgr = get_notification_manager()
            await broadcast("notifications", {"notifications": mgr.get_pending()})
        except Exception:
            pass
        
        # Vault
        try:
            from aeryn_core.vault import AerynVault
            vault = AerynVault()
            entries = vault.list_entries(limit=20)
            counts = vault.count_entries()
            await broadcast("vault", {"entries": entries, "total_entries": sum(counts.values())})
        except Exception:
            pass

# ── Pages ────────────────────────────────────

@app.get("/")
@app.get("/dashboard")
async def dashboard():
    return FileResponse("apps/api/dashboard.html")

@app.get("/chat")
async def chat_page():
    return FileResponse("apps/api/dashboard.html")

# ── Health ───────────────────────────────────

@app.get("/health")
async def health():
    return JSONResponse({"status": "healthy", "version": "41.0", **get_system_stats()})

# ── Universal Action Endpoint ─────────────────

@app.post("/api/{action}")
async def api_action(action: str, request: Request):
    """Universal action endpoint - handles all operations."""
    body = await get_json_body(request)
    params = body.get("params", body)  # Support both {params: {...}} and direct params
    
    try:
        if action == "chat":
            from aeryn_core.safety_engine import get_safety_engine
            eng = get_safety_engine()
            safety = eng.check_input(params.get("message", ""))
            if not safety.safe:
                return error("Message blocked by safety filter")
            return success({
                "response": f"I received: {params.get('message', '')[:200]}",
                "session_id": params.get("session_id", "default"),
            })
        
        elif action == "create_notification":
            from aeryn_core.notification_system import get_notification_manager, Notification
            mgr = get_notification_manager()
            notif = Notification(
                user_id=params.get("user_id", "default"),
                title=params.get("title", ""),
                message=params.get("message", ""),
                priority=params.get("priority", "normal"),
            )
            nid = mgr.create(notif)
            await broadcast("notification_created", {"id": nid})
            return success({"id": nid})
        
        elif action == "parse_tasks":
            from aeryn_core.auto_task import get_auto_task
            auto = get_auto_task()
            tasks = auto.parse(params.get("user_id", "default"), params.get("text", ""))
            return success({"tasks": tasks, "count": len(tasks)})
        
        elif action == "execute_tool":
            from aeryn_core.tool_runtime import get_tool_runtime
            rt = get_tool_runtime()
            result = await rt.execute(params.get("tool", ""), params.get("params", {}))
            return success(result.to_dict())
        
        elif action == "create_api_key":
            from aeryn_core.api_keys import get_api_key_manager
            km = get_api_key_manager()
            result = km.create(params.get("user_id", "default"), params.get("name", "key"))
            return success(result)
        
        elif action == "revoke_api_key":
            from aeryn_core.api_keys import get_api_key_manager
            km = get_api_key_manager()
            km.revoke(params.get("key_id", ""))
            return success()
        
        elif action == "set_secret":
            from aeryn_core.secrets_runtime import get_secrets_manager
            sm = get_secrets_manager()
            sm.set(params.get("user_id", "default"), params.get("name", ""), params.get("value", ""))
            return success()
        
        elif action == "check_safety":
            from aeryn_core.safety_engine import get_safety_engine
            eng = get_safety_engine()
            result = eng.check_input(params.get("text", ""))
            return success({"valid": result.safe, "risk": result.risk, "reason": result.reason})
        
        elif action == "generate_briefing":
            from aeryn_core.proactive_v2 import get_daily_briefing
            briefing = get_daily_briefing()
            result = briefing.generate_morning(params.get("user_id", "default"))
            return success(result)
        
        elif action == "generate_suggestions":
            from aeryn_core.proactive_v2 import get_proactive_v2
            engine = get_proactive_v2()
            suggestions = engine.detect_patterns(params.get("user_id", "default"))
            return success({"suggestions": suggestions})
        
        elif action == "create_task":
            from aeryn_core.shared_db import get_shared_db
            db = get_shared_db()
            task_id = db.add_task(
                params.get("title", ""),
                params.get("description", ""),
                params.get("priority", 5),
            )
            await broadcast("task_created", {"id": task_id})
            return success({"id": task_id})
        
        elif action == "update_task":
            from aeryn_core.shared_db import get_shared_db
            db = get_shared_db()
            db.update_task(
                params.get("task_id", ""),
                params.get("status"),
                params.get("progress"),
                params.get("result"),
                params.get("error"),
            )
            await broadcast("task_updated", {"id": params.get("task_id")})
            return success()
        
        elif action == "index_vault":
            from aeryn_core.semantic_indexer import get_semantic_indexer
            idx = get_semantic_indexer()
            result = idx.index_vault(force=params.get("force", False))
            return success(result)
        
        else:
            return error(f"Unknown action: {action}", 404)
    
    except Exception as e:
        return error(str(e), 500)

# ── Universal Data Endpoint ───────────────────

@app.get("/api/data")
async def api_data(action: str = "", user_id: str = "default", limit: int = 20):
    """Universal data read endpoint."""
    try:
        if action == "stats":
            return success(get_system_stats())
        
        elif action == "tasks":
            from aeryn_core.shared_db import get_shared_db
            db = get_shared_db()
            return success({"tasks": db.get_all_tasks(), "count": len(db.get_all_tasks())})
        
        elif action == "notifications":
            from aeryn_core.notification_system import get_notification_manager
            mgr = get_notification_manager()
            return success({"notifications": mgr.get_pending(user_id)})
        
        elif action == "vault":
            from aeryn_core.vault import AerynVault
            vault = AerynVault()
            return success({
                "entries": vault.list_entries(limit=limit),
                "total_entries": sum(vault.count_entries().values()),
                "counts": vault.count_entries(),
            })
        
        elif action == "tools":
            from aeryn_core.tool_runtime import get_tool_runtime
            rt = get_tool_runtime()
            return success({"tools": rt.list_tools()})
        
        elif action == "api_keys":
            from aeryn_core.api_keys import get_api_key_manager
            km = get_api_key_manager()
            return success({"keys": km.list_keys(user_id)})
        
        elif action == "usage":
            from aeryn_core.usage_metering import get_usage_metering
            um = get_usage_metering()
            return success(um.get_summary(user_id))
        
        elif action == "secrets":
            from aeryn_core.secrets_runtime import get_secrets_manager
            sm = get_secrets_manager()
            return success({"secrets": sm.list(user_id)})
        
        elif action == "circuit_breakers":
            from aeryn_core.error_recovery import get_error_recovery
            recovery = get_error_recovery()
            return success({"circuit_breakers": recovery.get_circuit_breaker_states()})
        
        elif action == "error_log":
            from aeryn_core.error_recovery import get_error_recovery
            recovery = get_error_recovery()
            return success({"errors": recovery.get_error_log(limit)})
        
        elif action == "search":
            from aeryn_core.semantic_indexer import get_semantic_indexer
            idx = get_semantic_indexer()
            return success({"results": idx.search(user_id, limit=limit)})
        
        elif action == "constitutional":
            try:
                from aeryn_core.constitutional_ai import get_constitutional_ai
                cai = get_constitutional_ai()
                return success({"principles": cai.get_principles()})
            except Exception:
                return success({"principles": []})
        
        elif action == "queue":
            from aeryn_core.background_queue import get_task_queue
            queue = get_task_queue()
            return success({"pending": queue.get_pending_count(), "running": queue.get_running_count()})
        
        else:
            return error("Unknown action", 404)
    
    except Exception as e:
        return error(str(e), 500)

# ── WebSocket ─────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time two-way communication."""
    await websocket.accept()
    client_id = f"ws_{int(time.time())}_{id(websocket)}"
    _clients[client_id] = websocket
    
    try:
        # Send initial data
        await websocket.send_json({"type": "connected", "data": {"client_id": client_id}})
        await websocket.send_json({"type": "stats", "data": get_system_stats()})
        
        while True:
            msg = await websocket.receive_text()
            try:
                cmd = json.loads(msg)
                cmd_type = cmd.get("type", "")
                cmd_data = cmd.get("data", {})
                
                if cmd_type == "ping":
                    await websocket.send_json({"type": "pong", "data": {}})
                elif cmd_type == "get_stats":
                    await websocket.send_json({"type": "stats", "data": get_system_stats()})
                elif cmd_type == "get_tasks":
                    from aeryn_core.shared_db import get_shared_db
                    db = get_shared_db()
                    await websocket.send_json({"type": "tasks", "data": {"tasks": db.get_all_tasks()}})
                elif cmd_type == "get_notifications":
                    from aeryn_core.notification_system import get_notification_manager
                    mgr = get_notification_manager()
                    await websocket.send_json({"type": "notifications", "data": {"notifications": mgr.get_pending()}})
                elif cmd_type == "get_vault":
                    from aeryn_core.vault import AerynVault
                    vault = AerynVault()
                    await websocket.send_json({"type": "vault", "data": {"entries": vault.list_entries(limit=20)}})
                elif cmd_type == "get_tools":
                    from aeryn_core.tool_runtime import get_tool_runtime
                    rt = get_tool_runtime()
                    await websocket.send_json({"type": "tools", "data": {"tools": rt.list_tools()}})
                elif cmd_type == "get_api_keys":
                    from aeryn_core.api_keys import get_api_key_manager
                    km = get_api_key_manager()
                    await websocket.send_json({"type": "api_keys", "data": {"keys": km.list_keys("default")}})
                elif cmd_type == "get_usage":
                    from aeryn_core.usage_metering import get_usage_metering
                    um = get_usage_metering()
                    await websocket.send_json({"type": "usage", "data": um.get_summary("default")})
                elif cmd_type == "get_secrets":
                    from aeryn_core.secrets_runtime import get_secrets_manager
                    sm = get_secrets_manager()
                    await websocket.send_json({"type": "secrets", "data": {"secrets": sm.list("default")}})
                elif cmd_type == "get_circuit_breakers":
                    from aeryn_core.error_recovery import get_error_recovery
                    recovery = get_error_recovery()
                    await websocket.send_json({"type": "circuit_breakers", "data": {"circuit_breakers": recovery.get_circuit_breaker_states()}})
                elif cmd_type == "get_briefing":
                    from aeryn_core.proactive_v2 import get_daily_briefing
                    briefing = get_daily_briefing()
                    await websocket.send_json({"type": "briefing", "data": briefing.generate_morning("default")})
                elif cmd_type == "get_suggestions":
                    from aeryn_core.proactive_v2 import get_proactive_v2
                    engine = get_proactive_v2()
                    await websocket.send_json({"type": "suggestions", "data": {"suggestions": engine.detect_patterns("default")}})
                elif cmd_type == "get_queue":
                    from aeryn_core.background_queue import get_task_queue
                    queue = get_task_queue()
                    await websocket.send_json({"type": "queue", "data": {"pending": queue.get_pending_count(), "running": queue.get_running_count()}})
                else:
                    await websocket.send_json({"type": "error", "data": {"message": f"Unknown command: {cmd_type}"}})
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "data": {"message": "Invalid JSON"}})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        _clients.pop(client_id, None)

# ── SSE ───────────────────────────────────────

from sse_starlette.sse import EventSourceResponse

@app.get("/sse")
async def sse_endpoint():
    """SSE fallback for real-time updates."""
    queue = asyncio.Queue()
    client_id = f"sse_{int(time.time())}"
    _sse_queues[client_id] = queue
    
    async def event_generator():
        try:
            # Send initial data
            yield {"event": "connected", "data": json.dumps({"client_id": client_id})}
            
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield event
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
        finally:
            _sse_queues.pop(client_id, None)
    
    return EventSourceResponse(event_generator())

# ── Startup ──────────────────────────────────

@app.on_event("startup")
async def startup():
    asyncio.create_task(broadcast_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3010)
