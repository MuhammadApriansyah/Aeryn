"""V61.0 — Tools & Proactive router for Aeryn API."""
from fastapi import APIRouter
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.platform.tool_runtime import get_tool_runtime
from aeryn_core.platform.background_queue import get_task_queue
from aeryn_core.reasoning.proactive_engine import get_proactive_engine
from aeryn_core.reasoning.long_horizon import get_long_horizon_planner, TaskPriority
from aeryn_core.platform.auto_task import get_auto_task
from aeryn_core.reasoning.context_manager import get_context_manager
from aeryn_core.memory.memory_decay import get_memory_decay_engine
from aeryn_core.memory.entity_resolution import get_entity_resolver
from aeryn_core.safety.owasp_security import get_owasp_security
from aeryn_core.database.semantic_indexer import get_semantic_indexer
from aeryn_core.billing.usage_metering import get_usage_metering

router = APIRouter()

# ── Tool Runtime Endpoints ────────────────────

@router.get("/tools/list")
async def list_tools():
    """List available tools."""
    runtime = get_tool_runtime()
    return {"tools": runtime.list_tools()}

@router.post("/tools/execute")
async def execute_tool(tool: str, params: dict = None):
    """Execute a tool natively."""
    runtime = get_tool_runtime()
    result = await runtime.execute(tool, params or {})
    return result.to_dict()

# ── Background Task Queue Endpoints ───────────

@router.post("/queue/submit")
async def submit_task(name: str, tool: str, params: dict = None):
    """Submit a task to the background queue."""
    queue = get_task_queue()
    runtime = get_tool_runtime()
    
    async def task_wrapper():
        return await runtime.execute(tool, params or {})
    
    task_id = await queue.submit(name, task_wrapper)
    return {"task_id": task_id, "status": "submitted"}

@router.get("/queue/task/{task_id}")
async def get_task_status(task_id: str):
    """Get task status."""
    queue = get_task_queue()
    task = queue.get_task(task_id)
    return task or {"error": "Task not found"}

@router.get("/queue/tasks")
async def list_queue_tasks():
    """List all tasks."""
    queue = get_task_queue()
    return {"tasks": queue.get_all_tasks()}

@router.get("/queue/stats")
async def queue_stats():
    """Get queue statistics."""
    queue = get_task_queue()
    return {
        "pending": queue.get_pending_count(),
        "running": queue.get_running_count(),
    }

# ── Proactive Engine Endpoints ────────────────

@router.get("/proactive/suggestions")
async def get_suggestions(user_id: str = "default"):
    """Get proactive suggestions."""
    engine = get_proactive_engine()
    return {"suggestions": engine.get_unread(user_id)}

@router.post("/proactive/generate")
async def generate_suggestions(user_id: str = "default"):
    """Generate new suggestions."""
    engine = get_proactive_engine()
    suggestions = engine.generate_all(user_id)
    return {"suggestions": suggestions}

@router.post("/proactive/mark-read")
async def mark_suggestion_read(suggestion_id: str):
    """Mark suggestion as read."""
    engine = get_proactive_engine()
    engine.mark_read(suggestion_id)
    return {"status": "ok"}

# ── Phase 2 Endpoints ─────────────────────────

@router.post("/briefing/morning")
async def morning_briefing(user_id: str = "default"):
    """Generate morning briefing."""
    briefing = get_daily_briefing()
    return briefing.generate_morning(user_id)

@router.post("/briefing/evening")
async def evening_briefing(user_id: str = "default"):
    """Generate evening briefing."""
    briefing = get_daily_briefing()
    return briefing.generate_evening(user_id)

@router.post("/auto-task/parse")
async def parse_tasks(user_id: str, text: str):
    """Parse natural language into tasks."""
    auto_task = get_auto_task()
    tasks = auto_task.parse(user_id, text)
    return {"tasks": tasks, "count": len(tasks)}

@router.get("/proactive/v2/patterns")
async def detect_patterns(user_id: str = "default"):
    """Detect usage patterns."""
    engine = get_proactive_v2()
    return {"patterns": engine.detect_patterns(user_id)}

@router.get("/proactive/v2/anomalies")
async def detect_anomalies(user_id: str = "default"):
    """Detect anomalies."""
    engine = get_proactive_v2()
    return {"anomalies": engine.detect_anomalies(user_id)}

# ── Phase 3 Endpoints ─────────────────────────

@router.post("/api-keys/create")
async def create_api_key(user_id: str, name: str, permissions: list = None):
    """Create new API key."""
    manager = get_api_key_manager()
    return manager.create(user_id, name, permissions)

@router.get("/api-keys/list")
async def list_api_keys(user_id: str):
    """List user's API keys."""
    manager = get_api_key_manager()
    return {"keys": manager.list_keys(user_id)}

@router.post("/api-keys/revoke")
async def revoke_api_key(key_id: str):
    """Revoke an API key."""
    manager = get_api_key_manager()
    return {"success": manager.revoke(key_id)}

@router.get("/usage/summary")
async def usage_summary(user_id: str = None, days: int = 30):
    """Get usage summary."""
    metering = get_usage_metering()
    return metering.get_summary(user_id, days)

@router.post("/usage/track")
async def track_usage(user_id: str, event_type: str, endpoint: str = None,
                      tokens_input: int = 0, tokens_output: int = 0, cost: float = 0.0):
    """Track a usage event."""
