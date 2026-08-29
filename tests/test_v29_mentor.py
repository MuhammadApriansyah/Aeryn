"""Test V29.3 — panel mentor endpoint."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aeryn_core.reasoning.reflection import PostRunReflection


@pytest.fixture
def refl(tmp_path):
    return PostRunReflection(reflection_dir=str(tmp_path / "r"))


def test_mentor_payload_structure(refl, tmp_path):
    """Simulasi endpoint /mentor — payload harus lengkap."""
    refl.reflect(goal="fs_read /x", plan={"subgoals": [], "status": []},
                 trace=[], answer=None, truncated=False)
    refl.reflect(goal="web_search y", plan={"subgoals": [], "status": []},
                 trace=[], answer="ok")
    digest = refl.digest(last_n=2)
    assert "success_rate" in digest
    assert "runs" in digest
    assert digest["runs"] == 2


def test_mentor_strategies_filter_GOAL_SAM(tmp_path):
    """Hanya strategi tagged GOAL_sam yang masuk active_strategies."""
    refl = PostRunReflection(reflection_dir=str(tmp_path / "refl"))
    refl.reflect(goal="fs_read /x", plan={"subgoals": [], "status": []},
                 trace=[{"type": "tool", "name": "fs_read",
                         "result_digest": "{'error':'x'}"}],
                 answer=None, truncated=True)
    with open(refl.path) as f:
        r = json.loads(f.readline())
    assert r["strategy"] and "GOAL_SAM" in r["strategy"]


def test_mentor_no_strategies_when_all_ok(tmp_path):
    """Run sukses semua → strategy kosong → tidak ada active."""
    refl = PostRunReflection(reflection_dir=str(tmp_path / "refl2"))
    refl.reflect(goal="baca file", plan={"subgoals": [], "status": []},
                 trace=[{"type": "tool", "name": "fs_read",
                         "result_digest": "ok"}],
                 answer="konten", truncated=False)
    with open(refl.path) as f:
        r = json.loads(f.readline())
    assert r["strategy"] == ""
