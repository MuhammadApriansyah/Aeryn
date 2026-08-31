"""PostgreSQL Memory Plugin API Routes."""
from fastapi import APIRouter, Query
from typing import Optional, List
import asyncio

router = APIRouter()

# Lazy import to avoid startup errors if PG unavailable
_plugin = None

def _get_plugin():
    global _plugin
    if _plugin is None:
        from . import get_postgres_memory
        _plugin = get_postgres_memory()
    return _plugin


@router.get("/postgres-memory/stats")
async def pg_stats():
    """Get PostgreSQL memory statistics."""
    try:
        plugin = _get_plugin()
        stats = await plugin.get_stats()
        return {"status": "ok", **stats}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/postgres-memory/remember")
async def pg_remember(body: dict):
    """Store a memory. Skip embedding for fast response."""
    try:
        plugin = _get_plugin()
        key = body.get("key")
        value = body.get("value")
        if not key or not value:
            return {"error": "key and value required"}
        
        memory_type = body.get("type", "fact")
        importance = body.get("importance", 0.5)
        entities = body.get("entities")
        ttl_days = body.get("ttl_days")
        skip_embedding = body.get("skip_embedding", True)  # Default: fast mode
        
        id_ = await plugin.remember(key, value, memory_type, importance, 
                                    body.get("session_id"), entities, ttl_days,
                                    skip_embedding=skip_embedding)
        return {"status": "ok", "id": id_}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/postgres-memory/index")
async def pg_index():
    """Generate embeddings for un-indexed memories. Call periodically."""
    try:
        plugin = _get_plugin()
        count = await plugin.index_unindexed()
        return {"status": "ok", "indexed": count}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/postgres-memory/recall")
async def pg_recall(q: str = "", limit: int = 10):
    """Search memories."""
    try:
        plugin = _get_plugin()
        results = await plugin.recall(q, limit)
        return {"status": "ok", "query": q, "results": results, "count": len(results)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/postgres-memory/sessions")
async def pg_sessions(q: str = "", limit: int = 5):
    """Search sessions."""
    try:
        plugin = _get_plugin()
        results = await plugin.search_sessions(q, limit)
        return {"status": "ok", "query": q, "results": results, "count": len(results)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/postgres-memory/session")
async def pg_save_session(body: dict):
    """Save session summary."""
    try:
        plugin = _get_plugin()
        session_id = body.get("session_id")
        summary = body.get("summary")
        if not session_id or not summary:
            return {"error": "session_id and summary required"}
        
        importance = body.get("importance", 0.5)
        tags = body.get("tags", [])
        metadata = body.get("metadata")
        
        id_ = await plugin.save_session(session_id, summary, importance, tags, metadata)
        return {"status": "ok", "id": id_}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.delete("/postgres-memory/forget")
async def pg_forget(key: str):
    """Remove a memory."""
    try:
        plugin = _get_plugin()
        success = await plugin.forget(key)
        return {"status": "ok" if success else "not_found"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
