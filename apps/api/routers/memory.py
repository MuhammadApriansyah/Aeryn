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
    tags = req.frontmatter.get("tags", []) if req.frontmatter else []
    links = req.frontmatter.get("links", []) if req.frontmatter else []
    if isinstance(tags, str):
        tags = [tags]
    if isinstance(links, str):
        links = [links]
    entry = VaultEntry(
        layer="Wiki",
        title=req.filename,
        body=req.content,
        tags=tags,
        links=links,
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
async def vault_search(query: str, limit: int = 10):
    """Search vault."""
    from aeryn_core.memory.vault import get_vault
    
    vault = get_vault()
    results = vault.search(query, limit=limit)
    
    return {"results": results, "count": len(results)}


@router.get("/vault/entries")
async def vault_entries(layer: str = ""):
    """List vault entries."""
    from aeryn_core.memory.vault import get_vault
    
    vault = get_vault()
    if layer:
        results = vault.list_layer(layer)
    else:
        results = vault.list_entries()
    
    return {"results": results, "count": len(results)}


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
    edge_type: str = "related"


@router.post("/graph/node")
async def graph_add_node(req: GraphNodeRequest):
    """Add a node to graph memory."""
    from aeryn_core.memory.graph_memory import get_graph_memory
    
    memory = get_graph_memory()
    result = memory.add_memory_node(req.node_id, req.label, req.node_type)
    
    return {"status": "ok", "result": result}


@router.post("/graph/edge")
async def graph_add_edge(req: GraphEdgeRequest):
    """Add an edge to graph memory."""
    from aeryn_core.memory.graph_memory import get_graph_memory
    
    memory = get_graph_memory()
    result = memory.add_edge(req.source, req.target, req.edge_type)
    
    return {"status": "ok", "result": result}


@router.get("/graph/neighbors/{node_id}")
async def graph_neighbors(node_id: str):
    """Get neighbors of a node."""
    from aeryn_core.memory.graph_memory import get_graph_memory
    
    memory = get_graph_memory()
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
    from aeryn_core.memory.hybrid_search import get_search_engine
    
    engine = get_search_engine()
    results = engine.search(query, limit)
    
    return {"results": results, "count": len(results)}


@router.post("/hybrid/index")
async def hybrid_index(content: str, metadata: Optional[Dict[str, str]] = None):
    """Index content for hybrid search."""
    from aeryn_core.memory.hybrid_search import get_search_engine
    
    engine = get_search_engine()
    result = engine.index_memory(content, metadata)
    
    return {"status": "ok", "result": result}


# ========================================
# Semantic Recall — Similarity-based
# ========================================

@router.get("/semantic/recall")
async def semantic_recall(query: str, limit: int = 5):
    """Semantic recall."""
    from aeryn_core.memory.semantic_recall import SemanticRecall
    
    recall = SemanticRecall()
    results = recall.recall(query, limit)
    
    return {"results": results, "count": len(results)}


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
    result = memory.know_person(req.person_id, req.name, req.metadata)
    
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
async def consolidate_run():
    """Run memory consolidation."""
    from aeryn_core.memory.memory_consolidation import MemoryConsolidator
    
    consolidator = MemoryConsolidator()
    result = consolidator.consolidate()
    
    return {"status": "ok", "result": result}


@router.get("/consolidate/should")
async def consolidate_should():
    """Check if consolidation should run."""
    from aeryn_core.memory.memory_consolidation import MemoryConsolidator
    
    consolidator = MemoryConsolidator()
    should = consolidator.should_consolidate()
    
    return {"should_consolidate": should}


# ========================================
# Memory Curation
# ========================================

@router.post("/curate/run")
async def curate_run(strategy: str = "all"):
    """Run memory curation."""
    from aeryn_core.memory.memory_curator import MemoryCurator
    
    curator = MemoryCurator()
    result = curator.curate_strategies(strategy)
    
    return {"status": "ok", "result": result}


# ========================================
# Supersession — Version control
# ========================================

@router.post("/supersede")
async def supersede(content_id: str, new_content: str):
    """Supersede old content."""
    from aeryn_core.memory.supersession import get_supersession_manager
    
    manager = get_supersession_manager()
    result = manager.supersede(content_id, new_content)
    
    return {"status": "ok", "result": result}


@router.get("/supersede/{content_id}")
async def get_superseded(content_id: str):
    """Get superseded versions."""
    from aeryn_core.memory.supersession import get_supersession_manager
    
    manager = get_supersession_manager()
    chain = manager.get_superseded_chain(content_id)
    
    return {"chain": chain}


# ========================================
# Memory Canary — Integrity checking
# ========================================

@router.post("/canary/plant")
async def canary_plant(marker: str = ""):
    """Plant a canary."""
    from aeryn_core.memory.memory_canary import plant
    
    result = plant(marker)
    
    return {"status": "ok", "result": result}


@router.get("/canary/probe")
async def canary_probe():
    """Probe canaries."""
    from aeryn_core.memory.memory_canary import probe
    
    results = probe()
    
    return {"results": results}


# ========================================
# Session History
# ========================================

@router.post("/session/record")
async def session_record(role: str, content: str):
    """Record a session message."""
    from aeryn_core.memory.session_history import record
    
    result = record(role, content)
    
    return {"status": "ok", "result": result}


@router.get("/session/history")
async def session_history(limit: int = 20):
    """Get session history."""
    from aeryn_core.memory.session_history import load
    
    history = load(limit)
    
    return {"history": history, "count": len(history)}


@router.get("/session/turns")
async def session_turns():
    """Get turn count."""
    from aeryn_core.memory.session_history import turn_count
    
    count = turn_count()
    
    return {"turns": count}


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
async def entity_resolve(name: str):
    """Resolve an entity."""
    from aeryn_core.memory.entity_resolution import get_entity_resolver
    
    resolver = get_entity_resolver()
    result = resolver.resolve(name)
    
    return {"result": result}


# ========================================
# Enhanced Memory
# ========================================

@router.post("/enhanced/extract")
async def enhanced_extract(text: str):
    """Extract entities from text."""
    from aeryn_core.memory.enhanced_memory import get_entity_extractor
    
    extractor = get_entity_extractor()
    result = extractor.extract(text)
    
    return {"entities": result}


@router.post("/enhanced/learn")
async def enhanced_learn(user_id: str, preference: str, value: str):
    """Learn user preference."""
    from aeryn_core.memory.enhanced_memory import get_preference_learner
    
    learner = get_preference_learner()
    result = learner.learn(user_id, preference, value)
    
    return {"status": "ok", "result": result}


@router.get("/enhanced/preferences/{user_id}")
async def enhanced_preferences(user_id: str):
    """Get user preferences."""
    from aeryn_core.memory.enhanced_memory import get_preference_learner
    
    learner = get_preference_learner()
    prefs = learner.get_preferences(user_id)
    
    return {"preferences": prefs}


# ========================================
# Memory Learning
# ========================================

@router.post("/learn/interaction")
async def learn_interaction(user_id: str, interaction: str):
    """Process interaction for learning."""
    from aeryn_core.memory.memory_learning import get_memory_learner
    
    learner = get_memory_learner()
    result = learner.process_interaction(user_id, interaction)
    
    return {"status": "ok", "result": result}


@router.get("/learn/context/{user_id}")
async def learn_context(user_id: str):
    """Get user context."""
    from aeryn_core.memory.memory_learning import get_memory_learner
    
    learner = get_memory_learner()
    context = learner.get_user_context(user_id)
    
    return {"context": context}


# ========================================
# Health
# ========================================

@router.get("/health")
async def memory_health():
    """Memory module health check."""
    return {"status": "healthy", "module": "memory"}
