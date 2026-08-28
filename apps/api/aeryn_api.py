#!/usr/bin/env python3
"""V41.0 — Aeryn Daemon :3010 — Simplified & Accessible API."""

import os, sys, json, uuid, sqlite3, asyncio, time, shutil, re
from typing import Optional, Dict, List, Any
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.responses import Response, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Aeryn Daemon", version="41.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Safe Path Validation ─────────────────────

SAFE_READ_DIRS = [
    os.path.expanduser("~/aeryn-core-agent"),
    "/tmp/aeryn-safe",
]

SAFE_WRITE_DIRS = [
    os.path.expanduser("~/aeryn-core-agent/Personalisasi"),
    "/tmp/aeryn-safe",
]

def safe_path_read(path: str) -> Optional[str]:
    """Validate path for reading."""
    try:
        real = os.path.realpath(path)
        for d in SAFE_READ_DIRS:
            real_d = os.path.realpath(d)
            if real.startswith(real_d + os.sep) or real == real_d:
                return real
    except Exception:
        pass
    return None

def safe_path_write(path: str) -> Optional[str]:
    """Validate path for writing."""
    try:
        real = os.path.realpath(path)
        for d in SAFE_WRITE_DIRS:
            real_d = os.path.realpath(d)
            if real.startswith(real_d + os.sep) or real == real_d:
                return real
    except Exception:
        pass
    return None

# ── Command Sanitization ─────────────────────

DANGEROUS_PATTERNS = [
    r';rm\s', r'\|rm\s', r'&&rm\s',
    r';mkfs', r'\|mkfs',
    r':\(\)\{.*\}\;',
    r'`[^`]+`', r'\$\([^)]+\)',
    r'>\s*/dev/', r'<\s*/etc/',
    r'curl\s+.*\|.*sh', r'wget\s+.*\|.*sh',
    r';\s*bash\s-i', r'\|bash\s-i',
    r'python\s+-c\s+.*import\s+os\.system',
]

def sanitize_command(cmd: str) -> tuple[bool, str]:
    """Sanitize shell command."""
    for p in DANGEROUS_PATTERNS:
        if re.search(p, cmd, re.IGNORECASE):
            return False, f"Dangerous pattern: {p}"
    return True, ""

# ── System Stats ─────────────────────────────

def get_system_stats() -> Dict:
    """Get system statistics."""
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

# ── All-in-One Action Endpoint ───────────────

@app.post("/api/action")
async def api_action(request: Request):
    """Universal action endpoint - handles all operations."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    action = body.get("action", "")
    params = body.get("params", {})
    
    handlers = {
        "chat": handle_chat,
        "create_notification": handle_create_notification,
        "parse_tasks": handle_parse_tasks,
        "execute_tool": handle_execute_tool,
        "create_api_key": handle_create_api_key,
        "set_secret": handle_set_secret,
        "check_safety": handle_check_safety,
        "generate_briefing": handle_generate_briefing,
        "generate_suggestions": handle_generate_suggestions,
    }
    
    handler = handlers.get(action)
    if handler:
        return await handler(params)
    
    return {"error": f"Unknown action: {action}"}

async def handle_chat(params: Dict) -> Dict:
    """Handle chat message."""
    message = params.get("message", "")
    session_id = params.get("session_id", "default")
    
    # Import safety engine
    try:
        from aeryn_core.safety_engine import get_safety_engine
        eng = get_safety_engine()
        safety = eng.check_input(message)
        if not safety.safe:
            return {"error": "Message blocked by safety filter", "safety": safety.to_dict()}
    except Exception:
        pass
    
    # Return response (simplified for now)
    return {
        "response": f"I received: {message[:200]}",
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
    }

async def handle_create_notification(params: Dict) -> Dict:
    """Create notification."""
    from aeryn_core.notification_system import get_notification_manager, Notification
    mgr = get_notification_manager()
    notif = Notification(
        user_id=params.get("user_id", "default"),
        title=params.get("title", ""),
        message=params.get("message", ""),
        priority=params.get("priority", "normal"),
    )
    nid = mgr.create(notif)
    return {"id": nid, "status": "created"}

async def handle_parse_tasks(params: Dict) -> Dict:
    """Parse tasks from text."""
    from aeryn_core.auto_task import get_auto_task
    auto = get_auto_task()
    tasks = auto.parse(params.get("user_id", "default"), params.get("text", ""))
    return {"tasks": tasks, "count": len(tasks)}

async def handle_execute_tool(params: Dict) -> Dict:
    """Execute a tool."""
    from aeryn_core.tool_runtime import get_tool_runtime
    rt = get_tool_runtime()
    result = await rt.execute(params.get("tool", ""), params.get("params", {}))
    return result.to_dict()

async def handle_create_api_key(params: Dict) -> Dict:
    """Create API key."""
    from aeryn_core.api_keys import get_api_key_manager
    km = get_api_key_manager()
    return km.create(params.get("user_id", "default"), params.get("name", "key"))

async def handle_set_secret(params: Dict) -> Dict:
    """Set a secret."""
    from aeryn_core.secrets_runtime import get_secrets_manager
    sm = get_secrets_manager()
    sm.set(params.get("user_id", "default"), params.get("name", ""), params.get("value", ""))
    return {"status": "stored"}

async def handle_check_safety(params: Dict) -> Dict:
    """Check text safety."""
    from aeryn_core.safety_engine import get_safety_engine
    eng = get_safety_engine()
    result = eng.check_input(params.get("text", ""))
    return {"valid": result.safe, "risk": result.risk, "issues": result.issues}

async def handle_generate_briefing(params: Dict) -> Dict:
    """Generate daily briefing."""
    from aeryn_core.proactive_v2 import get_daily_briefing
    briefing = get_daily_briefing()
    return briefing.generate_morning(params.get("user_id", "default"))

async def handle_generate_suggestions(params: Dict) -> Dict:
    """Generate suggestions."""
    from aeryn_core.proactive_v2 import get_proactive_v2
    engine = get_proactive_v2()
    suggestions = engine.generate_all(params.get("user_id", "default"))
    return {"suggestions": suggestions}

# ── Read Endpoints ───────────────────────────

@app.get("/api/data")
async def api_data(action: str = "", user_id: str = "default"):
    """Universal data read endpoint."""
    
    if action == "stats":
        return get_system_stats()
    
    elif action == "tasks":
        from aeryn_core.shared_db import get_shared_db
        db = get_shared_db()
        tasks = db.get_all_tasks()
        return {"tasks": tasks, "count": len(tasks)}
    
    elif action == "notifications":
        from aeryn_core.notification_system import get_notification_manager
        mgr = get_notification_manager()
        return {"notifications": mgr.get_pending(user_id)}
    
    elif action == "vault":
        from aeryn_core.vault import AerynVault
        vault = AerynVault()
        entries = vault.list_entries(limit=20)
        counts = vault.count_entries()
        return {"entries": entries, "total_entries": sum(counts.values())}
    
    elif action == "tools":
        from aeryn_core.tool_runtime import get_tool_runtime
        rt = get_tool_runtime()
        return {"tools": rt.list_tools()}
    
    elif action == "api_keys":
        from aeryn_core.api_keys import get_api_key_manager
        km = get_api_key_manager()
        return {"keys": km.list_keys(user_id)}
    
    elif action == "usage":
        from aeryn_core.usage_metering import get_usage_metering
        um = get_usage_metering()
        return um.get_summary(user_id)
    
    elif action == "secrets":
        from aeryn_core.secrets_runtime import get_secrets_manager
        sm = get_secrets_manager()
        return {"secrets": sm.list(user_id)}
    
    elif action == "circuit_breakers":
        from aeryn_core.error_recovery import get_error_recovery
        recovery = get_error_recovery()
        return {"circuit_breakers": recovery.get_circuit_breaker_states()}
    
    elif action == "search":
        from aeryn_core.semantic_indexer import get_semantic_indexer
        idx = get_semantic_indexer()
        return {"results": idx.search(user_id, limit=10)}
    
    elif action == "constitutional":
        try:
            from aeryn_core.constitutional_ai import get_constitutional_ai
            cai = get_constitutional_ai()
            return {"principles": cai.get_principles()}
        except Exception:
            return {"principles": []}
    
    return {"error": "Unknown action"}

# ── Pages ────────────────────────────────────

@app.get("/")
@app.get("/dashboard")
async def dashboard():
    return FileResponse("apps/api/dashboard.html")

@app.get("/chat")
async def chat_page():
    return FileResponse("apps/api/dashboard.html")

# ── Health Check ─────────────────────────────

@app.get("/health")
async def health():
    stats = get_system_stats()
    return JSONResponse({
        "status": "healthy",
        "version": "41.0",
        "memory_mb": round(stats.get("process_mem_mb", 0), 1),
        **stats,
    })

# ── Startup ──────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    # Create safe directories
    for d in SAFE_WRITE_DIRS:
        os.makedirs(d, exist_ok=True)
    
    uvicorn.run(app, host="0.0.0.0", port=3010)
