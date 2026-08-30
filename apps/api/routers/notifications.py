"""V61.0 — Notifications router for Aeryn API."""
from fastapi import APIRouter
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.platform.notification_system import get_notification_manager, get_scheduler, Notification
from aeryn_core.database.semantic_indexer import get_semantic_indexer
from aeryn_core.utils.error_recovery import get_error_recovery

router = APIRouter()

# ── Notification Endpoints ─────────────────────

@router.post("/notifications/create")
async def create_notification(user_id: str, title: str, message: str,
                               scheduled_for: str = None, priority: str = "normal",
                               channel: str = "all", metadata: dict = None):
    manager = get_notification_manager()
    notif = Notification(user_id=user_id, title=title, message=message,
                         scheduled_for=scheduled_for, priority=priority,
                         channel=channel, metadata=metadata)
    nid = manager.create(notif)
    return {"id": nid, "status": "created"}

@router.get("/notifications/due")
async def get_due_notifications(user_id: str = None, limit: int = 10):
    manager = get_notification_manager()
    return {"notifications": manager.get_due(user_id, limit)}

@router.get("/notifications/pending")
async def get_pending_notifications(user_id: str = None):
    manager = get_notification_manager()
    return {"notifications": manager.get_pending(user_id)}

@router.post("/notifications/cancel")
async def cancel_notification(notification_id: str):
    manager = get_notification_manager()
    success = manager.cancel(notification_id)
    return {"success": success}

@router.post("/search/index")
async def index_vault(force: bool = False):
    """Index all vault entries into semantic search."""
    indexer = get_semantic_indexer()
    result = indexer.index_vault(force=force)
    return result

@router.get("/search/advanced")
async def advanced_search(q: str, limit: int = 10):
    """Semantic search across indexed documents."""
    indexer = get_semantic_indexer()
    results = indexer.search(q, limit=limit)
    return {"query": q, "results": results, "count": len(results)}

@router.get("/search/stats")
async def search_stats():
    """Get semantic search statistics."""
    indexer = get_semantic_indexer()
    return indexer.get_stats()

# ── Error Recovery Endpoints ──────────────────

@router.get("/errors/recovery/stats")
async def error_recovery_stats():
    """Get error recovery statistics."""
    recovery = get_error_recovery()
    return recovery.get_stats()

@router.get("/errors/recovery/log")
async def error_log(limit: int = 50):
    """Get recent error log."""
    recovery = get_error_recovery()
    return {"errors": recovery.get_error_log(limit)}

@router.get("/errors/recovery/circuit-breakers")
async def circuit_breaker_states():
    """Get circuit breaker states."""
    recovery = get_error_recovery()
    return {"circuit_breakers": recovery.get_circuit_breaker_states()}

# ── Tool Runtime Endpoints ────────────────────
