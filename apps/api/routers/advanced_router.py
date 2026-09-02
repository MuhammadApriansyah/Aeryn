"""Advanced Router — divisions, plugins, planning, reflection."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/v1", tags=["advanced"])


# ========================================
# Divisions
# ========================================

class ExecuteDivisionRequest(BaseModel):
    message: str
    division: str = ""  # Empty = auto-classify
    session_id: str = "default"


@router.get("/divisions")
async def list_divisions():
    """List all 5 cognitive divisions."""
    from aeryn_core.agent.divisions import get_division_manager
    manager = get_division_manager()
    return {"divisions": manager.list_divisions()}


@router.post("/divisions/classify")
async def classify_message(message: str = ""):
    """Classify a message into a division."""
    from aeryn_core.agent.divisions import get_division_manager
    manager = get_division_manager()
    division_id = manager.classify(message)
    return {"division": division_id}


@router.post("/divisions/execute")
async def execute_division(req: ExecuteDivisionRequest):
    """Execute a message through a specific division."""
    from aeryn_core.agent.loop import AgentLoop
    
    agent = AgentLoop()
    result = await agent.run(req.session_id, req.message)
    return result


# ========================================
# Plugins
# ========================================

@router.get("/plugins/discover")
async def discover_plugins():
    """Discover available plugins."""
    from aeryn_core.plugins.loader import get_plugin_loader
    loader = get_plugin_loader()
    plugins = loader.discover()
    return {"plugins": plugins, "count": len(plugins)}


@router.post("/plugins/load")
async def load_plugins():
    """Load all plugins."""
    from aeryn_core.plugins.loader import get_plugin_loader
    from aeryn_core.tools import get_tool_registry
    loader = get_plugin_loader()
    registry = get_tool_registry()
    loaded = loader.load_all(registry)
    return {"loaded": list(loaded.keys()), "count": len(loaded)}


@router.post("/plugins/load/{name}")
async def load_plugin(name: str):
    """Load a specific plugin."""
    from aeryn_core.plugins.loader import get_plugin_loader
    from aeryn_core.tools import get_tool_registry
    loader = get_plugin_loader()
    registry = get_tool_registry()
    plugin = loader.load_plugin(name, registry)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")
    return {"plugin": name, "status": "loaded"}


# ========================================
# Planning
# ========================================

class PlanRequest(BaseModel):
    goal: str
    steps: Optional[List[str]] = None


@router.post("/plan")
async def make_plan(req: PlanRequest):
    """Create a plan."""
    from aeryn_core.agent.advanced import get_planner
    planner = get_planner()
    
    steps = req.steps or planner.decompose(req.goal)
    plan = planner.make_plan(req.goal, steps)
    return plan


@router.post("/plan/decompose")
async def decompose_goal(goal: str = ""):
    """Decompose a goal into steps."""
    from aeryn_core.agent.advanced import get_planner
    planner = get_planner()
    steps = planner.decompose(goal)
    return {"goal": goal, "steps": steps}


@router.get("/plan/{plan_id}")
async def get_plan(plan_id: int):
    """Get a plan by id."""
    from aeryn_core.agent.advanced import get_planner
    planner = get_planner()
    plan = planner.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


# ========================================
# Reflection
# ========================================

class ReflectionRequest(BaseModel):
    goal: str
    outcome: str
    strategy: str = ""


@router.post("/reflect")
async def reflect(req: ReflectionRequest):
    """Reflect on a task outcome."""
    from aeryn_core.agent.advanced import get_reflector
    reflector = get_reflector()
    result = reflector.reflect(req.goal, req.outcome, req.strategy)
    return result


@router.get("/reflect/recent")
async def recent_reflections(limit: int = 5):
    """Get recent reflections."""
    from aeryn_core.agent.advanced import get_reflector
    reflector = get_reflector()
    strategies = reflector.recent_strategies(limit)
    return {"reflections": strategies}


# ========================================
# Proactive
# ========================================

class ActionRequest(BaseModel):
    action: str


@router.post("/proactive/record")
async def record_action(req: ActionRequest):
    """Record a user action."""
    from aeryn_core.agent.advanced import get_proactive_engine
    engine = get_proactive_engine()
    engine.record_action(req.action)
    return {"status": "ok"}


@router.get("/proactive/suggest")
async def suggest_actions(limit: int = 5):
    """Suggest frequent actions."""
    from aeryn_core.agent.advanced import get_proactive_engine
    engine = get_proactive_engine()
    suggestions = engine.suggest(limit)
    return {"suggestions": suggestions}