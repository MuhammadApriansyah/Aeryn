#!/usr/bin/env python3
"""V62.2 — FW2.1: Multi-agent orchestration wired ke AgentLoop.

Supervisor menerima task kompleks → klasifikasi per-subtask ke division
agents → dispatch PARALEL (isolated contexts via asyncio.gather) →
konsolidasi hasil. E2E: 2 worker jalan bersamaan.
Real APIs only — no test doubles.
"""

import os
import sys
import asyncio
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

REPO = os.environ.get(
    "AERYN_REPO",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."),
)
REPO = os.path.abspath(REPO)
if REPO not in sys.path:
    sys.path.insert(0, REPO)


async def _run_division_agent(division_id: str, subtask: str, session_id: str) -> Dict[str, Any]:
    """Run one division agent on a subtask via AgentLoop (isolated session)."""
    from aeryn_core.agent.loop import AgentLoop

    # Isolated session: fw2/<division>-<timestamp> — context tak tercampur
    iso_session = f"fw2/{division_id}-{int(datetime.now().timestamp())}"
    agent = AgentLoop()
    try:
        resp = await agent.run(iso_session, subtask, user_id="system-fw2")
        return {
            "division": division_id,
            "subtask": subtask[:200],
            "content": resp.get("content", ""),
            "iterations": resp.get("iterations", 0),
            "status": "ok",
            "session": iso_session,
        }
    except Exception as e:
        return {
            "division": division_id,
            "subtask": subtask[:200],
            "content": "",
            "status": "error",
            "error": str(e)[:300],
            "session": iso_session,
        }


def _split_subtasks(task: str) -> List[str]:
    """Split a complex task into subtasks.

    Patterns: numbered lists ("1. ... 2. ..."), "dan"/"lalu"/"kemudian"
    separators between imperative clauses, else single task.
    """
    # Numbered list: "1. X 2. Y"
    numbered = re.split(r"\s*\d+[\.\)]\s+", task)
    if len(numbered) > 2:
        return [s.strip() for s in numbered[1:] if s.strip()]

    # Coordinating separators: "X dan Y", "X lalu Y", "X kemudian Y"
    parts = re.split(r"\s+(?:lalu|kemudian)\s+", task)
    if len(parts) > 1:
        return [p.strip() for p in parts if p.strip()]

    # "dan" only if both sides are imperative-ish (>4 words each)
    parts = re.split(r"\s+dan\s+", task)
    if len(parts) > 1 and all(len(p.split()) >= 4 for p in parts):
        return [p.strip() for p in parts if p.strip()]

    return [task.strip()]


async def orchestrate_parallel(
    task: str, session_id: str = "fw2-parallel", max_workers: int = 4
) -> Dict[str, Any]:
    """FW2.1 entry: task kompleks → subtasks → dispatch paralel → konsolidasi.

    Args:
        task: kompleks task (bisa berisi "1. ... 2. ..." atau "X lalu Y")
        session_id: base session id (agents get isolated sessions)
        max_workers: max parallel division agents

    Returns:
        {division, results: [...], consolidated, worker_count, communication_count}
    """
    from aeryn_core.multi_agent.orchestrator import Supervisor
    from aeryn_core.agent.divisions import get_division_manager

    supervisor = Supervisor()
    dm = get_division_manager()

    subtasks = _split_subtasks(task)[:max_workers]

    # Route each subtask to its division (supervisor pattern)
    routes = []
    for st in subtasks:
        div_id = await supervisor.route(st)
        routes.append((div_id, st))
        supervisor.communication_count += 1

    # Log the routing decisions (AgentMessage dataclass)
    from aeryn_core.multi_agent.orchestrator import AgentMessage
    supervisor.message_log = [
        AgentMessage(sender="supervisor", recipient=div, content=st, message_type="task")
        for div, st in routes
    ]

    # Dispatch PARALEL — isolated contexts via asyncio.gather
    tasks_coro = [
        _run_division_agent(div, st, session_id) for div, st in routes
    ]
    results = await asyncio.gather(*tasks_coro)

    # Konsolidasi hasil
    ok_results = [r for r in results if r.get("status") == "ok"]
    consolidated = "\n\n".join(
        f"### [{r['division']}] {r['subtask']}\n{r['content']}" for r in ok_results
    ) or "(tidak ada hasil sukses)"

    await supervisor.blackboard.write("last_parallel_task", task)
    await supervisor.blackboard.write("last_results", results)

    return {
        "division": routes[0][0] if routes else "reasoning",
        "results": results,
        "consolidated": consolidated,
        "worker_count": len(results),
        "ok_count": len(ok_results),
        "communication_count": supervisor.communication_count,
        "task": task[:200],
    }


async def orchestrate_single(task: str, session_id: str = "fw2-single") -> Dict[str, Any]:
    """Single-task orchestration via Supervisor + AgentLoop (routed, not parallel)."""
    from aeryn_core.multi_agent.orchestrator import Supervisor

    supervisor = Supervisor()
    return await supervisor.orchestrate(
        task,
        agent_runner=lambda div, st: _run_division_agent(div, st, session_id),
    )
