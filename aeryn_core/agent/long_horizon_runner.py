"""Long-Horizon Planning (RM7) — multi-hari: goal besar → task terbagi →
checkpoint → resume lintas sesi/hari.

Wiring: LongHorizonPlanner (reasoning/long_horizon.py — SQLite persist,
create_task/decompose_task/checkpoint/resume) + make_plan (skill-first +
heuristic + LLM) + SubagentOrchestrator (eksekusi subtask).

Alur (Aeryn_Identity.md §15 — Long-Horizon Planning):
    Goal besar → make_plan → create_task + decompose_task (subtasks)
    → eksekusi bertahap (per sesi/hari — checkpoint per langkah)
    → resume_task dari checkpoint terakhir → selesai.

Real API only — no test doubles: LLM nyata, SQLite persist nyata.
"""

from typing import Dict, Any, List, Optional

from aeryn_core.reasoning.long_horizon import LongHorizonPlanner


class LongHorizonRunner:
    """Goal besar multi-hari: plan → task → decompose → execute bertahap."""

    def __init__(self):
        self.planner = LongHorizonPlanner()

    def plan_goal(self, goal: str) -> Dict[str, Any]:
        """Goal → plan (make_plan: skill-first + heuristic + LLM fallback)."""
        from aeryn_core.reasoning.planner import make_plan
        try:
            from aeryn_core.utils.model_client import get_model_client
            mc = get_model_client()
        except Exception:
            mc = None
        plan = make_plan(mc, goal, session_id="long-horizon")
        return plan

    def create_long_task(self, goal: str, deadline: str = None) -> Dict[str, Any]:
        """Goal → long-horizon task + decompose (subtasks dari plan).

        Task tersimpan di SQLite (lintas sesi/hari) — resume dari checkpoint.
        """
        # 1) Plan (steps)
        plan = self.plan_goal(goal)
        steps = plan.get("steps") if isinstance(plan, dict) else None
        if not steps:
            steps = [{"task": goal, "role": "minimal"}]

        # 2) create_task (SQLite persist)
        task_id = self.planner.create_task(
            title=goal[:100],
            description=f"long-horizon: {len(steps)} langkah, dibuat dari goal")
        # 3) decompose_task (subtasks — key title/description sesuai schema)
        subtasks_in = [{"title": f"langkah-{i}",
                        "description": str(s.get("task", s.get("description", "")))[:500]}
                       for i, s in enumerate(steps, 1)]
        sub_ids = self.planner.decompose_task(task_id, subtasks_in)
        return {"ok": True, "task_id": task_id, "subtask_ids": sub_ids,
                "steps": len(steps), "plan": plan.get("title", goal[:60])}

    def execute_next_steps(self, task_id: str, max_steps: int = 2) -> Dict[str, Any]:
        """Eksekusi N langkah berikutnya (per sesi/hari) — checkpoint per langkah.

        Resume dari subtask pertama yang belum selesai (progress-based).
        """
        from aeryn_core.agent.subagent import get_subagent_orchestrator
        import asyncio

        task = self.planner.get_task(task_id)
        if not task:
            return {"ok": False, "error": f"task {task_id} tidak ada"}
        subtasks = self.planner.get_subtasks(task_id)
        if not subtasks:
            return {"ok": False, "error": "subtask kosong — decompose belum jalan"}
        pending = [s for s in subtasks if s.get("status") != "done"]
        if not pending:
            self.planner.update_progress(task_id, 100.0, "completed")
            return {"ok": True, "note": "semua subtask selesai", "executed": 0}

        orch = get_subagent_orchestrator(max_concurrent=1)
        executed, results = 0, []
        for s in pending[:max_steps]:
            sid = s.get("id")
            task_text = s.get("task") or s.get("description") or s.get("name", "")
            # checkpoint SEBELUM eksekusi (state)
            self.planner.create_checkpoint(task_id, f"before:{sid}",
                                           {"subtask": task_text[:200]})
            # asyncio.run (event loop eksplisit — MainThread tanpa loop)
            r = asyncio.run(
                orch.run([{"name": s.get("name", "step"), "task": task_text,
                           "role": "read_only"}]))[0]
            ok = not r.error and bool(r.output)
            # update progress subtask + checkpoint SESUDAH
            if ok:
                self.planner.update_progress(sid, 100.0, "done")
                self.planner.create_checkpoint(task_id, f"after:{sid}",
                                               {"output": r.output[:300]})
            else:
                self.planner.update_progress(sid, 0.0, "failed")
            executed += 1
            results.append({"subtask": task_text[:80], "ok": ok,
                            "output": r.output[:200], "error": r.error[:120]})

        # update progress parent (proporsi subtask done)
        subtasks_all = self.planner.get_subtasks(task_id)
        done = sum(1 for s in subtasks_all if s.get("status") == "done")
        progress = 100.0 * done / max(len(subtasks_all), 1)
        status = "completed" if progress >= 100 else "active"
        self.planner.update_progress(task_id, progress, status)

        return {"ok": True, "task_id": task_id, "executed": executed,
                "progress": round(progress, 1), "status": status,
                "results": results}

    def status(self, task_id: str) -> Dict[str, Any]:
        """Status task + subtasks + checkpoint terakhir (continuity)."""
        task = self.planner.get_task(task_id)
        if not task:
            return {"ok": False, "error": f"task {task_id} tidak ada"}
        subtasks = self.planner.get_subtasks(task_id)
        cp = self.planner.get_latest_checkpoint(task_id)
        done = sum(1 for s in subtasks if s.get("status") == "done")
        return {"ok": True, "task": task, "subtasks": len(subtasks),
                "done": done, "progress_pct": round(100.0 * done / max(len(subtasks), 1), 1),
                "latest_checkpoint": cp}


_runner = None


def get_long_horizon_runner() -> LongHorizonRunner:
    global _runner
    if _runner is None:
        _runner = LongHorizonRunner()
    return _runner
