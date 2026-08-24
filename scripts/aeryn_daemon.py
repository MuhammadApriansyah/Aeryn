"""Aeryn-Core Daemon — server persist hybrid (FastAPI + uvicorn).

Satu orchestrator hidup sepanjang umur proses → memori vektor, tensor emosi,
dan checkpoint sesi PERSIST antar request (tidak di-instantiate ulang).

Endpoint:
  GET  /health                  → status daemon
  POST /compile                 → { session_id, base_prompt, user_prompt, history?, tasks?, preference_vector? }
                                  → { compiled_prompt, blackboard, gate_mode, memories }
  POST /digest                  → { session_id, user_prompt, response }
                                  → governance result + telemetry
  GET  /memory/{session_id}     → ringkasan state sesi (tensor terakhir)
  POST /session/{sid}/reset     → hapus checkpoint afektif sesi (fresh start opsional)

Port default 3010. Jalankan: ./venv-proot/bin/python scripts/aeryn_daemon.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "/home/sen/aeryn-core-agent")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from aeryn_core.orchestrator import UnifiedCognitiveOrchestrator

app = FastAPI(title="Aeryn-Core Daemon", version="0.24.0")

# Satu otak untuk seluruh umur proses — inilah inti persist.
print("[aeryn-daemon] booting cognitive core...", flush=True)
BRAIN = UnifiedCognitiveOrchestrator(dimension=384)
LAST_TENSOR: dict[str, dict] = {}
STARTED = time.time()
print("[aeryn-daemon] core ready.", flush=True)


class CompileReq(BaseModel):
    session_id: str = Field(min_length=1)
    base_prompt: str
    user_prompt: str
    history: list[str] = []
    tasks: list[str] = []
    preference_vector: dict | None = None


class DigestReq(BaseModel):
    session_id: str = Field(min_length=1)
    user_prompt: str
    response: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "core": "aeryn-v28",
        "uptime_s": int(time.time() - STARTED),
        "sessions_touched": len(LAST_TENSOR),
        "gate_mode": BRAIN.cached_active_gate_mode,
    }


@app.post("/compile")
def compile_prompt(req: CompileReq):
    try:
        compiled = BRAIN.compile_stateful_system_prompt(
            session_id=req.session_id,
            base_character_prompt=req.base_prompt,
            user_prompt=req.user_prompt,
            mock_history_logs=req.history,
            open_tasks=req.tasks,
            external_preference_vector=req.preference_vector,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"compile failed: {e}")

    try:
        bb = json.loads(BRAIN.cached_shared_blackboard)
    except Exception:
        bb = {}
    LAST_TENSOR[req.session_id] = bb.get("emotional_tensor_snapshot", {})

    # Ekstrak blok memori dari prompt agar client tahu konteks apa yang disuntik
    memories = []
    if "[RELEVANT_MEMORY_CONTEXT]" in compiled:
        block = compiled.split("[RELEVANT_MEMORY_CONTEXT]", 1)[1]
        for line in block.splitlines()[1:]:
            line = line.strip().lstrip("- ").strip()
            if line and not line.startswith("["):
                memories.append(line)

    return {
        "compiled_prompt": compiled,
        "blackboard": bb,
        "gate_mode": BRAIN.cached_active_gate_mode,
        "memories": memories[:4],
    }


@app.post("/digest")
def digest(req: DigestReq):
    try:
        result = BRAIN.digest_external_llm_response(
            session_id=req.session_id,
            user_prompt=req.user_prompt,
            raw_llm_output_text=req.response,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"digest failed: {e}")
    return result


@app.get("/memory/{session_id}")
def memory(session_id: str):
    cp = None
    try:
        cp = BRAIN.rust_brain.load_affective_checkpoint(session_id)
    except Exception:
        pass
    return {
        "session_id": session_id,
        "last_tensor": LAST_TENSOR.get(session_id),
        "persisted_checkpoint": list(cp) if cp else None,
    }


@app.post("/session/{session_id}/reset")
def reset_session(session_id: str):
    LAST_TENSOR.pop(session_id, None)
    return {"reset": True, "session_id": session_id}


# ── V25: Agentic loop (hybrid-native scaffolding) ───────────────────────
import sys
sys.path.insert(0, "/home/sen/aeryn-core-agent")
from aeryn_core.model_client import ModelClient
from aeryn_core.tool_bridge import build_default_registry
from aeryn_core.tool_governance import ToolGovernanceGate
from aeryn_core.shadow_mode import ParityLedger, ShadowRunner
from aeryn_core.planner import make_plan, load_plan
from aeryn_core.terminal_tool import make_terminal, TERMINAL_SCHEMA
from aeryn_core.episodic_memory import EpisodicMemory
from aeryn_core.reflection import PostRunReflection
from aeryn_core.agents.division_4_gov.sub_agents_real import SubAgentContextDriftShield

TOOLS = build_default_registry(sandbox_roots=["~/aeryn-core-agent", "~/webnovel-platform"])
# V27.2 — tool tier power: terminal sandboxed (whitelist + no-shell + cwd lock).
TOOLS.register("terminal", make_terminal(["~/aeryn-core-agent", "~/webnovel-platform"]),
               TERMINAL_SCHEMA, tier="power")
GATE = ToolGovernanceGate(drift_shield=SubAgentContextDriftShield())
LEDGER = ParityLedger(TOOLS)
SHADOW = ShadowRunner(TOOLS, LEDGER)
MEMORY = EpisodicMemory()  # V27.4 — memori episodik lintas-sesi
REFLECT = PostRunReflection(registry=TOOLS, ledger=LEDGER)  # V27.5 — refleksi pasca-run
# V27.0: tool safe-tier yang lulus shadow 5x beruntun otomatis naik native.
SHADOW.auto_promote = {"web_search", "http_get"}  # hanya tier safe; fs/power tetap manual


def _maybe_auto_promote(name):
    """V27.3 meta-loop ringan: graduation_ready dari ledger → promosi native."""
    if name not in getattr(SHADOW, "auto_promote", set()):
        return False
    s = LEDGER.summary().get(name) or {}
    if s.get("graduation_ready") and TOOLS.tools[name]["status"] == "shadowing":
        TOOLS.promote(name, "native")
        return True
    return False


def _checker_fs_read(args, result):
    """Paritas fs_read: hasil harus berupa dict dgn path & content non-error."""
    return isinstance(result, dict) and "content" in result and "error" not in result


def _checker_web_search(args, result):
    return isinstance(result, dict) and "results" in result


SHADOW.register_checker("fs_read", _checker_fs_read)
SHADOW.register_checker("web_search", _checker_web_search)

MODEL = None  # lazy init saat /agent/run pertama


class AgentRunReq(BaseModel):
    goal: str
    session_id: str = "agent_default"
    max_iterations: int = 6
    model: str = None
    provider: str = None
    max_wall_seconds: int = Field(default=240, ge=30, le=900)
    critic: bool = False  # V27.6: critic pass sebelum jawaban final (goal kompleks)


@app.get("/mentor")
def mentor_panel(last_n: int = 10):
    """V29.3 — panel mentor mini: gabungan reflection digest + tool status
    + strategi terbaru, siap dikonsumsi CLI/web.

    Output: {success_rate, active_strategies, recommendations, tool_status,
             last_run}
    """
    digest = REFLECT.digest(last_n=last_n)
    # Strategi aktif: yang masih < 48h & tag GOAL_SAM
    strategies = []
    try:
        path = REFLECT.path
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    if r.get("strategy") and "GOAL_SAM" in r["strategy"]:
                        strategies.append({"goal": r["goal"][:100],
                                           "strategy": r["strategy"],
                                           "ts": r.get("ts")})
    except (OSError, ValueError):
        pass
    return {
        "success_rate": digest.get("success_rate"),
        "runs": digest.get("runs"),
        "active_strategies": strategies[:5],
        "recommendations": digest.get("top_recommendations", [])[:3],
        "findings": digest.get("top_findings", [])[:3],
        "tool_status": {name: {"status": t["status"], "success": t["success"],
                               "fail": t["fail"]}
                        for name, t in TOOLS.tools.items()},
    }


@app.get("/tools")
def list_tools():
    return {name: {"tier": t["tier"], "status": t["status"],
                   "success": t["success"], "fail": t["fail"],
                   "shadow": t.get("shadow")}
            for name, t in TOOLS.tools.items()} | {
        "parity_summary": LEDGER.summary(),
        "governance_audit": GATE.digest_audit(),
    }


@app.get("/agent/plan/{session_id}")
def get_plan(session_id: str):
    """V27.1: inspeksi plan + status per langkah."""
    plan = load_plan(session_id)
    if not plan:
        raise HTTPException(status_code=404, detail="no plan for session")
    return plan


@app.get("/agent/reflections")
def get_reflections(last_n: int = 20):
    """V27.5: digest refleksi N run terakhir — bahan meta-review mentor."""
    return REFLECT.digest(last_n)


@app.post("/tools/{name}/promote")
def promote_tool(name: str, status: str):
    if name not in TOOLS.tools:
        raise HTTPException(status_code=404, detail="unknown tool")
    if status not in ("bridged", "shadowing", "native"):
        raise HTTPException(status_code=400, detail="bad status")
    TOOLS.promote(name, status)
    return {"tool": name, "status": status}


@app.post("/agent/run")
def agent_run(req: AgentRunReq):
    """Loop LLM→tool→observasi dengan konteks kognitif aeryn di system prompt."""
    events = list(_run_steps(req))          # drain generator
    final = events[-1] if events else {}
    return final.get("data", {"error": "no events"})


# V28 — lock per-session: dua run concurrent pada session yang sama
# diserialisasi (bukan diblokir total), race condition registry state hilang.
_SESSION_LOCKS: dict = {}


def _session_lock(sid: str):
    import threading
    return _SESSION_LOCKS.setdefault(sid, threading.Lock())


from fastapi.responses import StreamingResponse


@app.post("/agent/run/stream")
def agent_run_stream(req: AgentRunReq):
    """V28: SSE per-step — event plan/tool/final dipush saat terjadi."""
    def gen():
        for ev in _run_steps(req):
            yield f"event: {ev['event']}\ndata: {json.dumps(ev['data'], ensure_ascii=False)}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


def _build_system_prompt(req: AgentRunReq, MODEL_) -> tuple:
    """System prompt kognitif + plan + episodic recall + nada emosi."""
    try:
        compiled = BRAIN.compile_stateful_system_prompt(
            req.session_id, "Kamu Aeryn, agen otonom yang hangat dan metodis.",
            req.goal, [], [])
        system_prompt = compiled
    except Exception:
        system_prompt = "Kamu Aeryn, agen otonom yang hangat dan metodis."

    plan = make_plan(MODEL_, req.goal, req.session_id)
    plan_block = "\n".join(
        f"{sg.get('step', i)}. {sg.get('desc','')} (tool: {sg.get('tool_hint','none')}; "
        f"sukses bila: {sg.get('done_when','')})"
        for i, sg in enumerate(plan["subgoals"]))
    system_prompt = (system_prompt or "") + (
        f"\n\n## Rencana kerja (ikuti berurutan)\n{plan_block}\n"
        "Kerjakan subgoal satu per satu. ATURAN PENTING: keluarkan HANYA SATU "
        "panggilan tool per pesan — tunggu hasilnya baru lanjut ke langkah berikutnya. "
        "Setelah semua selesai, rangkum hasilnya.")

    past = MEMORY.recall(req.goal)
    system_prompt += MEMORY.prompt_block(past)

    # V29.2 — inject strategi dari refleksi goal serupa
    strat = REFLECT.find_recent_strategy(req.goal)
    if strat:
        system_prompt += (
            "\n\n## Strategi dari refleksi sebelumnya (ikuti bila relevan)\n"
            f"{strat}\n")
    from aeryn_core.emotion_tone import tone_directive
    system_prompt += tone_directive(LAST_TENSOR.get(req.session_id, {}))
    return system_prompt, plan


def _run_steps(req: AgentRunReq):
    """Generator inti agentic loop — yield event dict per langkah.

    Event: plan → tool* → critic? → final/error/timeout/truncated.
    Dipakai /agent/run (drain) maupun /agent/run/stream (SSE).
    """
    global MODEL
    with _session_lock(req.session_id):
        if MODEL is None or req.model or req.provider:
            MODEL = ModelClient(provider=req.provider, model=req.model)

        system_prompt, plan = _build_system_prompt(req, MODEL)
        yield {"event": "plan", "data": {
            "source": plan["source"], "subgoals": plan["subgoals"]}}

        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": req.goal}]
        trace = []
        import time as _time
        deadline = _time.time() + req.max_wall_seconds

        def _finish(answer=None, error=None, timed_out=False, iterations=0,
                    truncated=False):
            """Satu pintu keluar: record episode + refleksi."""
            # V29.2: refleksi dulu (berisi strategy), lalu record episode
            reflection = REFLECT.reflect(req.goal, plan, trace, answer=answer,
                                         error=error, timed_out=timed_out,
                                         truncated=truncated)
            MEMORY.record(req.session_id, req.goal,
                          plan.get("source", "unknown"), trace,
                          answer=answer, error=error, timed_out=timed_out,
                          strategy=reflection.get("strategy"))
            out = {"answer": answer, "trace": trace,
                   "iterations": iterations}
            if error:
                out["error"] = error
            if timed_out:
                out["timed_out"] = True
            if truncated:
                out["truncated"] = True
            if reflection["findings"]:
                out["reflection"] = {
                    "findings": reflection["findings"],
                    "recommendations": reflection["recommendations"]}
            return out

        for i in range(req.max_iterations):
            if _time.time() > deadline:
                out = _finish(error="wall-clock budget habis sebelum goal tuntas",
                              timed_out=True, iterations=i)
                yield {"event": "timeout", "data": out}
                return
            try:
                resp = MODEL.chat(messages, tools=TOOLS.schemas())
            except urllib.error.HTTPError as e:
                trace.append({"step": i, "type": "error", "http": e.code})
                out = _finish(error=f"LLM provider HTTP {e.code} (semua model fallback habis)",
                              iterations=i)
                yield {"event": "error", "data": out}
                return
            except (urllib.error.URLError, RuntimeError, TimeoutError) as e:
                trace.append({"step": i, "type": "error", "detail": str(e)[:200]})
                out = _finish(error=f"LLM unreachable: {e}", iterations=i)
                yield {"event": "error", "data": out}
                return
            msg = resp["choices"][0]["message"]
            calls = msg.get("tool_calls") or []
            if not calls:
                trace.append({"step": i, "type": "final"})
                answer = msg.get("content")
                if req.critic and answer and any(t["type"] == "tool" for t in trace):
                    from aeryn_core.critic_pass import make_critic
                    digests = [t.get("result_digest", "") for t in trace
                               if t["type"] == "tool"]
                    c = make_critic(MODEL)(answer, digests)
                    answer = c["answer"]
                    verdict = (c.get("critic") or {}).get("verdict", "?")
                    trace.append({"step": i, "type": "critic",
                                  "verdict": verdict})
                out = _finish(answer=answer, iterations=i + 1)
                yield {"event": "final", "data": out}
                return
            messages.append(msg)
            # Guard single-call: satu tool-call per giliran.
            for ci, call in enumerate(calls):
                fn = call["function"]["name"]
                args = json.loads(call["function"]["arguments"] or "{}")
                entry = TOOLS.tools.get(fn)
                if ci > 0:
                    result = {"error": "MULTI-CALL DITOLAK: kirim ulang panggilan ini "
                                       "SENDIRIAN pada giliran berikutnya, satu per satu"}
                elif entry is None:
                    result = {"error": f"unknown tool: {fn}"}
                else:
                    gate = GATE.evaluate(fn, entry["tier"], entry["status"],
                                         entry["success"], entry["fail"], args)
                    if not gate["allowed"]:
                        result = {"error": f"governance denied: {gate['reason']}"}
                    else:
                        try:
                            result = SHADOW.run_with_shadow(fn, args)
                            _maybe_auto_promote(fn)
                        except Exception as te:
                            result = {"error": f"tool {fn} failed: {type(te).__name__}: {te}"[:300]}
                trace.append({"step": i, "type": "tool", "name": fn, "args": args,
                              "result_digest": str(result)[:200]})
                messages.append({"role": "tool", "tool_call_id": call["id"],
                                 "content": json.dumps(result, ensure_ascii=False)[:8000]})
                yield {"event": "tool", "data": {
                    "step": i, "name": fn, "args": args,
                    "digest": str(result)[:200]}}

        out = _finish(iterations=req.max_iterations, truncated=True)
        yield {"event": "truncated", "data": out}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3010, log_level="warning")
