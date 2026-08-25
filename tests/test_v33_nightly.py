"""Test V33 Fase 2 — nightly_reflection aggregator (deterministik)."""
import importlib.util
import json
import os
import sys
import tempfile
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def nightly(tmp_path, monkeypatch):
    """Muat modul dengan path episode & output diarahkan ke tmp."""
    ep_dir = tmp_path / "episodes"
    ep_dir.mkdir()
    out_dir = tmp_path / "nightly"

    spec = importlib.util.spec_from_file_location(
        "nightly_reflection", os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts", "nightly_reflection.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "EPISODES", str(ep_dir / "episodes.jsonl"))
    monkeypatch.setattr(mod, "OUT_DIR", str(out_dir))
    return mod


def _write_episodes(path, eps):
    with open(path, "w") as f:
        for e in eps:
            f.write(json.dumps(e) + "\n")


def test_empty_window(nightly):
    r = nightly.aggregate(86400)
    assert r["runs"] == 0
    assert r["success_rate_pct"] == 100.0


def test_mixed_episodes(nightly):
    now = time.time()
    _write_episodes(nightly.EPISODES, [
        {"ts": now - 3600, "session_id": "s1", "goal": "g", "tools": ["web_search"],
         "ok": True, "error": "", "lessons": []},
        {"ts": now - 7200, "session_id": "s2", "goal": "h", "tools": [],
         "ok": False, "error": "LLM unreachable", "lessons": ["run gagal"]},
        # di luar window — tidak boleh ikut
        {"ts": now - 200000, "session_id": "old", "goal": "x", "tools": [],
         "ok": True, "error": "", "lessons": []},
        # korup — dilewati tanpa meledak
        "bukan json\n",
    ])
    r = nightly.aggregate(86400)
    assert r["runs"] == 2
    assert r["errors"] == 1
    assert r["unique_sessions"] == 2
    assert r["top_tools"] == {"web_search": 1}
    assert r["success_rate_pct"] == 50.0
    assert any("unreachable" in e for e in r["error_samples"])


def test_write_report_overwrites_same_day(nightly):
    rep1 = nightly.aggregate(0)
    p1 = nightly.write_report(rep1)
    rep2 = nightly.aggregate(0)
    p2 = nightly.write_report(rep2)
    assert p1 == p2
    with open(p1) as f:
        assert json.load(f)["runs"] == rep2["runs"]


def test_handoff_summary_shapes(nightly):
    assert nightly.handoff_summary({"runs": 0}) == ""
    s = nightly.handoff_summary({
        "runs": 5, "errors": 1, "success_rate_pct": 80.0,
        "generated_at": "2026-08-25T00:00:00Z",
        "error_samples": ["boom"], "top_tools": {"web_search": 3}})
    assert "5 run" in s and "80.0% sukses" in s and "web_search" in s
