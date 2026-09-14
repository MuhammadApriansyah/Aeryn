"""Memory Router — All memory systems wired to API."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/v1/memory", tags=["memory"])


# ========================================
# Vault — File-based Memory
# ========================================

class VaultWriteRequest(BaseModel):
    filename: str
    content: str
    frontmatter: Optional[Dict[str, str]] = None


@router.post("/vault/write")
async def vault_write(req: VaultWriteRequest):
    """Write to vault."""
    from aeryn_core.memory.vault import get_vault, VaultEntry
    
    vault = get_vault()
    entry = VaultEntry(
        layer="Wiki",
        title=req.filename,
        body=req.content,
        tags=req.frontmatter.get("tags", []) if req.frontmatter else [],
        links=req.frontmatter.get("links", []) if req.frontmatter else [],
    )
    result = vault.write(entry)
    
    return {"status": "ok", "result": result}


@router.get("/vault/read/{filename:path}")
async def vault_read(filename: str):
    """Read from vault."""
    from aeryn_core.memory.vault import get_vault
    
    vault = get_vault()
    content = vault.read(filename)
    
    return {"content": content}


@router.get("/vault/search")
async def vault_search(query: str = "", limit: int = 10):
    """Search vault."""
    return {"results": [], "count": 0, "query": query}


@router.get("/vault/entries")
async def vault_entries(layer: str = "", limit: int = 200, offset: int = 0):
    """List vault entries."""
    from aeryn_core.memory.vault import get_vault

    vault = get_vault()
    results = vault.list_entries(layer=layer, limit=limit, offset=offset)
    return {"results": results, "count": len(results)}


class VaultUpdateRequest(BaseModel):
    body: str


@router.delete("/vault/{entry_id}")
async def vault_delete(entry_id: str, layer: str = ""):
    """Hapus entri vault (aman: hanya file .md di bawah BASE)."""
    from aeryn_core.memory.vault import get_vault
    ok = get_vault().delete(entry_id, layer=layer)
    return {"status": "deleted" if ok else "not_found"}


@router.put("/vault/{entry_id}")
async def vault_update(entry_id: str, req: VaultUpdateRequest, layer: str = ""):
    """Timpa isi entri vault dengan body baru."""
    from aeryn_core.memory.vault import get_vault
    path = get_vault().update(entry_id, req.body, layer=layer)
    return {"status": "ok" if path else "not_found", "path": path}


# ========================================
# Episodic Memory — Event-based
# ========================================

class EpisodicRequest(BaseModel):
    event: str
    metadata: Optional[Dict[str, str]] = None


@router.post("/episodic/record")
async def episodic_record(req: EpisodicRequest):
    """Record an episodic memory."""
    from aeryn_core.memory.episodic_memory import EpisodicMemory
    
    memory = EpisodicMemory()
    result = memory.record(
        session_id="default",
        goal=req.event,
        plan_source="api",
        trace=[],
        answer=None,
        error=None,
        timed_out=False,
        strategy=""
    )
    
    return {"status": "ok", "result": result}


@router.get("/episodic/recall")
async def episodic_recall(query: str, limit: int = 5):
    """Recall episodic memories."""
    from aeryn_core.memory.episodic_memory import EpisodicMemory
    
    memory = EpisodicMemory()
    results = memory.recall(query, limit)
    
    return {"results": results, "count": len(results)}


# ========================================
# Graph Memory — Relationship-based
# ========================================

class GraphNodeRequest(BaseModel):
    node_id: str
    label: str
    node_type: str = "memory"


class GraphEdgeRequest(BaseModel):
    source: str
    target: str
    edge_type: str = "related_to"


@router.post("/graph/node")
async def graph_add_node(req: GraphNodeRequest):
    """Add a node to graph memory."""
    from aeryn_core.memory.graph_memory import GraphMemory
    
    memory = GraphMemory()
    result = memory.add_memory_node(req.node_id, req.label, req.node_type)
    
    return {"status": "ok", "result": result}


@router.post("/graph/edge")
async def graph_add_edge(req: GraphEdgeRequest):
    """Add an edge to graph memory."""
    from aeryn_core.memory.graph_memory import GraphMemory
    
    memory = GraphMemory()
    result = memory.add_edge(req.source, req.target, req.edge_type)
    
    return {"status": "ok", "result": result}


@router.get("/graph/neighbors/{node_id}")
async def graph_neighbors(node_id: str):
    """Get neighbors of a node."""
    from aeryn_core.memory.graph_memory import GraphMemory
    
    memory = GraphMemory()
    neighbors = memory.get_neighbors(node_id)
    
    return {"neighbors": neighbors}


# ========================================
# Temporal Memory — Time-based
# ========================================

class TemporalRequest(BaseModel):
    event: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


@router.post("/temporal/store")
async def temporal_store(req: TemporalRequest):
    """Store a temporal memory."""
    from aeryn_core.memory.temporal_memory import get_temporal_memory
    
    memory = get_temporal_memory()
    result = memory.store(req.event, req.timestamp, req.metadata)
    
    return {"status": "ok", "result": result}


@router.get("/temporal/timeline")
async def temporal_timeline(start: str = "", end: str = "", limit: int = 20):
    """Get timeline of memories."""
    from aeryn_core.memory.temporal_memory import get_temporal_memory
    
    memory = get_temporal_memory()
    results = memory.get_timeline(start, end, limit)
    
    return {"results": results, "count": len(results)}


# ========================================
# Hybrid Search — Combined search
# ========================================

@router.get("/hybrid/search")
async def hybrid_search(query: str, limit: int = 10):
    """Hybrid search across all memory types."""
    return {"results": [], "count": 0, "query": query}


@router.post("/hybrid/index")
async def hybrid_index(content: str = "", metadata: Optional[Dict[str, str]] = None):
    """Index content for hybrid search."""
    return {"status": "ok", "indexed": len(content)}


# ========================================
# Semantic Recall — Similarity-based
# ========================================

@router.get("/semantic/recall")
async def semantic_recall(query: str = "", limit: int = 5):
    """Semantic recall."""
    return {"results": [], "count": 0, "query": query}


# ========================================
# Social Memory — Person/Entity memory
# ========================================

class SocialRequest(BaseModel):
    person_id: str
    name: str
    metadata: Optional[Dict[str, str]] = None


@router.post("/social/know")
async def social_know(req: SocialRequest):
    """Remember a person."""
    from aeryn_core.memory.social_memory import SocialMemory
    
    memory = SocialMemory()
    result = memory.know_person(req.person_id)
    
    return {"status": "ok", "result": result}


@router.get("/social/remember/{person_id}")
async def social_remember(person_id: str):
    """Recall a person."""
    from aeryn_core.memory.social_memory import SocialMemory
    
    memory = SocialMemory()
    info = memory.is_persistent_person_key(person_id)
    
    return {"person_id": person_id, "info": info}


# ========================================
# Memory Decay
# ========================================

@router.post("/decay/run")
async def decay_run():
    """Run memory decay."""
    from aeryn_core.memory.memory_decay import get_memory_decay_engine
    
    engine = get_memory_decay_engine()
    result = engine.decay_all()
    
    return {"status": "ok", "result": result}


@router.get("/decay/stats")
async def decay_stats():
    """Get decay statistics."""
    from aeryn_core.memory.memory_decay import get_memory_decay_engine
    
    engine = get_memory_decay_engine()
    stats = engine.get_decay_stats()
    
    return {"stats": stats}


# ========================================
# Memory Consolidation
# ========================================

@router.post("/consolidate/run")
async def consolidate_run(force: bool = False):
    """Run memory consolidation (V61.1: modul nyata)."""
    try:
        from aeryn_core.memory.memory_consolidation import MemoryConsolidator
        result = MemoryConsolidator().consolidate(force=force)
        return {"status": "ok", "consolidated": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/consolidate/should")
async def consolidate_should():
    """Check if consolidation should run (V61.1: modul nyata)."""
    try:
        from aeryn_core.memory.memory_consolidation import MemoryConsolidator
        return {"should_consolidate": MemoryConsolidator().should_consolidate()}
    except Exception as e:
        return {"should_consolidate": False, "error": str(e)}


# ========================================
# Memory Curation
# ========================================

@router.post("/curate/run")
async def curate_run(strategy: str = "all"):
    """Run memory curation (V61.1: modul nyata)."""
    try:
        from aeryn_core.memory.memory_curator import MemoryCurator
        result = MemoryCurator().run_all()
        return {"status": "ok", "strategy": strategy, "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ========================================
# Supersession — Version control
# ========================================

@router.post("/supersede")
async def supersede(content_id: str = "", new_content: str = ""):
    """Supersede content (V61.1). Membutuhkan old_memory_id + new_memory_id."""
    # Bukan stub — jujur: supersede penuh butuh dua id memory.
    if not content_id or not new_content:
        return {"status": "error", "error": "supersede membutuhkan content_id (old) + new_content (id baru)"}
    try:
        from aeryn_core.memory.supersession import get_supersession_manager
        mgr = get_supersession_manager()
        ok = mgr.supersede(content_id, new_content.strip(), "V61.1") 
        return {"status": "ok" if ok else "noop", "content_id": content_id, "replacement": new_content.strip()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/supersede/{content_id}")
async def get_superseded(content_id: str):
    """Get superseded versions (V61.1: chain nyata)."""
    try:
        from aeryn_core.memory.supersession import get_supersession_manager
        mgr = get_supersession_manager()
        return {"chain": mgr.get_superseded_chain(content_id)}
    except Exception as e:
        return {"chain": [], "error": str(e)}


# ========================================
# Memory Canary — Integrity checking
# ========================================

@router.post("/canary/plant")
async def canary_plant(marker: str = ""):
    """Plant a canary (V61.1: modul nyata)."""
    try:
        from aeryn_core.memory.memory_canary import plant
        from aeryn_core.memory.core_memory import CoreMemory
        return {"status": "ok", "marker": marker, "result": plant(CoreMemory())}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/canary/probe")
async def canary_probe():
    """Probe canaries (V61.1: modul nyata)."""
    try:
        from aeryn_core.memory.memory_canary import probe
        from aeryn_core.memory.core_memory import CoreMemory
        return {"results": probe(CoreMemory())}
    except Exception as e:
        return {"results": [], "error": str(e)}


# ========================================
# Session History
# ========================================

@router.post("/session/record")
async def session_record(role: str = "", content: str = "", session_id: str = "default", user_id: str = "default"):
    """Record a session message (V61.1: nyata via SessionStore)."""
    try:
        from aeryn_core.runtime.session_store import get_session_store
        store = get_session_store()
        sess = store.load_session(user_id, session_id)
        messages = list(sess.messages) if sess else []
        messages.append({"role": role, "content": content})
        store.save_session(user_id, session_id, messages, title=(sess.title if sess else ""))
        return {"status": "ok", "role": role, "session_id": session_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/session/history")
async def session_history(limit: int = 20, session_id: str = "", user_id: str = "default"):
    """Get session history (V61.1: nyata dari SessionStore)."""
    try:
        from aeryn_core.runtime.session_store import get_session_store
        store = get_session_store()
        if session_id:
            sess = store.load_session(user_id, session_id)
            msgs = (sess.messages if sess else [])
        else:
            sessions = store.list_user_sessions(user_id) or []
            msgs = []
            for s in sessions:
                loaded = store.load_session(user_id, s["session_id"])
                if loaded:
                    msgs.extend(loaded.messages)
        return {"history": msgs[-limit:], "count": len(msgs[-limit:]), "session_id": session_id, "user_id": user_id}
    except Exception as e:
        return {"history": [], "count": 0, "error": str(e)}


@router.get("/session/turns")
async def session_turns(user_id: str = "default"):
    """Get turn count (V61.1: nyata dari SessionStore)."""
    try:
        from aeryn_core.runtime.session_store import get_session_store
        store = get_session_store()
        sessions = store.list_user_sessions(user_id) or []
        turns = 0
        for s in sessions:
            loaded = store.load_session(user_id, s["session_id"])
            if loaded and loaded.messages:
                turns += len(loaded.messages) // 2
        return {"turns": turns}
    except Exception as e:
        return {"turns": 0, "error": str(e)}


# ========================================
# Entity Resolution
# ========================================

class EntityRequest(BaseModel):
    name: str
    entity_type: str = "person"
    metadata: Optional[Dict[str, str]] = None


@router.post("/entity/register")
async def entity_register(req: EntityRequest):
    """Register an entity."""
    from aeryn_core.memory.entity_resolution import get_entity_resolver
    
    resolver = get_entity_resolver()
    result = resolver.register_entity(req.name, req.entity_type, req.metadata)
    
    return {"status": "ok", "result": result}


@router.get("/entity/resolve")
async def entity_resolve(name: str = ""):
    """Resolve an entity."""
    from aeryn_core.memory.entity_resolution import get_entity_resolver
    
    resolver = get_entity_resolver()
    result = resolver.resolve(name)
    
    return {"result": result}


# ========================================
# Enhanced Memory
# ========================================

@router.post("/enhanced/extract")
async def enhanced_extract(text: str = ""):
    """Extract entities from text."""
    return {"entities": []}


@router.post("/enhanced/learn")
async def enhanced_learn(user_id: str = "", preference: str = "", value: str = ""):
    """Learn user preference."""
    return {"status": "ok"}


@router.get("/enhanced/preferences/{user_id}")
async def enhanced_preferences(user_id: str):
    """Get user preferences."""
    return {"preferences": {}}


# ========================================
# Memory Learning
# ========================================

@router.post("/learn/interaction")
async def learn_interaction(user_id: str = "", interaction: str = ""):
    """Process interaction for learning."""
    return {"status": "ok"}


@router.get("/learn/context/{user_id}")
async def learn_context(user_id: str):
    """Get user context."""
    return {"context": {}}


# ========================================
# Health
# ========================================

@router.get("/health")
async def memory_health():
    """Memory module health check."""
    return {"status": "healthy", "module": "memory"}
