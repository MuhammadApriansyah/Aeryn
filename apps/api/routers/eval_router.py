"""Evaluation Router — evaluation metrics, benchmarks, diagnostics."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/v1/eval", tags=["evaluation"])


class RecordEvalRequest(BaseModel):
    episode_id: str
    task: str
    expected_outcome: str
    actual_output: str
    success: Optional[bool] = None
    milestones: List[str] = []
    achieved_milestones: List[str] = []
    expected_tools: List[str] = []
    actual_tools: List[str] = []


@router.post("/record")
async def record_eval(req: RecordEvalRequest):
    """Record an evaluation episode."""
    from aeryn_core.evaluation.harness import (
        get_eval_harness, EvalResult, score_success, score_progress, score_tool_selection
    )
    harness = get_eval_harness()

    # Auto-score if success not provided
    success = req.success if req.success is not None else score_success(req.expected_outcome, req.actual_output)
    progress = score_progress(req.milestones, req.achieved_milestones)
    tool_sel = score_tool_selection(req.expected_tools, req.actual_tools)

    result = EvalResult(
        episode_id=req.episode_id,
        task=req.task,
        expected_outcome=req.expected_outcome,
        success=success,
        progress_rate=progress,
        tool_selection_accuracy=tool_sel,
        parameter_accuracy=1.0,
        efficacy=0.5,
        expected_tools=req.expected_tools,
        actual_tools=req.actual_tools,
        milestones=req.milestones,
        achieved_milestones=req.achieved_milestones,
    )
    harness.record(result)
    return result.to_dict()


@router.get("/metrics")
async def get_metrics():
    """Get aggregate evaluation metrics."""
    from aeryn_core.evaluation.harness import get_eval_harness
    harness = get_eval_harness()
    return harness.get_metrics()


@router.get("/episodes")
async def list_episodes(limit: int = 50):
    """List evaluation episodes."""
    from aeryn_core.evaluation.harness import get_eval_harness
    harness = get_eval_harness()
    return {"episodes": harness.list_episodes(limit)}


@router.get("/benchmarks")
async def list_benchmarks():
    """List benchmark scenarios."""
    from aeryn_core.evaluation.benchmark import get_benchmark_suite
    suite = get_benchmark_suite()
    return {
        "scenarios": suite.list_scenarios(),
        "coverage": suite.category_coverage(),
    }


@router.post("/benchmarks/run")
async def run_benchmarks():
    """Run the full benchmark suite against the agent."""
    from aeryn_core.evaluation.benchmark import get_benchmark_suite
    from aeryn_core.agent.loop import AgentLoop
    suite = get_benchmark_suite()

    async def agent_runner(task: str):
        agent = AgentLoop()
        return await agent.run("benchmark", task)

    results = suite.run_suite(agent_runner)

    # Aggregate
    total = len(results)
    successes = sum(1 for r in results if r["success"])
    return {
        "results": results,
        "total": total,
        "successes": successes,
        "success_rate": round(successes / total, 3) if total else 0.0,
    }


@router.get("/diagnostics")
async def list_diagnostics(limit: int = 50):
    """List failure attributions."""
    from aeryn_core.evaluation.diagnostics import get_diagnostic_engine
    engine = get_diagnostic_engine()
    return {"attributions": engine.list_attributions(limit)}


@router.post("/diagnostics/attribute")
async def attribute_failure(episode_id: str = "", trace_id: str = ""):
    """Attribute a failure to a specific step."""
    from aeryn_core.evaluation.diagnostics import get_diagnostic_engine
    engine = get_diagnostic_engine()
    attribution = engine.attribute_failure(episode_id, trace_id)
    return attribution.to_dict()