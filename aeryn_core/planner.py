"""V27.1 — Planner: dekomposisi goal → subgoal terurut (plan-then-execute).

Filosofi scaffolding: planner LLM membuat rencana SEBELUM loop agentic jalan,
loop lalu eksekusi subgoal satu per satu dengan evaluasi per langkah. Plan
disimpan per-session dan bisa diinspeksi via GET /agent/plan/{session_id}.
"""
import json
import os
import urllib.request

PLAN_DIR = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/plans")
MAX_SUBGOALS = 6

PLANNER_PROMPT = """Kamu adalah modul perencana Aeryn. Uraikan goal pengguna menjadi \
subgoal berurutan yang KONKRET dan dapat dieksekusi dengan tool yang tersedia. \
Balas HANYA JSON valid, tanpa penjelasan lain:
{{"subgoals": [{{"step": 0, "desc": "...", "tool_hint": "web_search|http_get|fs_read|none", "done_when": "kriteria sukses singkat"}}]}}
Maksimal {max_subgoals} subgoal. Jika goal sederhana, cukup 1-2 subgoal."""


def _looks_structured(goal: str) -> bool:
    """Goal sudah terdekomposisi user (bernomor/berpoin/ber-step)?"""
    import re as _re
    return bool(_re.search(r"(\(\d\)|^\s*\d+[.)]|\blangkah\b|\bstep\b|\blalu\b|;)",
                           goal, _re.I | _re.M))


def _heuristic_plan(goal: str) -> list:
    """Plan tanpa LLM: deteksi intent per segmen goal (instan & deterministik).

    Meniru pola skill-command Hermes: instruksi berstruktur tidak butuh
    reasoning model — pattern matching cukup.
    """
    import re as _re
    parts = _re.split(r";\s*|\(\d+\)\s*|(?<=[.!?])\s+", goal)
    subgoals = []
    for s in (x.strip(" .;") for x in parts):
        if len(s) < 8 or _re.match(r"^(kerjakan|lakukan|ikuti|jawab|dengan)\b", s, _re.I):
            continue
        low = s.lower()
        if "fs_read" in low or any(k in low for k in
                ("cargo.toml", "readme", "file", ".py", ".json")):
            hint = "fs_read"
        elif "http_get" in low or low.startswith(("http", "fetch", "ambil judul",
                                                  "buka url", "akses")):
            hint = "http_get"
        elif ("web_search" in low or low.startswith(("cari", "search"))
              or " cari " in low):
            hint = "web_search"
        else:
            hint = "none"
        subgoals.append({"step": len(subgoals), "desc": s[:160],
                         "tool_hint": hint, "done_when": "langkah selesai"})
    return subgoals


def make_plan(model_client, goal: str, session_id: str) -> dict:
    """Heuristic-first untuk goal terstruktur (0 panggilan LLM); LLM hanya
    untuk goal kabur; fallback trivial bila semua gagal."""
    if _looks_structured(goal):
        subgoals = _heuristic_plan(goal)
        if 1 < len(subgoals) <= MAX_SUBGOALS:
            plan = {"goal": goal, "subgoals": subgoals,
                    "status": ["pending"] * len(subgoals), "source": "heuristic"}
            _persist(session_id, plan)
            return plan
    payload_msgs = [
        {"role": "system", "content": PLANNER_PROMPT.format(max_subgoals=MAX_SUBGOALS)},
        {"role": "user", "content": f"Goal: {goal}\nJSON:"},
    ]
    try:
        resp = model_client.chat(payload_msgs, tools=None, temperature=0.2,
                                 max_tokens=900)
        raw = resp["choices"][0]["message"].get("content") or ""
        # Ekstrak blok JSON pertama dari jawaban
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(raw[start:end + 1])
            subgoals = data.get("subgoals") or []
            if isinstance(subgoals, list) and subgoals:
                plan = {"goal": goal, "subgoals": subgoals[:MAX_SUBGOALS],
                        "status": ["pending"] * len(subgoals[:MAX_SUBGOALS]),
                        "source": "llm"}
                _persist(session_id, plan)
                return plan
    except Exception:
        pass
    # Fallback deterministik — agen tetap bisa jalan tanpa plan
    plan = {"goal": goal, "subgoals": [
        {"step": 0, "desc": goal, "tool_hint": "none",
         "done_when": "goal tercapai"}], "status": ["pending"], "source": "fallback"}
    _persist(session_id, plan)
    return plan


def load_plan(session_id: str):
    try:
        return json.loads(open(os.path.join(PLAN_DIR, f"{session_id}.json")).read())
    except (OSError, ValueError):
        return None


def mark_step(plan: dict, step_idx: int, ok: bool, note: str = ""):
    if plan and 0 <= step_idx < len(plan["status"]):
        plan["status"][step_idx] = "done" if ok else ("failed" if not ok else "done")
        if note:
            plan.setdefault("notes", []).append(
                {"step": step_idx, "ok": ok, "note": note[:160]})


def _persist(session_id: str, plan: dict):
    try:
        os.makedirs(PLAN_DIR, exist_ok=True)
        json.dump(plan, open(os.path.join(PLAN_DIR, f"{session_id}.json"), "w"),
                  ensure_ascii=False, indent=1)
    except OSError:
        pass
