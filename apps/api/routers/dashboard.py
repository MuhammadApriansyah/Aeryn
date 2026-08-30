"""V61.0 — Dashboard router for Aeryn API."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, StreamingResponse, HTMLResponse
import os, sys, time, json, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from sse_starlette.sse import EventSourceResponse
from aeryn_core.platform.realtime import get_emitter
from aeryn_core.utils.llm_client import get_mode_router
from aeryn_core.safety.safety_engine import get_safety_engine
from aeryn_core.utils.persona_engine import load_persona
from aeryn_core.platform.notification_system import get_notification_manager, get_scheduler, Notification
from aeryn_core.auth.api_keys import get_api_key_manager
from aeryn_core.safety.secrets_runtime import get_secrets_manager
from aeryn_core.database.semantic_indexer import get_semantic_indexer
from aeryn_core.memory.hybrid_search import get_search_engine
from aeryn_core.memory.vault import AerynVault
from aeryn_core.memory.social_memory import SocialMemory
from aeryn_core.utils.performance import get_uptime
from aeryn_core.utils.error_recovery import get_error_recovery

router = APIRouter()

# ── SSE + WebSocket Endpoints ─────────────────────────────────

from sse_starlette.sse import EventSourceResponse

@router.get("/dashboard/stream")
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


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time two-way dashboard commands."""
    emitter = get_emitter()
    client_id = f"ws_{int(time.time())}_{id(websocket)}"
    await websocket.accept()
    emitter.register_ws(client_id, websocket)
    
    try:
        # Send connection ack
        await websocket.send_json({"type": "connected", "data": {"client_id": client_id}})
        
        # Push immediate health update on connect
        await _push_health_update(websocket)
        
        # Push immediate stats on connect
        await _push_stats_update(websocket)
        
        # Push immediate notifications on connect
        await _push_notifications_update(websocket)
        
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
                
                elif cmd_type == "get_health":
                    await _push_health_update(websocket)
                
                elif cmd_type == "get_stats":
                    await _push_stats_update(websocket)
                
                elif cmd_type == "get_notifications":
                    await _push_notifications_update(websocket)
                
                elif cmd_type == "chat":
                    await _handle_chat(websocket, emitter, cmd_data)
                
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
                        notif = Notification(
                            user_id=cmd_data.get("user_id", "default"),
                            title=cmd_data.get("title", ""),
                            message=cmd_data.get("message", ""),
                            priority=cmd_data.get("priority", "normal")
                        )
                        nid = mgr.create(notif)
                        await websocket.send_json({"type": "notif_created", "data": {"id": nid}})
                        # Broadcast new notification to all WS clients
                        await emitter.broadcast("notification_new", {
                            "id": nid,
                            "user_id": cmd_data.get("user_id", "default"),
                            "title": cmd_data.get("title", ""),
                            "message": cmd_data.get("message", ""),
                            "priority": cmd_data.get("priority", "normal"),
                        })
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
                
                elif cmd_type == "action":
                    action = cmd_data.get("action", "")
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


async def _push_health_update(websocket):
    """Push current health data to a specific WebSocket client."""
    try:
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        try:
            cpu_pct = psutil.cpu_percent(interval=0.1)
        except Exception:
            cpu_pct = 0
        health = {
            "status": "healthy",
            "memory_mb": round(mem_mb, 1),
            "version": "61.0",
            "cpu_percent": cpu_pct,
        }
    except ImportError:
        health = {"status": "healthy", "version": "61.0", "memory_mb": 0, "cpu_percent": 0}
    except Exception as e:
        health = {"status": "error", "error": str(e), "version": "61.0"}
    
    try:
        await websocket.send_json({"type": "health_update", "data": health})
    except Exception:
        pass


async def _push_stats_update(websocket):
    """Push system stats to a specific WebSocket client."""
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

        stats = {
            "memory_used_mb": mem_used_mb,
            "memory_total_mb": mem_total_mb,
            "memory_percent": mem_pct,
            "disk_free_gb": disk_free_gb,
            "disk_percent": disk_pct,
            "uptime_s": round(time.time() - _start_time, 0),
        }
        await websocket.send_json({"type": "stats", "data": stats})
    except Exception:
        pass


async def _push_notifications_update(websocket):
    """Push pending notifications to a specific WebSocket client."""
    try:
        notif_mgr = get_notification_manager()
        notifs = notif_mgr.get_pending()
        await websocket.send_json({"type": "notifications", "data": {"notifications": notifs}})
    except Exception:
        await websocket.send_json({"type": "notifications", "data": {"notifications": []}})


async def _handle_chat(websocket, emitter, cmd_data):
    """Handle chat command via WebSocket with LLM."""
    try:
        from aeryn_core.safety.safety_engine import get_safety_engine
        from aeryn_core.utils.persona_engine import load_persona
        eng = get_safety_engine()
        text = cmd_data.get("message", "")
        safety = eng.check_input(text)
        if not safety.safe:
            await websocket.send_json({"type": "error", "data": {"message": "Blocked by safety engine"}})
            return
        
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
        
        await websocket.send_json({
            "type": "chat_response",
            "data": {
                "response": response,
                "session_id": sid,
                "reasoning": reasoning,
                "provider": result.get("provider"),
                "model": result.get("model"),
            }
        })
    except Exception as e:
        await websocket.send_json({"type": "error", "data": {"message": str(e)}})

