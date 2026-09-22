#!/usr/bin/env python3
"""V61.0 — Agent Daemon: autonomy loop for Aeryn.

Runs as a background task inside the FastAPI lifespan. Polls task queue,
executes via tool_runtime + LLM, stores results. Adaptive to environment
(proot=single worker, vps=multi-worker, k8s=scaled by replicas).

No test doubles — uses real BackgroundTaskQueue, tool_runtime, llm_client.
"""
import os
import asyncio
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class AgentDaemon:
    """Autonomous agent loop: pick task → reason → execute tool → store result."""

    def __init__(self, poll_interval: float = 3.0):
        self.poll_interval = poll_interval
        self._running = False
        self._task = None
        self.env = os.environ.get("AERYN_ENV", "proot")
        self.max_workers = self._detect_workers()

    def _detect_workers(self) -> int:
        if self.env == "k8s":
            return 1  # scaled by replicas
        elif self.env == "vps":
            return 4
        return 2  # proot: conservative

    async def start(self):
        self._running = True
        logger.info(f"AgentDaemon starting (env={self.env}, workers={self.max_workers})")
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AgentDaemon stopped")

    async def _loop(self):
        """Main autonomy loop."""
        while self._running:
            try:
                await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Daemon tick error: {e}")
            await asyncio.sleep(self.poll_interval)

    async def _tick(self):
        """One iteration: pick a pending task and execute."""
        from aeryn_core.platform.background_queue import get_task_queue
        from aeryn_core.platform.tool_runtime import get_tool_runtime
        from aeryn_core.platform.auto_task import get_auto_task

        queue = get_task_queue()
        pending = queue.get_pending_count()
        if pending == 0:
            await self._autonomy_tick()   # V61.2 #8: otonomi walau idle
            return

        # Pick first pending task
        tasks = queue.get_all_tasks()
        task_info = next((t for t in tasks if t.get("status") == "pending"), None)
        if not task_info:
            return

        task_id = task_info["id"]
        queue._update_status(task_id, "running")

        try:
            # Parse task into actionable steps
            auto_task = get_auto_task()
            runtime = get_tool_runtime()

            goal = task_info.get("name", "")
            # Execute: call LLM to reason about goal, then run tool if needed
            result = await self._execute_goal(goal, runtime)

            queue._update_status(task_id, "completed", result=str(result)[:5000])
            logger.info(f"Task {task_id} completed")
        except Exception as e:
            queue._update_status(task_id, "failed", result=str(e)[:1000])
            logger.error(f"Task {task_id} failed: {e}")

    async def _execute_goal(self, goal: str, runtime) -> str:
        """Use LLM to reason, then execute tool if the goal maps to one."""
        # Map common goals to tools
        if "search" in goal.lower():
            res = await runtime.execute("web_search", {"query": goal})
            return res.output if res.ok else res.error
        elif "list" in goal.lower() or "file" in goal.lower():
            res = await runtime.execute("fs_list", {"path": "."})
            return res.output if res.ok else res.error
        elif "run" in goal.lower() or "exec" in goal.lower() or "command" in goal.lower():
            res = await runtime.execute("terminal", {"command": goal})
            return res.output if res.ok else res.error
        else:
            # Default: use LLM to respond (chat-style)
            # ModeRouter tidak punya .chat — pakai router.llm (AerynLLMClient, async)
            from aeryn_core.utils.llm_client import get_mode_router
            router = get_mode_router()
            resp = await router.llm.chat(
                [{"role": "user", "content": goal}], session_id="daemon"
            )
            return resp.get("content", "No response")


    async def _autonomy_tick(self):
        """Autonomi SELF-INITIATED (V61.2 #8) — bekerja berguna walau queue kosong.

        Rate-limited; non-LLM (murah): maintenance memori + heartbeat bitemporal
        + alert proaktif berbasis aturan (error-rate).
        """
        import json
        from aeryn_core.memory.fact_store import get_fact_store
        self._autonomy_count = getattr(self, "_autonomy_count", 0) + 1
        if self._autonomy_count % 60 != 0:
            return
        done = []
        # 0) GOAL PURSUIT (F4.2): kejar goal aktif prio tertinggi
        try:
            from aeryn_core.agent.goal_pursuit import pursue_next_goal
            pursued = pursue_next_goal()
            if pursued:
                done.append(f"goal:{pursed[title][:30]}@{pursed[progress]}%")
        except Exception as e:
            logger.warning("autonomy goal-pursuit: %s", e)
        try:
            from aeryn_core.memory.memory_consolidation import MemoryConsolidator
            c = MemoryConsolidator()
            if c.should_consolidate():
                c.consolidate(force=False)
                done.append("consolidate")
        except Exception as e:
            logger.warning("autonomy consolidate: %s", e)
        try:
            get_fact_store().record(
                entity="aeryn", predicate="autonomy_heartbeat",
                fact=json.dumps({"cycle": self._autonomy_count,
                                 "done": done}), source="daemon")
            done.append("heartbeat")
        except Exception as e:
            logger.warning("autonomy heartbeat: %s", e)
        # 3) Proactivity aturan: error-rate tinggi → alert
        try:
            import urllib.request
            with urllib.request.urlopen(
                    "http://127.0.0.1:3010/v1/logging/stats?window_hours=1",
                    timeout=3) as r:
                st = json.loads(r.read())
            if st.get("error_rate", 0) > 20:
                get_fact_store().record(
                    entity="aeryn", predicate="proactive_alert",
                    fact=json.dumps({"error_rate_pct": st.get("error_rate"),
                                     "watch": "elevated 5xx"}),
                    source="daemon")
                done.append("alert")
        except Exception as e:
            logger.info("autonomy alert skip: %s", e)
        if done:
            logger.info("Autonomy tick %d → %s", self._autonomy_count, done)


# Singleton
_daemon = None

def get_agent_daemon() -> AgentDaemon:
    global _daemon
    if _daemon is None:
        _daemon = AgentDaemon()
    return _daemon
