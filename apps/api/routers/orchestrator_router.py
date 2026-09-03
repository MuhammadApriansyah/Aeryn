"""Multi-Agent Orchestrator Router — supervisor, handoff, blackboard, parallel."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/v1/orchestrate", tags=["multi-agent"])


class OrchestrateRequest(BaseModel):
    task: str
    division: str = ""  # empty = auto-route


class HandoffRequest(BaseModel):
    from_division: str
    to_division: str
    task: str
    context: Optional[Dict[str, Any]] = None


class ParallelRequest(BaseModel):
    tasks: Dict[str, str]  # {division_id: task_text}


@router.post("/route")
async def route_task(task: str = ""):
    """Route a task to the best division."""
    from aeryn_core.multi_agent.orchestrator import get_supervisor
    supervisor = get_supervisor()
    division_id = await supervisor.route(task)
    return {"division": division_id, "task": task}


@router.post("/execute")
async def execute_task(req: OrchestrateRequest):
    """Orchestrate a task through the best division."""
    from aeryn_core.multi_agent.orchestrator import get_supervisor
    from aeryn_core.agent.loop import AgentLoop
    supervisor = get_supervisor()

    async def agent_runner(division_id: str, task: str):
        # Force a specific division by pre-classifying
        agent = AgentLoop()
        return await agent.run("orchestrate_" + division_id, task)

    result = await supervisor.orchestrate(req.task, agent_runner)
    return result


@router.post("/handoff")
async def handoff_task(req: HandoffRequest):
    """Hand off a task between divisions."""
    from aeryn_core.multi_agent.orchestrator import get_supervisor
    supervisor = get_supervisor()
    handoff = await supervisor.handoff(
        req.from_division, req.to_division, req.task, req.context
    )
    return handoff.to_dict()


@router.post("/broadcast")
async def broadcast(sender: str = "supervisor", message: str = ""):
    """Broadcast a message to all divisions."""
    from aeryn_core.multi_agent.orchestrator import get_supervisor
    supervisor = get_supervisor()
    recipients = await supervisor.broadcast(sender, message)
    return {"recipients": recipients, "message": message}


@router.post("/parallel")
async def run_parallel(req: ParallelRequest):
    """Run multiple divisions in parallel."""
    from aeryn_core.multi_agent.orchestrator import get_supervisor, ParallelOrchestrator
    from aeryn_core.agent.loop import AgentLoop
    supervisor = get_supervisor()
    orchestrator = ParallelOrchestrator(supervisor)

    async def agent_runner(division_id: str, task: str):
        agent = AgentLoop()
        return await agent.run("parallel_" + division_id, task)

    results = await orchestrator.run_parallel(req.tasks, agent_runner)
    return {"results": results}


@router.get("/metrics")
async def get_metrics():
    """Get multi-agent collaboration metrics."""
    from aeryn_core.multi_agent.orchestrator import get_supervisor
    supervisor = get_supervisor()
    return supervisor.get_metrics()


@router.get("/blackboard")
async def get_blackboard():
    """Read shared blackboard state."""
    from aeryn_core.multi_agent.orchestrator import get_supervisor
    supervisor = get_supervisor()
    entries = await supervisor.blackboard.read_all()
    return {"blackboard": entries}