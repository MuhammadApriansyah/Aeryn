"""V61.1 — Bitemporal knowledge graph HTTP API."""
from fastapi import APIRouter, Query, Body
from pydantic import BaseModel, Field

router = APIRouter()


class FactIn(BaseModel):
    entity: str = Field(..., description="Subject (mis. 'sen', 'aeryn')")
    predicate: str = Field(..., description="Relation (mis. 'prefers_color')")
    fact: str = Field(..., description="Statement / value")
    source: str = None
    confidence: float = 1.0
    valid_from: str = None
    valid_to: str = None


@router.post("/facts")
async def record_fact(body: FactIn):
    """Record a (new version of a) fact — bitemporal update."""
    from aeryn_core.memory.fact_store import get_fact_store
    store = get_fact_store()
    fid = store.record(body.entity, body.predicate, body.fact,
                       source=body.source, confidence=body.confidence,
                       valid_from=body.valid_from, valid_to=body.valid_to)
    return {"status": "recorded", "fact_id": fid, "entity": body.entity,
            "predicate": body.predicate}


@router.get("/facts/entities")
async def fact_entities():
    """All entities known to the knowledge graph."""
    from aeryn_core.memory.fact_store import get_fact_store
    store = get_fact_store()
    return {"entities": store.entities()}


class EvalIn(BaseModel):
    name: str = ""
    description: str = ""
    trigger: str = ""
    expertise: str = ""
    examples: list = []
    source: str = "api"


@router.post("/evolution/evaluate")
async def skill_evolve(body: EvalIn):
    """Evaluate a candidate skill (B2) — returns verdict + records to fact graph."""
    from aeryn_core.adaptive.skill_evolution import SkillCandidate, evolve
    cand = SkillCandidate(
        name=body.name,
        description=body.description,
        trigger=body.trigger,
        expertise=body.expertise,
        examples=body.examples,
        source=body.source,
    )
    return evolve(cand)


@router.get("/facts/{entity}")
async def get_facts(entity: str, predicate: str = None, as_of: str = None):
    """Get facts for an entity (as-of now, or at a given valid time)."""
    from aeryn_core.memory.fact_store import get_fact_store
    store = get_fact_store()
    facts = store.as_of(entity, predicate, at=as_of) if as_of else store.current(entity, predicate)
    return {"entity": entity, "facts": facts}


@router.get("/facts/{entity}/history")
async def fact_history(entity: str, predicate: str = None):
    """Full audit trail of an entity's facts (all versions)."""
    from aeryn_core.memory.fact_store import get_fact_store
    store = get_fact_store()
    return {"entity": entity, "history": store.history(entity, predicate)}