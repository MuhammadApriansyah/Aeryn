#!/usr/bin/env python3
"""V41.0 — Broadcast all data types via WebSocket + SSE."""

import os, sys, json, asyncio, time, shutil
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.realtime import get_emitter


async def broadcast_system_stats():
    """Broadcast system stats."""
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
        
        disk = shutil.disk_usage("/")
        disk_free_gb = round(disk.free / (1024**3), 2)
        disk_pct = round((disk.total - disk.free) / disk.total * 100, 1)
        
        process_mem = 0
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    process_mem = int(line.split()[1]) / 1024
                    break
        
        emitter = get_emitter()
        await emitter.broadcast("stats", {
            "memory_used_mb": mem_used_mb,
            "memory_total_mb": mem_total_mb,
            "memory_percent": mem_pct,
            "disk_free_gb": disk_free_gb,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round((disk.total - disk.free) / (1024**3), 2),
            "disk_percent": disk_pct,
            "process_mem_mb": round(process_mem, 1),
            "cpu_percent": 0,
        })
    except Exception as e:
        print(f"Stats broadcast error: {e}")


async def broadcast_tasks():
    """Broadcast task queue."""
    try:
        from aeryn_core.shared_db import get_shared_db
        db = get_shared_db()
        tasks = db.get_all_tasks()
        emitter = get_emitter()
        await emitter.broadcast("tasks", {"tasks": tasks, "count": len(tasks)})
    except Exception as e:
        print(f"Tasks broadcast error: {e}")


async def broadcast_notifications():
    """Broadcast pending notifications."""
    try:
        from aeryn_core.notification_system import get_notification_manager
        mgr = get_notification_manager()
        pending = mgr.get_pending()
        emitter = get_emitter()
        await emitter.broadcast("notifications", {"notifications": pending})
    except Exception as e:
        print(f"Notifications broadcast error: {e}")


async def broadcast_vault():
    """Broadcast vault data."""
    try:
        from aeryn_core.vault import AerynVault
        vault = AerynVault()
        entries = vault.list_entries(limit=20)
        counts = vault.count_entries()
        total = sum(counts.values())
        emitter = get_emitter()
        await emitter.broadcast("vault", {"entries": entries, "total_entries": total, "counts": counts})
    except Exception as e:
        print(f"Vault broadcast error: {e}")


async def broadcast_tools():
    """Broadcast available tools."""
    try:
        from aeryn_core.tool_runtime import get_tool_runtime
        rt = get_tool_runtime()
        tools = rt.list_tools()
        emitter = get_emitter()
        await emitter.broadcast("tools", {"tools": tools})
    except Exception as e:
        print(f"Tools broadcast error: {e}")


async def broadcast_performance():
    """Broadcast performance data."""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        emitter = get_emitter()
        await emitter.broadcast("performance", {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_used_mb": mem.used / 1024 / 1024,
            "memory_total_mb": mem.total / 1024 / 1024,
            "disk_percent": disk.percent,
            "disk_used_gb": (disk.total - disk.free) / 1024 / 1024 / 1024,
            "disk_free_gb": disk.free / 1024 / 1024 / 1024,
        })
    except ImportError:
        # Fallback without psutil
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            mem_total = mem_available = 0
            for line in lines:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1])
            mem_pct = round((mem_total - mem_available) / mem_total * 100, 1) if mem_total else 0
            emitter = get_emitter()
            await emitter.broadcast("performance", {
                "cpu_percent": 0,
                "memory_percent": mem_pct,
                "memory_used_mb": round((mem_total - mem_available) / 1024, 1),
                "memory_total_mb": round(mem_total / 1024, 1),
            })
        except Exception as e:
            print(f"Performance broadcast error: {e}")


async def broadcast_uptime():
    """Broadcast uptime."""
    try:
        from aeryn_core.performance import get_uptime
        ut = get_uptime()
        emitter = get_emitter()
        await emitter.broadcast("uptime", {
            "uptime_s": ut.uptime_seconds,
            "uptime": ut.uptime_formatted,
            "restart_count": ut._restart_count,
        })
    except Exception as e:
        print(f"Uptime broadcast error: {e}")


async def broadcast_queue():
    """Broadcast task queue stats."""
    try:
        from aeryn_core.background_queue import get_task_queue
        queue = get_task_queue()
        emitter = get_emitter()
        await emitter.broadcast("queue", {
            "pending": queue.get_pending_count(),
            "running": queue.get_running_count(),
        })
    except Exception as e:
        print(f"Queue broadcast error: {e}")


async def broadcast_api_keys():
    """Broadcast API keys."""
    try:
        from aeryn_core.api_keys import get_api_key_manager
        km = get_api_key_manager()
        keys = km.list_keys("dashboard")
        emitter = get_emitter()
        await emitter.broadcast("api_keys", {"keys": keys})
    except Exception as e:
        print(f"API keys broadcast error: {e}")


async def broadcast_usage():
    """Broadcast usage stats."""
    try:
        from aeryn_core.usage_metering import get_usage_metering
        um = get_usage_metering()
        summary = um.get_summary("dashboard")
        emitter = get_emitter()
        await emitter.broadcast("usage", summary)
    except Exception as e:
        print(f"Usage broadcast error: {e}")


async def broadcast_secrets():
    """Broadcast secrets list."""
    try:
        from aeryn_core.secrets_runtime import get_secrets_manager
        sm = get_secrets_manager()
        secrets_list = sm.list("dashboard")
        emitter = get_emitter()
        await emitter.broadcast("secrets", {"secrets": secrets_list})
    except Exception as e:
        print(f"Secrets broadcast error: {e}")


async def broadcast_circuit_breakers():
    """Broadcast circuit breaker states."""
    try:
        from aeryn_core.error_recovery import get_error_recovery
        recovery = get_error_recovery()
        breakers = recovery.get_circuit_breaker_states()
        emitter = get_emitter()
        await emitter.broadcast("circuit_breakers", {"circuit_breakers": breakers})
    except Exception as e:
        print(f"Circuit breakers broadcast error: {e}")


async def broadcast_briefing():
    """Broadcast daily briefing."""
    try:
        from aeryn_core.proactive_v2 import get_daily_briefing
        briefing = get_daily_briefing()
        morning = briefing.generate_morning("dashboard")
        emitter = get_emitter()
        await emitter.broadcast("briefing", morning)
    except Exception as e:
        print(f"Briefing broadcast error: {e}")


async def broadcast_suggestions():
    """Broadcast proactive suggestions."""
    try:
        from aeryn_core.proactive_v2 import get_proactive_v2
        engine = get_proactive_v2()
        suggestions = engine.generate_all("dashboard")
        emitter = get_emitter()
        await emitter.broadcast("suggestions", {"suggestions": suggestions})
    except Exception as e:
        print(f"Suggestions broadcast error: {e}")


async def broadcast_constitutional():
    """Broadcast constitutional AI principles."""
    try:
        from aeryn_core.constitutional_ai import get_constitutional_ai
        cai = get_constitutional_ai()
        principles = cai.get_principles()
        emitter = get_emitter()
        await emitter.broadcast("constitutional", {"principles": principles})
    except Exception as e:
        print(f"Constitutional broadcast error: {e}")


async def broadcast_all():
    """Broadcast all data types to all connected clients."""
    await asyncio.gather(
        broadcast_system_stats(),
        broadcast_tasks(),
        broadcast_notifications(),
        broadcast_vault(),
        broadcast_tools(),
        broadcast_performance(),
        broadcast_uptime(),
        broadcast_queue(),
        broadcast_api_keys(),
        broadcast_usage(),
        broadcast_secrets(),
        broadcast_circuit_breakers(),
        broadcast_briefing(),
        broadcast_suggestions(),
        broadcast_constitutional(),
        return_exceptions=True,
    )


async def broadcast_loop():
    """Main broadcast loop - sends all data every 5 seconds."""
    while True:
        await asyncio.sleep(5)
        await broadcast_all()


async def handle_websocket_command(command: str, data: dict) -> dict:
    """Handle a WebSocket command and return response data."""
    try:
        if command == "get_stats":
            from aeryn_core.performance import get_optimizer
            opt = get_optimizer()
            return opt.get_system_stats()
        
        elif command == "get_tasks":
            from aeryn_core.shared_db import get_shared_db
            db = get_shared_db()
            tasks = db.get_all_tasks()
            return {"tasks": tasks, "count": len(tasks)}
        
        elif command == "get_notifications":
            from aeryn_core.notification_system import get_notification_manager
            mgr = get_notification_manager()
            return {"notifications": mgr.get_pending(data.get("user_id"))}
        
        elif command == "get_vault":
            from aeryn_core.vault import AerynVault
            vault = AerynVault()
            entries = vault.list_entries(limit=data.get("limit", 20))
            counts = vault.count_entries()
            return {"entries": entries, "total_entries": sum(counts.values()), "counts": counts}
        
        elif command == "get_tools":
            from aeryn_core.tool_runtime import get_tool_runtime
            rt = get_tool_runtime()
            return {"tools": rt.list_tools()}
        
        elif command == "get_briefing":
            from aeryn_core.proactive_v2 import get_daily_briefing
            briefing = get_daily_briefing()
            return briefing.generate_morning(data.get("user_id", "dashboard"))
        
        elif command == "get_suggestions":
            from aeryn_core.proactive_v2 import get_proactive_v2
            engine = get_proactive_v2()
            return {"suggestions": engine.generate_all(data.get("user_id", "dashboard"))}
        
        elif command == "get_performance":
            from aeryn_core.performance import get_optimizer
            opt = get_optimizer()
            return opt.get_system_stats()
        
        elif command == "get_uptime":
            from aeryn_core.performance import get_uptime
            ut = get_uptime()
            return {"uptime_s": ut.uptime_seconds, "uptime": ut.uptime_formatted}
        
        elif command == "get_queue":
            from aeryn_core.background_queue import get_task_queue
            queue = get_task_queue()
            return {"pending": queue.get_pending_count(), "running": queue.get_running_count()}
        
        elif command == "get_api_keys":
            from aeryn_core.api_keys import get_api_key_manager
            km = get_api_key_manager()
            return {"keys": km.list_keys(data.get("user_id", "dashboard"))}
        
        elif command == "get_usage":
            from aeryn_core.usage_metering import get_usage_metering
            um = get_usage_metering()
            return um.get_summary(data.get("user_id", "dashboard"), data.get("days", 30))
        
        elif command == "get_secrets":
            from aeryn_core.secrets_runtime import get_secrets_manager
            sm = get_secrets_manager()
            return {"secrets": sm.list(data.get("user_id", "dashboard"))}
        
        elif command == "get_circuit_breakers":
            from aeryn_core.error_recovery import get_error_recovery
            recovery = get_error_recovery()
            return {"circuit_breakers": recovery.get_circuit_breaker_states()}
        
        elif command == "get_constitutional":
            from aeryn_core.constitutional_ai import get_constitutional_ai
            cai = get_constitutional_ai()
            return {"principles": cai.get_principles()}
        
        elif command == "chat":
            # Chat is handled specially - return a placeholder
            # Actual chat processing happens via the chat endpoint
            return {"response": "Chat message received via WebSocket"}
        
        elif command == "create_notification":
            from aeryn_core.notification_system import get_notification_manager, Notification
            mgr = get_notification_manager()
            notif = Notification(
                user_id=data.get("user_id", "dashboard"),
                title=data.get("title", ""),
                message=data.get("message", ""),
                priority=data.get("priority", "normal"),
            )
            nid = mgr.create(notif)
            return {"id": nid, "status": "created"}
        
        elif command == "parse_tasks":
            from aeryn_core.auto_task import get_auto_task
            auto = get_auto_task()
            tasks = auto.parse(data.get("user_id", "dashboard"), data.get("text", ""))
            return {"tasks": tasks, "count": len(tasks)}
        
        elif command == "execute_tool":
            from aeryn_core.tool_runtime import get_tool_runtime
            rt = get_tool_runtime()
            result = await rt.execute(data.get("tool", ""), data.get("params", {}))
            return result.to_dict()
        
        elif command == "check_safety":
            from aeryn_core.safety_engine import get_safety_engine
            eng = get_safety_engine()
            result = eng.check_input(data.get("text", ""))
            return {"valid": result.safe, "risk": result.risk, "issues": result.issues}
        
        else:
            return {"error": f"Unknown command: {command}"}
    
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Test broadcast
    async def test():
        await broadcast_all()
        print("Broadcast test complete")
    
    asyncio.run(test())
