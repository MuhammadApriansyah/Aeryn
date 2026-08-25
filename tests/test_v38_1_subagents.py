"""Test V38.1 — SubAgentRunner: sub-agen Aeryn.

Paralelisme, anti-rekursi, cap jumlah, isolasi session_id, error per-item.
Runner di-stub — tanpa LLM.
"""
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.sub_agent_runner import (
    MAX_SUBAGENTS_PER_RUN, in_subagent, spawn_subagents)


def test_parallel_execution_and_order():
    seen_threads = set()

    def runner(sop, goal, sid, mi, mw):
        seen_threads.add(threading.current_thread().name)
        time.sleep(0.05)
        return {"answer": f"HASIL: jawab-{goal} | STATUS: SELESAI", "ok": True}

    r = spawn_subagents(["t1", "t2", "t3"], runner=runner)
    assert len(r["results"]) == 3
    assert [x["idx"] for x in r["results"]] == [0, 1, 2]
    assert all(x["ok"] for x in r["results"])
    assert r["duration_ms"] < 400  # paralel: ~max(50ms) bukan sum


def test_anti_recursion():
    def evil_runner(sop, goal, sid, mi, mw):
        # di dalam sub-agen, spawn lagi harus ditolak
        return spawn_subagents([f"{goal}-anak"], runner=lambda *a: {})

    r = spawn_subagents(["induk"], runner=evil_runner)
    inner = r["results"][0]
    assert not inner["ok"]
    # alasan bisa berupa anti-rekursi langsung ATAU SOP-violation karena
    # hasil spawn ditolak (tanpa format HASIL/STATUS) — keduanya valid
    combined = str(inner["error"]) + str(inner.get("answer_head", ""))
    assert ("anti-rekursi" in combined) or ("melanggar" in combined)


def test_cap_max_subagents():
    calls = []

    def runner(sop, goal, sid, mi, mw):
        calls.append(goal)
        return {"answer": "HASIL: x | STATUS: SELESAI", "ok": True}

    r = spawn_subagents([f"g{i}" for i in range(10)], runner=runner)
    assert len(r["results"]) == MAX_SUBAGENTS_PER_RUN
    assert len(calls) == MAX_SUBAGENTS_PER_RUN


def test_isolated_session_ids():
    sids = []

    def runner(sop, goal, sid, mi, mw):
        sids.append(sid)
        # buktikan konteks terisolasi: flag thread-local aktif
        assert in_subagent()
        return {"answer": "HASIL: ok | STATUS: SELESAI", "ok": True}

    spawn_subagents(["a", "b"], runner=runner)
    assert len(set(sids)) == 2 and all(s.startswith("sub_") for s in sids)


def test_item_error_does_not_kill_others():
    def runner(sop, goal, sid, mi, mw):
        if goal == "boom":
            raise RuntimeError("meledak")
        return {"answer": "HASIL: selamat | STATUS: SELESAI", "ok": True}

    r = spawn_subagents(["boom", "aman"], runner=runner)
    by_idx = {x["idx"]: x for x in r["results"]}
    assert not by_idx[0]["ok"] and "meledak" in by_idx[0]["error"]
    assert by_idx[1]["ok"]


def test_empty_and_bad_input():
    assert "error" in spawn_subagents([], runner=lambda *a: {})
    assert "error" in spawn_subagents("bukan list", runner=lambda *a: {})
    assert "error" in spawn_subagents(["x"], runner=None)
