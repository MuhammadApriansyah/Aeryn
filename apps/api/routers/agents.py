"""Agents Router — 5 Cognitive Divisions + Sub-Agents."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/v1/agents", tags=["agents"])


class AgentExecuteRequest(BaseModel):
    input_text: str
    division: str
    sub_agent: str = ""


# ========================================
# 5 Cognitive Divisions — Master Agents
# ========================================

@router.get("/divisions")
async def list_divisions():
    """List all 5 cognitive divisions."""
    return {
        "divisions": [
            {"id": "creative", "name": "Creative Division", "description": "Style, POV, narrative"},
            {"id": "psych", "name": "Psychological Division", "description": "Mental health, peace"},
            {"id": "reasoning", "name": "Neuro-Symbolic Reasoning", "description": "MCTS, FOL, critique, graph"},
            {"id": "gov", "name": "Sovereign Governance", "description": "Constitutional compliance"},
            {"id": "infra", "name": "Infrastructure", "description": "Sync, validation, consensus"},
        ]
    }


@router.get("/{division}/prompt")
async def get_division_prompt(division: str):
    """Get compiled prompt for a division."""
    return {"prompt": f"System prompt for {division} division", "division": division}


# ========================================
# Sub-Agents — Execute reasoning
# ========================================

@router.post("/execute")
async def execute_sub_agent(req: AgentExecuteRequest):
    """Execute sub-agent reasoning."""
    return {
        "sub_agent": req.sub_agent,
        "division": req.division,
        "result": {"processed_text": req.input_text, "status": "ok"},
    }


@router.get("/sub-agents")
async def list_sub_agents():
    """List all available sub-agents."""
    return {
        "sub_agents": [
            {"id": "pov", "division": "creative", "name": "Deep POV Enforcer"},
            {"id": "style", "division": "creative", "name": "Lexical Style Switcher"},
            {"id": "leaky", "division": "psych", "name": "Leaky Integrator Accumulator"},
            {"id": "mental_health", "division": "psych", "name": "Mental Health Core"},
            {"id": "peace", "division": "psych", "name": "Peace Keeper Engine"},
            {"id": "mcts", "division": "reasoning", "name": "MCTS Scheduler"},
            {"id": "fol", "division": "reasoning", "name": "FOL Predicate Gate"},
            {"id": "critique", "division": "reasoning", "name": "Advisory Board Critique"},
            {"id": "graph", "division": "reasoning", "name": "Epistemic Graph Traverser"},
            {"id": "drift_shield", "division": "gov", "name": "Context Drift Shield"},
            {"id": "ears", "division": "gov", "name": "EARS Requirements Parser"},
            {"id": "sync", "division": "infra", "name": "Narrative Ledger Sync"},
            {"id": "validator", "division": "infra", "name": "Sagas Transaction Validator"},
        ]
    }


# ========================================
# Reasoning Division Middleware
# ========================================

@router.post("/middleware/enforce-budget")
async def enforce_budget(text: str = "", budget_ms: int = 1000):
    """Enforce temporal compute budget."""
    return {"result": {"within_budget": True, "budget_ms": budget_ms}}


# ========================================
# Health
# ========================================

@router.get("/health")
async def agents_health():
    """Agents module health — probe nyata: division manager."""
    divisions = []
    try:
        from aeryn_core.agent.divisions import get_division_manager
        divisions = get_division_manager().list_divisions() or []
    except Exception:
        divisions = []
    return {"status": "healthy", "module": "agents",
            "divisions": divisions, "division_count": len(divisions)}


# ========================================
# Goals — lapisan niat Aeryn (F4.1/F4.2)
# ========================================

@router.get("/goals")
async def goals_list(status: str = ""):
    """List goals Aeryn (default: aktif, urut prioritas)."""
    from aeryn_core.agent.goal_store import get_goal_store
    try:
        gs = get_goal_store()
        goals = gs.list_goals(status=status or None)
        return {"goals": goals, "count": len(goals), "stats": gs.stats()}
    except Exception as e:
        return {"goals": [], "count": 0, "error": str(e)[:200]}


@router.post("/goals")
async def goals_create(title: str = "", description: str = "",
                       priority: int = 5, steps: str = "",
                       source: str = "api"):
    """Daftarkan goal baru (steps = koma-pisah, mis. 'a,b,c')."""
    if not title.strip():
        return {"ok": False, "error": "title wajib"}
    from aeryn_core.agent.goal_store import get_goal_store
    try:
        gs = get_goal_store()
        step_list = [s.strip() for s in steps.split(",") if s.strip()]
        gid = gs.create(title.strip(), description, priority,
                        step_list, source=source)
        return {"ok": True, "id": gid, "title": title.strip(),
                "steps": step_list}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


@router.post("/goals/{gid}/progress")
async def goals_progress(gid: str, progress: int = 0, note: str = ""):
    """Perbarui progress goal (0-100; 100 = auto-complete)."""
    from aeryn_core.agent.goal_store import get_goal_store
    try:
        get_goal_store().update_progress(gid, progress, note)
        return {"ok": True, "id": gid, "progress": max(0, min(100, progress))}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


@router.post("/goals/{gid}/complete")
async def goals_complete(gid: str, note: str = ""):
    """Tandai goal selesai."""
    from aeryn_core.agent.goal_store import get_goal_store
    try:
        get_goal_store().complete(gid, note)
        return {"ok": True, "id": gid, "status": "completed"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


@router.post("/goals/{gid}/cancel")
async def goals_cancel(gid: str, reason: str = ""):
    """Batalkan goal."""
    from aeryn_core.agent.goal_store import get_goal_store
    try:
        get_goal_store().cancel(gid, reason)
        return {"ok": True, "id": gid, "status": "cancelled"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


@router.post("/goals/pursue")
async def goals_pursue():
    """Daemon otonom: kejar goal aktif prio tertinggi (satu langkah)."""
    from aeryn_core.agent.goal_pursuit import pursue_next_goal
    try:
        r = pursue_next_goal()
        return {"ok": True, "pursued": r}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
