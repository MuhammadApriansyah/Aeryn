"""Supervisor Loop — pola supervisor formal (SUBAGENT-2).

Supervisor = 1 agent koordinator:
1. Terima goal → decompose jadi sub-tasks
2. Assign ke specialized workers (divisions Aeryn sebagai role mapping)
3. Fan-out parallel (SubagentOrchestrator)
4. Fan-in: kumpulkan hasil → sintesis jawaban final (supervisor LLM call)

Sumber: arXiv 2603.05344, LangGraph supervisor pattern, Tyk enterprise guide.

Real API only — no test doubles: decompose + workers + sintesis = LLM nyata.
"""

import asyncio
from typing import List, Dict, Any, Optional

from aeryn_core.agent.subagent import get_subagent_orchestrator, SubagentResult
from aeryn_core.utils.llm_client import AerynLLMClient

# Divisions Aeryn → subagent role mapping (5 divisions = worker spesialis)
DIVISION_WORKER_ROLES: Dict[str, str] = {
    "division_1_creative": "allow_all",     # kreatif — tools penuh
    "division_2_psych": "minimal",          # psikologis — reasoning murni
    "division_3_reasoning": "read_only",    # reasoning — baca + analisa
    "division_4_gov": "read_only",          # governance — baca + validasi
    "division_5_infra": "allow_all",        # infra — eksekusi penuh
}


class SupervisorResult:
    """Hasil supervisor loop (decompose + workers + sintesis)."""

    def __init__(self, goal: str, subtasks: List[Dict[str, Any]],
                 workers: List[Dict[str, Any]], synthesis: str = "",
                 error: str = "", duration_s: float = 0.0):
        self.goal = goal
        self.subtasks = subtasks
        self.workers = workers
        self.synthesis = synthesis
        self.error = error
        self.duration_s = duration_s

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "subtasks": self.subtasks,
            "workers": self.workers,
            "synthesis": self.synthesis[:3000],
            "error": self.error[:300],
            "duration_s": round(self.duration_s, 2),
        }


class SupervisorLoop:
    """Supervisor formal: decompose → fan-out → fan-in → sintesis."""

    def __init__(self, max_concurrent: int = 4):
        self.orchestrator = get_subagent_orchestrator(max_concurrent=max_concurrent)
        self.llm = AerynLLMClient()

    async def _decompose(self, goal: str) -> List[Dict[str, Any]]:
        """Decompose goal → sub-tasks (LLM nyata, JSON parse)."""
        prompt = (
            f"Decompose goal berikut menjadi 2-4 sub-tasks yang bisa dikerjakan "
            f"paralel oleh specialized workers.\n\n"
            f"Goal: {goal}\n\n"
            f"Balas HANYA JSON array (tanpa penjelasan):\n"
            f'[{{"name": "worker-1", "task": "...", "role": "read_only"}}, ...]\n\n'
            f"Role yang tersedia: allow_all (eksekusi penuh), read_only (analisa), "
            f"minimal (reasoning murni). Pilih yang paling tepat per sub-task."
        )
        resp = await self.llm.chat(
            [{"role": "user", "content": prompt}],
            session_id="supervisor:decompose",
            temperature=0.3, max_tokens=800)
        content = resp.get("content") or ""
        # Parse JSON (toleran terhadap ```json fence)
        import json as _json
        import re as _re
        m = _re.search(r"\[.*\]", content, _re.DOTALL)
        if not m:
            # Fallback: satu sub-task = goal langsung (reasoning worker)
            return [{"name": "worker-reason", "task": goal, "role": "minimal"}]
        try:
            tasks = _json.loads(m.group(0))
            if not isinstance(tasks, list) or not tasks:
                return [{"name": "worker-reason", "task": goal, "role": "minimal"}]
            out = []
            for t in tasks:
                if isinstance(t, dict) and t.get("task"):
                    out.append({
                        "name": str(t.get("name", "worker"))[:40],
                        "task": str(t["task"])[:800],
                        "role": str(t.get("role", "read_only")),
                    })
            return out or [{"name": "worker-reason", "task": goal, "role": "minimal"}]
        except Exception:
            return [{"name": "worker-reason", "task": goal, "role": "minimal"}]

    async def _synthesize(self, goal: str,
                          results: List[SubagentResult]) -> str:
        """Fan-in: gabungkan hasil worker → sintesis final (LLM nyata)."""
        parts = []
        for r in results:
            if r.error:
                parts.append(f"[{r.name}] GAGAL: {r.error[:150]}")
            else:
                parts.append(f"[{r.name}] {r.output[:1200]}")
        prompt = (
            f"Goal: {goal}\n\n"
            f"Hasil specialized workers:\n\n" + "\n\n".join(parts) +
            f"\n\nSintesis hasil di atas menjadi jawaban final yang koheren, "
            f"lengkap, dan langsung bisa dipakai. Bahasa Indonesia, concise."
        )
        resp = await self.llm.chat(
            [{"role": "user", "content": prompt}],
            session_id="supervisor:synthesize",
            temperature=0.5, max_tokens=1500)
        return resp.get("content") or ""

    async def run(self, goal: str) -> SupervisorResult:
        """Supervisor loop penuh: goal → decompose → fan-out → fan-in → sintesis."""
        import time
        t0 = time.time()

        # 1) Decompose
        try:
            subtasks = await self._decompose(goal)
        except Exception as e:
            return SupervisorResult(goal=goal, subtasks=[], workers=[],
                                    error=f"decompose gagal: {str(e)[:200]}",
                                    duration_s=time.time() - t0)

        # 2) Fan-out (parallel, budget-bound per subagent)
        try:
            results = await self.orchestrator.run(subtasks)
        except Exception as e:
            return SupervisorResult(goal=goal, subtasks=subtasks, workers=[],
                                    error=f"fan-out gagal: {str(e)[:200]}",
                                    duration_s=time.time() - t0)

        # 3) Fan-in: sintesis
        try:
            synthesis = await self._synthesize(goal, results)
        except Exception as e:
            synthesis = ""
            synth_err = f"sintesis gagal: {str(e)[:200]}"
        else:
            synth_err = ""

        workers = [r.to_dict() for r in results]
        err = synth_err or ("semua worker gagal"
                            if results and all(r.error for r in results) else "")
        return SupervisorResult(goal=goal, subtasks=subtasks, workers=workers,
                                synthesis=synthesis, error=err,
                                duration_s=time.time() - t0)


_supervisor = None


def get_supervisor_loop(max_concurrent: int = 4) -> SupervisorLoop:
    global _supervisor
    if _supervisor is None:
        _supervisor = SupervisorLoop(max_concurrent=max_concurrent)
    return _supervisor
