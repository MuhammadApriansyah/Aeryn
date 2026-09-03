"""Multi-Agent Orchestration — supervisor, handoff, blackboard, parallel.

Berdasarkan riset (LangGraph, MAESTRO, Samira Ghodratnama):
- Topologi: supervisor (centralized), hierarchical, peer-to-peer, shared memory
- 5 divisi kognitif bisa kolaborasi, bukan jalan terpisah
- Handoff: satu divisi serahkan task ke divisi lain
- Blackboard: shared memory untuk state kolaborasi
- Parallel: jalankan banyak divisi sekaligus

Metrik multi-agent (dari riset):
- Coordination efficiency: success per komunikasi
- Communication overhead: jumlah message/token yang dipertukarkan
- Plan quality: kualitas rencana lintas agen
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from aeryn_core.utils.config import DATABASE_DIR


@dataclass
class AgentMessage:
    """A message exchanged between agents."""
    sender: str
    recipient: str
    content: str
    message_type: str = "task"  # task | handoff | result | broadcast
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "message_type": self.message_type,
            "timestamp": self.timestamp,
        }


@dataclass
class Handoff:
    """A task handoff from one agent to another."""
    from_agent: str
    to_agent: str
    task: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "task": self.task,
            "context": self.context,
            "timestamp": self.timestamp,
        }


class Blackboard:
    """Shared memory for agent collaboration (blackboard pattern)."""

    def __init__(self):
        self._entries: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def write(self, key: str, value: Any):
        async with self._lock:
            self._entries[key] = value

    async def read(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._entries.get(key, default)

    async def read_all(self) -> Dict[str, Any]:
        async with self._lock:
            return dict(self._entries)

    async def clear(self):
        async with self._lock:
            self._entries.clear()


class Supervisor:
    """Centralized orchestrator routing tasks to divisions.

    Pola supervisor (centralized): supervisor menerima task, klasifikasi
    ke divisi yang tepat, dan mengkoordinasi eksekusi/handoff.
    """

    def __init__(self):
        from aeryn_core.agent.divisions import get_division_manager
        self.divisions = get_division_manager()
        self.blackboard = Blackboard()
        self.message_log: List[AgentMessage] = []
        self.handoff_log: List[Handoff] = []
        self.communication_count = 0  # for coordination efficiency metric

    async def route(self, task: str) -> str:
        """Route a task to the best division."""
        division_id = self.divisions.classify(task)
        return division_id

    async def orchestrate(self, task: str, agent_runner: Callable = None) -> Dict[str, Any]:
        """Orchestrate a single task through the best division."""
        division_id = await self.route(task)

        # Write task to blackboard
        await self.blackboard.write("current_task", task)
        await self.blackboard.write("current_division", division_id)

        # Log the routing decision
        self.message_log.append(AgentMessage(
            sender="supervisor",
            recipient=division_id,
            content=task,
            message_type="task",
        ))
        self.communication_count += 1

        if agent_runner:
            result = await agent_runner(division_id, task)
        else:
            result = {"division": division_id, "task": task, "status": "routed"}

        await self.blackboard.write("last_result", result)
        return {
            "division": division_id,
            "result": result,
            "communication_count": self.communication_count,
        }

    async def handoff(self, from_div: str, to_div: str, task: str, context: Dict = None) -> Handoff:
        """Hand off a task from one division to another."""
        handoff = Handoff(
            from_agent=from_div,
            to_agent=to_div,
            task=task,
            context=context or {},
        )
        self.handoff_log.append(handoff)
        self.message_log.append(AgentMessage(
            sender=from_div,
            recipient=to_div,
            content=task,
            message_type="handoff",
        ))
        self.communication_count += 1

        await self.blackboard.write(f"handoff:{from_div}->{to_div}", task)
        return handoff

    async def broadcast(self, sender: str, message: str) -> List[str]:
        """Broadcast a message to all divisions."""
        recipients = list(self.divisions.divisions.keys())
        for r in recipients:
            self.message_log.append(AgentMessage(
                sender=sender,
                recipient=r,
                content=message,
                message_type="broadcast",
            ))
        self.communication_count += len(recipients)
        return recipients

    def coordination_efficiency(self, success: bool) -> float:
        """Coordination efficiency: success per communication."""
        if self.communication_count == 0:
            return 0.0
        return (1.0 if success else 0.0) / self.communication_count

    def get_metrics(self) -> Dict[str, Any]:
        """Get multi-agent collaboration metrics."""
        return {
            "communication_count": self.communication_count,
            "message_count": len(self.message_log),
            "handoff_count": len(self.handoff_log),
            "coordination_efficiency": self.coordination_efficiency(True),
        }


class ParallelOrchestrator:
    """Run multiple divisions concurrently on related sub-tasks."""

    def __init__(self, supervisor: Supervisor):
        self.supervisor = supervisor

    async def run_parallel(self, tasks: Dict[str, str], agent_runner: Callable = None) -> Dict[str, Any]:
        """
        Run multiple tasks across divisions in parallel.
        tasks: {division_id: task_text}
        Returns: {division_id: result}
        """
        results = {}

        async def _run_one(div_id: str, task_text: str):
            if agent_runner:
                return div_id, await agent_runner(div_id, task_text)
            return div_id, {"status": "routed", "task": task_text}

        # Run all divisions in parallel
        coros = [_run_one(div_id, task) for div_id, task in tasks.items()]
        for coro in asyncio.as_completed(coros):
            div_id, result = await coro
            results[div_id] = result

        # Record parallel execution as broadcast-like communication
        for div_id in tasks:
            self.supervisor.message_log.append(AgentMessage(
                sender="supervisor",
                recipient=div_id,
                content=tasks[div_id],
                message_type="task",
            ))
        self.supervisor.communication_count += len(tasks)

        return results


# Global instances
_supervisor = None

def get_supervisor() -> Supervisor:
    global _supervisor
    if _supervisor is None:
        _supervisor = Supervisor()
    return _supervisor