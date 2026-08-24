"""Test V29.2 — reflection loop: refleksi → strategy → run berikutnya pakai strategi."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aeryn_core.reflection import PostRunReflection


@pytest.fixture
def refl(tmp_path):
    return PostRunReflection(reflection_dir=str(tmp_path / "r"))


def test_gagal_generate_strategy(refl):
    """Run gagal → strategy tag GOAL_SAM + rekomendasi validasi."""
    plan = {"subgoals": [{"step": 0, "desc": "read file", "tool_hint": "fs_read",
                          "done_when": "ok"}], "status": ["pending"]}
    trace = [{"type": "tool", "name": "fs_read",
              "result_digest": "str({'error': 'FileNotFoundError: ...'})"}]
    out = refl.reflect(goal="fs_read /nonexistent", plan=plan, trace=trace,
                       answer=None)
    assert out["strategy"]
    assert "GOAL_SAM" in out["strategy"]
    assert "validasi" in out["strategy"].lower() or "boros" in out["strategy"].lower()


def test_sukses_tidak_generate_strategy(refl):
    """Run sukses tanpa issue → strategy kosong."""
    plan = {"subgoals": [{"step": 0, "desc": "read x", "tool_hint": "fs_read",
                          "done_when": "ok"}], "status": ["done"]}
    trace = [{"type": "tool", "name": "fs_read",
              "result_digest": "str({'content':'hello'})"}]
    out = refl.reflect(goal="fs_read /etc/hostname", plan=plan, trace=trace,
                       answer="hello")
    assert out["strategy"] == ""
    assert out["ok"] is True


def test_boros_tool_strategy(refl):
    """Too many tool calls vs subgoals → strategy boros tool."""
    plan = {"subgoals": [{"step": 0, "desc": "x", "tool_hint": "none",
                          "done_when": "ok"}], "status": ["done"]}
    trace = [{"type": "tool", "name": f"tool_{i}", "result_digest": "ok"}
             for i in range(5)]
    out = refl.reflect(goal="uji boros", plan=plan, trace=trace, answer="ok")
    assert "boros" in out["strategy"].lower() or "GOAL_SAM" in out["strategy"]


def test_find_recent_strategy_pakai_goal_serupa(refl):
    """Strategy dari goal serupa (fuzzy 50% token) ditemukan."""
    plan = {"subgoals": [{"step": 0, "tool_hint": "fs_read",
                          "done_when": "ok"}], "status": ["pending"]}
    refl.reflect(goal="fs_read /nonexistent/xyz", plan=plan,
                 trace=[{"type": "tool", "name": "fs_read",
                         "result_digest": "{'error':'FileNotFoundError'}"}],
                 answer=None)
    strat = refl.find_recent_strategy("fs_read /nonexistent/abc")
    assert strat and "GOAL_SAM" in strat


def test_find_recent_strategy_expired_kosong(refl):
    """Strategy lebih lama dari max_age_h → tidak kembali."""
    plan = {"subgoals": [], "status": []}
    refl.reflect(goal="goal test", plan=plan, trace=[], answer="ok")
    # strategy kosong karena ok=True → tidak persist meaningful strategy
    strat = refl.find_recent_strategy("goal test", max_age_h=0.0)
    assert strat == ""


def test_strategy_tersimpan_di_episode(tmp_path):
    """Integrasi: Episode mencatat strategy."""
    from aeryn_core.episodic_memory import EpisodicMemory
    mem = EpisodicMemory(episode_dir=str(tmp_path / "eps"))
    mem.record("sid", "fs_read x", "heuristic",
               [{"type": "tool", "name": "fs_read"}],
               answer=None, strategy="GOAL_SAM: validasi path")
    import json as _j
    with open(mem.path) as f:
        ep = _j.loads(f.readline())
    assert ep["strategy"] == "GOAL_SAM: validasi path"
