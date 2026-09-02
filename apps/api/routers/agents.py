"""Agents Router — 5 Cognitive Divisions + Sub-Agents."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/v1/agents", tags=["agents"])


class AgentExecuteRequest(BaseModel):
    input_text: str
    division: str
    sub_agent: str = ""


class MiddlewareRequest(BaseModel):
    text: str
    budget_ms: int = 1000


# ========================================
# 5 Cognitive Divisions — Master Agents
# ========================================

@router.get("/divisions")
async def list_divisions():
    """List all 5 cognitive divisions."""
    return {
        "divisions": [
            {"id": "creative", "name": "Creative Division", "description": "Style, POV, narrative"},
            {"id": "psych", "name": "Psychological Division", "description": "Mental health, peace, leaky integration"},
            {"id": "reasoning", "name": "Neuro-Symbolic Reasoning", "description": "MCTS, FOL, critique, graph"},
            {"id": "gov", "name": "Sovereign Governance", "description": "Constitutional compliance, requirements"},
            {"id": "infra", "name": "Infrastructure", "description": "Sync, validation, consensus"},
        ]
    }


@router.get("/{division}/prompt")
async def get_division_prompt(division: str):
    """Get compiled prompt for a division."""
    if division == "creative":
        from aeryn_core.agents.division_1_creative.master_agent import CreativeDivisionDirector
        agent = CreativeDivisionDirector()
        return {"prompt": agent.compile_sovereign_system_prompt_node("", "{}", [], "")}
    elif division == "psych":
        from aeryn_core.agents.division_2_psych.master_agent import PsychologicalAmigdalaOrchestrator
        agent = PsychologicalAmigdalaOrchestrator()
        return {"prompt": agent.compile_psychological_vector_payload([], [], [])}
    elif division == "reasoning":
        from aeryn_core.agents.division_3_reasoning.master_agent import NeuroSymbolicReasoningDirector
        agent = NeuroSymbolicReasoningDirector()
        return {"prompt": agent.compile_reasoning_vector_payload([], "", 3)}
    elif division == "gov":
        from aeryn_core.agents.division_4_gov.master_agent import SovereignGovernanceDirector
        agent = SovereignGovernanceDirector()
        return {"prompt": agent.verify_constitutional_compliance("")}
    elif division == "infra":
        from aeryn_core.agents.division_5_infra.master_agent import TransactionConsensusDirector
        agent = TransactionConsensusDirector()
        return {"prompt": agent.execute_infrastructure_accounting_sync("")}
    else:
        raise HTTPException(404, f"Division {division} not found")


# ========================================
# Sub-Agents — Execute reasoning
# ========================================

@router.post("/execute")
async def execute_sub_agent(req: AgentExecuteRequest):
    """Execute sub-agent reasoning."""
    sub_agents = {
        # Creative
        "pov": ("agents.division_1_creative.sub_agent_pov.agent", "SubAgentDeepPovEnforcer"),
        "style": ("agents.division_1_creative.sub_agent_style.agent", "SubAgentLexicalStyleSwitcher"),
        # Psych
        "leaky": ("agents.division_2_psych.sub_agents_real", "SubAgentLeakyIntegratorAccumulator"),
        "mental_health": ("agents.division_2_psych.sub_agents_real", "SubAgentMentalHealthCore"),
        "peace": ("agents.division_2_psych.sub_agents_real", "SubAgentPeaceKeeperEngine"),
        # Reasoning
        "mcts": ("agents.division_3_reasoning.sub_agent_mcts.agent", "SubAgentMonteCarloTreeSearchScheduler"),
        "fol": ("agents.division_3_reasoning.sub_agent_fol.agent", "SubAgentFirstOrderLogicPredicateGate"),
        "critique": ("agents.division_3_reasoning.sub_agent_critique.agent", "SubAgentAdvisoryBoardMonologueCritique"),
        "graph": ("agents.division_3_reasoning.sub_agent_graph.agent", "SubAgentEpistemicGraphTraverser"),
        # Governance
        "drift_shield": ("agents.division_4_gov.sub_agents_real", "SubAgentContextDriftShield"),
        "ears": ("agents.division_4_gov.sub_agents_real", "SubAgentEarsRequirementsParser"),
        # Infrastructure
        "sync": ("agents.division_5_infra.sub_agent_sync.agent", "SubAgentNarrativeLedgerSynchronizer"),
        "validator": ("agents.division_5_infra.sub_agent_validator.agent", "SubAgentSagasTransactionValidator"),
    }
    
    if req.sub_agent not in sub_agents:
        raise HTTPException(404, f"Sub-agent {req.sub_agent} not found")
    
    module_path, class_name = sub_agents[req.sub_agent]
    
    import importlib
    module = importlib.import_module(f"aeryn_core.{module_path}")
    agent_class = getattr(module, class_name)
    agent = agent_class()
    
    result = agent.execute_sub_brain_reasoning(req.input_text)
    
    return {
        "sub_agent": req.sub_agent,
        "division": req.division,
        "result": result,
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
async def enforce_budget(req: MiddlewareRequest):
    """Enforce temporal compute budget."""
    from aeryn_core.agents.division_3_reasoning.middleware import ReasoningDivisionMiddleware
    
    middleware = ReasoningDivisionMiddleware()
    result = middleware.enforce_temporal_compute_budget(req.text, req.budget_ms)
    
    return {"result": result}


# ========================================
# Health
# ========================================

@router.get("/health")
async def agents_health():
    """Agents module health check."""
    return {"status": "healthy", "module": "agents"}
