"""Goal-Derived Workflow (FIX-SEBAGIAN-1) — workflow yang DITURUNKAN dari goal.

Sesuai Aeryn_Identity.md Section 5:
    User → Provide Goal → Aeryn Understands Goal → Aeryn Designs/Selects
    Workflow → Executes → Evaluates → Adapts

Bedanya dengan SupervisorLoop (sekali-jalan):
- Workflow punya SKEMA langkah (steps) yang dieksekusi SEQUENTIAL dengan
  output tiap langkah jadi INPUT langkah berikut (dataflow).
- Tiap langkah dievaluasi (berhasil/gagal) → adapt: langkah gagal → retry
  dengan pendekatan berbeda (Reflexion-style) SEBELUM lanjut.
- Stateful: state tersimpan per langkah (steps[] + outputs).

Real API only — no test doubles: LLM nyata untuk desain + eksekusi tiap
langkah.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional

from aeryn_core.utils.llm_client import AerynLLMClient
from aeryn_core.agent.subagent import get_subagent_orchestrator


class WorkflowStep:
    """Satu langkah workflow (sequential, dataflow ke langkah berikut)."""

    def __init__(self, idx: int, task: str, role: str = "read_only",
                 status: str = "pending", output: str = "",
                 error: str = "", retries: int = 0, duration_s: float = 0.0):
        self.idx = idx
        self.task = task
        self.role = role
        self.status = status  # pending | running | done | failed
        self.output = output
        self.error = error
        self.retries = retries
        self.duration_s = duration_s

    def to_dict(self) -> Dict[str, Any]:
        return {"step": self.idx, "task": self.task[:300], "role": self.role,
                "status": self.status, "output": self.output[:1500],
                "error": self.error[:200], "retries": self.retries,
                "duration_s": round(self.duration_s, 2)}


class GoalWorkflow:
    """Workflow dinamis dari goal: desain → eksekusi sequential → evaluasi → adapt."""

    def __init__(self, max_retries_per_step: int = 2):
        self.llm = AerynLLMClient()
        self.orchestrator = get_subagent_orchestrator(max_concurrent=1)
        self.max_retries_per_step = max_retries_per_step

    async def _design(self, goal: str) -> List[Dict[str, Any]]:
        """Aeryn DESAIN workflow dari goal (LLM nyata → steps JSON)."""
        prompt = (
            f"Desain workflow SEQUENTIAL untuk goal berikut.\n\n"
            f"Goal: {goal}\n\n"
            f"Aturan:\n"
            f"- 2-5 langkah, tiap langkah membawa goal lebih dekat ke selesai\n"
            f"- Output langkah sebelumnya jadi konteks langkah berikutnya\n"
            f"- Langkah terakhir = menyusun jawaban/simpulan final\n\n"
            f"Balas HANYA JSON array (tanpa penjelasan):\n"
            f'[{{"task": "...", "role": "read_only"}}, ...]\n'
            f"Role: allow_all (eksekusi penuh), read_only (analisa), minimal (reasoning murni)."
        )
        resp = await self.llm.chat([{"role": "user", "content": prompt}],
                                   session_id="workflow:design",
                                   temperature=0.3, max_tokens=800)
        content = resp.get("content") or ""
        import json as _json
        import re as _re
        m = _re.search(r"\[.*\]", content, _re.DOTALL)
        if not m:
            # Fallback aman: satu langkah = goal langsung
            return [{"task": goal, "role": "minimal"}]
        try:
            steps = _json.loads(m.group(0))
            if not isinstance(steps, list) or not steps:
                return [{"task": goal, "role": "minimal"}]
            out = []
            for s in steps:
                if isinstance(s, dict) and s.get("task"):
                    out.append({"task": str(s["task"])[:800],
                                "role": str(s.get("role", "read_only"))})
            return out or [{"task": goal, "role": "minimal"}]
        except Exception:
            return [{"task": goal, "role": "minimal"}]

    async def _execute_step(self, step: WorkflowStep,
                            prior_outputs: List[str]) -> None:
        """Eksekusi satu langkah — output langkah sebelumnya jadi konteks."""
        t0 = time.time()
        step.status = "running"
        ctx = "\n\n".join(prior_outputs[-3:]) if prior_outputs else "(langkah pertama)"
        task = (f"Konteks dari langkah sebelumnya:\n{ctx}\n\n"
                f"Langkahmu sekarang: {step.task}\n\n"
                f"Kerjakan langkah ini — output-mu jadi konteks langkah berikutnya.")
        results = await self.orchestrator.run(
            [{"name": f"step-{step.idx}", "task": task, "role": step.role}])
        r = results[0] if results else None
        if r and not r.error and r.output:
            step.status = "done"
            step.output = r.output
        elif r and r.error:
            step.status = "failed"
            step.error = r.error
        else:
            step.status = "failed"
            step.error = "subagent tidak mengembalikan hasil"
        step.duration_s = time.time() - t0

    async def _adapt_step(self, step: WorkflowStep,
                          prior_outputs: List[str]) -> bool:
        """ADAPT: langkah gagal → refleksi pendekatan baru → retry. True = berhasil."""
        while step.retries < self.max_retries_per_step:
            step.retries += 1
            t0 = time.time()
            ctx = "\n\n".join(prior_outputs[-2:]) if prior_outputs else "(langkah pertama)"
            prompt = (
                f"REFLEXION-ADAPT: Langkah workflow GAGAL.\n"
                f"Langkah: {step.task}\n"
                f"Error: {step.error[:200]}\n"
                f"Konteks: {ctx[:600]}\n\n"
                f"Ubah PENDEKATAN (bukan ulang sama persis) dan kerjakan ulang "
                f"langkah ini. Output-mu jadi konteks langkah berikutnya."
            )
            results = await self.orchestrator.run(
                [{"name": f"step-{step.idx}-retry{step.retries}",
                  "task": prompt, "role": step.role}])
            r = results[0] if results else None
            if r and not r.error and r.output:
                step.status = "done"
                step.output = r.output
                step.duration_s = time.time() - t0
                return True
            if r and r.error:
                step.error = r.error
            step.duration_s += time.time() - t0
        return False  # retries habis — langkah tetap gagal

    async def run(self, goal: str) -> Dict[str, Any]:
        """Goal → desain workflow → eksekusi sequential → evaluasi/adapt → selesai."""
        t0 = time.time()

        # 1) DESAIN (dynamic dari goal)
        try:
            plan = await self._design(goal)
        except Exception as e:
            return {"goal": goal, "error": f"desain gagal: {str(e)[:200]}",
                    "steps": [], "completed": 0, "failed": 0,
                    "duration_s": round(time.time() - t0, 2)}

        steps = [WorkflowStep(i, s["task"], s.get("role", "read_only"))
                 for i, s in enumerate(plan, 1)]

        # 2) EKSEKUSI SEQUENTIAL + 3) EVALUASI + 4) ADAPT per langkah
        prior_outputs: List[str] = []
        for step in steps:
            await self._execute_step(step, prior_outputs)
            if step.status == "failed":
                ok = await self._adapt_step(step, prior_outputs)
                if not ok:
                    # Langkah gagal permanen — lanjut dengan konteks yang ada
                    prior_outputs.append(f"[langkah {step.idx} GAGAL: {step.error[:100]}]")
                    continue
            prior_outputs.append(step.output)

        done = sum(1 for s in steps if s.status == "done")
        failed = sum(1 for s in steps if s.status == "failed")

        # 5) SELESAKHI: gabungkan outputs jadi hasil akhir (jika ada langkah sukses)
        final = ""
        good_outputs = [s.output for s in steps if s.status == "done" and s.output]
        if good_outputs:
            try:
                resp = await self.llm.chat(
                    [{"role": "user", "content":
                        f"Goal: {goal}\n\nHasil tiap langkah workflow:\n\n"
                        + "\n\n".join(o[:1200] for o in good_outputs[-3:])
                        + "\n\nSusun hasil akhir yang koheren dan lengkap. Concise."}],
                    session_id="workflow:final", temperature=0.5, max_tokens=1200)
                final = resp.get("content") or ""
            except Exception:
                final = good_outputs[-1][:1500]  # fallback: output langkah terakhir

        return {"goal": goal,
                "steps": [s.to_dict() for s in steps],
                "completed": done, "failed": failed,
                "final": final[:3000],
                "duration_s": round(time.time() - t0, 2)}


_workflow = None


def get_goal_workflow(max_retries_per_step: int = 2) -> GoalWorkflow:
    global _workflow
    if _workflow is None:
        _workflow = GoalWorkflow(max_retries_per_step=max_retries_per_step)
    return _workflow
