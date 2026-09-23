"""Subagent Orchestration — spawn isolated subagents (GAP UTAMA: Aeryn
Autonomous AI Agent sejati).

Subagent = child agent dengan:
- Context window sendiri (isolated — tidak melihat parent history)
- Tool budget sendiri (filtered tool access + max tool calls)
- Termination conditions (stop saat evidence clear / progress stall)
- Timeout per task

Sumber referensi: arXiv 2603.05344 (Subagent Orchestration — Code explorer,
Strategic planner, Web tools, User clarification), Claude Code subagents
(isolated context, one-level spawn).

Real API only — no test doubles: subagent memanggil AerynLLMClient.chat()
nyata dan tool registry nyata.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional

from aeryn_core.utils.llm_client import AerynLLMClient
from aeryn_core.tools import get_tool_registry

# Role presets (per arXiv 2603.05344 — subagent specialization):
# allow_all        = semua tools (worker penuh)
# read_only        = hanya baca (explorer/planner — tanpa mutasi)
# web_and_file     = web fetch + file write (clone web content)
# minimal          = hampir tanpa tool (user clarification / reasoning murni)
ROLE_TOOL_FILTERS: Dict[str, Optional[List[str]]] = {
    "allow_all": None,  # None = tidak difilter
    "read_only": ["fs_read", "file_read", "file_search", "web_search",
                  "web_read", "memory_search", "vault_read",
                  "social_memory_get", "graph_traverse", "task_list",
                  "pitfall_search", "graph_status"],
    "web_and_file": ["web_search", "web_read", "fs_read", "file_write",
                     "file_read", "fs_list"],
    "minimal": [],
}

# Budget default per subagent
DEFAULT_MAX_TOOL_CALLS = 15
DEFAULT_TIMEOUT_S = 120
DEFAULT_MAX_TOKENS = 2000


def _filter_tools(all_tools: List, allowed: Optional[List[str]]) -> List:
    """Filter tool registry → hanya tools dalam allowlist role (jika None = semua)."""
    if allowed is None:
        return all_tools
    return [t for t in all_tools if t.name in allowed]


class SubagentResult:
    """Hasil satu subagent (output + metadata + evidence)."""

    def __init__(self, name: str, role: str, output: str = "",
                 error: str = "", tool_calls: int = 0,
                 duration_s: float = 0.0, timed_out: bool = False,
                 iterations: int = 0):
        self.name = name
        self.role = role
        self.output = output
        self.error = error
        self.tool_calls = tool_calls
        self.duration_s = duration_s
        self.timed_out = timed_out
        self.iterations = iterations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "role": self.role,
            "output": self.output[:2000], "error": self.error[:300],
            "tool_calls": self.tool_calls, "duration_s": round(self.duration_s, 2),
            "timed_out": self.timed_out, "iterations": self.iterations,
        }


class SubagentOrchestrator:
    """Spawn subagents terisolasi — parallel atau sequential.

    Setiap subagent:
    - Punya LLM client sendiri + context sendiri (mulai kosong)
    - Tool access difilter per role (read_only dsb) + tool call budget
    - Loop: LLM → tool call (budget-bound) → observe → LLM → ... → final
    - Termination: final answer / budget habis / timeout / progress stall
    """

    def __init__(self, max_concurrent: int = 4):
        self.max_concurrent = max_concurrent

    async def _run_one(self, name: str, task: str, role: str,
                       backstory: str = "", timeout_s: int = DEFAULT_TIMEOUT_S,
                       max_tool_calls: int = DEFAULT_MAX_TOOL_CALLS,
                       max_tokens: int = DEFAULT_MAX_TOKENS,
                       model: Optional[str] = None,
                       temperature: float = 0.7) -> SubagentResult:
        """Jalankan satu subagent (isolated)."""
        t0 = time.time()
        allowed = ROLE_TOOL_FILTERS.get(role)
        if allowed is None and role != "allow_all":
            return SubagentResult(name=name, role=role,
                                  error=f"role '{role}' tidak dikenal — pilih: allow_all, read_only, web_and_file, minimal")

        llm = AerynLLMClient()  # isolated client (context sendiri)
        registry = get_tool_registry()
        tools = _filter_tools(registry.list_tools(), allowed)
        schemas = [t.to_openai_schema() for t in tools]

        system = (
            f"You are {name}, a specialized subagent of Aeryn (role: {role}).\n"
            + (f"Backstory: {backstory}\n" if backstory else "")
            + "You have your own context window — you see only your own task and your own tool calls.\n"
            + "Available tools:\n"
            + "\n".join(f"- {t.name}: {t.description[:80]}" for t in tools)
            + "\n\nTermination rules (WAJIB):\n"
            + "- Stop when evidence is clear — jangan over-explore\n"
            + "- Stop if progress stalls — re-reading the same source triggers immediate stop\n"
            + "- Prefer depth over breadth\n"
            + "- When you have the final answer, respond directly (no tool call)"
        )

        messages = [{"role": "system", "content": system},
                    {"role": "user", "content": task}]
        tool_call_count = 0
        iterations = 0

        async def _loop() -> SubagentResult:
            nonlocal tool_call_count, iterations, messages
            stall_count = 0
            last_tools_used: List[str] = []
            while iterations < 12:
                iterations += 1
                try:
                    resp = await llm.chat(messages, session_id=f"subagent:{name}",
                                          model=model, temperature=temperature,
                                          max_tokens=max_tokens, tools=schemas or None)
                except Exception as e:
                    # Provider error yang tidak tertangani (fallback chain habis)
                    return SubagentResult(name=name, role=role,
                                          error=f"LLM error: {str(e)[:200]}",
                                          tool_calls=tool_call_count,
                                          duration_s=time.time() - t0,
                                          iterations=iterations)
                content = resp.get("content") or ""
                calls = resp.get("tool_calls") or []
                prov = resp.get("provider", "")

                # Error path tanpa exception: blocked / no provider / all failed
                # (chat() return content+reasoning TANPA field error — cek eksplisit)
                if prov in ("none", "") and not calls:
                    if "blocked" in content.lower() or "no llm providers" in content.lower() \
                            or "all providers failed" in content.lower():
                        return SubagentResult(name=name, role=role,
                                              error=content[:200],
                                              tool_calls=tool_call_count,
                                              duration_s=time.time() - t0,
                                              iterations=iterations)

                if not calls:
                    # Final answer (atau reasoning murni) — stop
                    return SubagentResult(name=name, role=role, output=content,
                                          tool_calls=tool_call_count,
                                          duration_s=time.time() - t0,
                                          iterations=iterations)

                # Eksekusi tool calls (budget-bound)
                messages.append({"role": "assistant", "content": content,
                                 "tool_calls": calls})
                stall = True
                for c in calls:
                    if tool_call_count >= max_tool_calls:
                        break
                    tname = c.get("name", "")
                    targs = c.get("arguments") or {}
                    tool = next((t for t in tools if t.name == tname), None)
                    if tool is None:
                        out = f"error: tool '{tname}' tidak di-allow untuk role {role}"
                    else:
                        try:
                            if tool.is_async:
                                out = await tool.handler(**targs)
                            else:
                                out = tool.handler(**targs)
                            if not isinstance(out, str):
                                import json as _j
                                out = _j.dumps(out, default=str)[:4000]
                            # stall detection: tool sama + argumen sama berulang
                            if f"{tname}:{str(targs)[:60]}" not in last_tools_used:
                                stall = False
                                last_tools_used.append(f"{tname}:{str(targs)[:60]}")
                        except Exception as e:
                            out = f"error saat eksekusi {tname}: {str(e)[:200]}"
                    tool_call_count += 1
                    messages.append({"role": "tool", "tool_call_id": c.get("id", ""),
                                     "name": tname, "content": str(out)})

                if tool_call_count >= max_tool_calls:
                    # Budget habis — minta jawaban final tanpa tool lagi
                    messages.append({"role": "user",
                                     "content": "[BUDGET HABIS] Tool call budget tercapai. "
                                                "Beri jawaban final dari evidence yang sudah ada sekarang."})
                    resp2 = await llm.chat(messages, session_id=f"subagent:{name}",
                                           model=model, temperature=temperature,
                                           max_tokens=max_tokens, tools=None)
                    out2 = resp2.get("content") or ""
                    return SubagentResult(name=name, role=role, output=out2,
                                          error=resp2.get("error", ""),
                                          tool_calls=tool_call_count,
                                          duration_s=time.time() - t0,
                                          iterations=iterations + 1)

                if stall:
                    stall_count += 1
                    if stall_count >= 2:
                        # Progress stall — minta final (anti-loop)
                        messages.append({"role": "user",
                                         "content": "[PROGRESS STALL] Sumber yang sama berulang. "
                                                    "Stop exploring — beri jawaban final sekarang."})
                        resp3 = await llm.chat(messages, session_id=f"subagent:{name}",
                                               model=model, temperature=temperature,
                                               max_tokens=max_tokens, tools=None)
                        return SubagentResult(name=name, role=role,
                                              output=resp3.get("content") or "",
                                              error=resp3.get("error", ""),
                                              tool_calls=tool_call_count,
                                              duration_s=time.time() - t0,
                                              iterations=iterations + 1)
                else:
                    stall_count = 0
            # Iteration cap
            return SubagentResult(name=name, role=role,
                                  error="iteration cap tercapai (12)",
                                  tool_calls=tool_call_count,
                                  duration_s=time.time() - t0,
                                  iterations=iterations)

        try:
            return await asyncio.wait_for(_loop(), timeout=timeout_s)
        except asyncio.TimeoutError:
            return SubagentResult(name=name, role=role, error="timeout",
                                  tool_calls=tool_call_count,
                                  duration_s=time.time() - t0,
                                  timed_out=True, iterations=iterations)

    async def run(self, tasks: List[Dict[str, Any]]) -> List[SubagentResult]:
        """Jalankan banyak subagent — parallel (bounded max_concurrent).

        Task format: {name, task, role, backstory?, timeout_s?, model?}
        """
        if not tasks:
            return []
        sem = asyncio.Semaphore(self.max_concurrent)

        async def _bounded(t: Dict[str, Any]) -> SubagentResult:
            async with sem:
                return await self._run_one(
                    name=t.get("name", "subagent"),
                    task=t.get("task", ""),
                    role=t.get("role", "read_only"),
                    backstory=t.get("backstory", ""),
                    timeout_s=int(t.get("timeout_s", DEFAULT_TIMEOUT_S)),
                    max_tool_calls=int(t.get("max_tool_calls", DEFAULT_MAX_TOOL_CALLS)),
                    max_tokens=int(t.get("max_tokens", DEFAULT_MAX_TOKENS)),
                    model=t.get("model"),
                    temperature=float(t.get("temperature", 0.7)),
                )

        return list(await asyncio.gather(*[_bounded(t) for t in tasks]))


_orchestrator = None


def get_subagent_orchestrator(max_concurrent: int = 4) -> SubagentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SubagentOrchestrator(max_concurrent=max_concurrent)
    return _orchestrator
