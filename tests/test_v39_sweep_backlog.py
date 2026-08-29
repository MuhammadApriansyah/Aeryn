"""Test V39-F4/F5 — injection sweep + weakness backlog."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.safety.injection_sweep import run_sweep, weakness_backlog


def test_all_indirect_samples_wrapped():
    r = run_sweep()
    assert r["all_wrapped"], "semua konten harus dibungkus pembatas"


def test_detection_catches_common_patterns():
    r = run_sweep()
    # minimal pola paling kasar harus kedetek
    assert r["detected"] >= 3, f"hanya {r['detected']}/{r['total']} terdeteksi"


def test_weakness_backlog_clusters_failures(tmp_path):
    p = tmp_path / "episodes.jsonl"
    rows = [
        {"goal": "deploy ke server produksi sekarang", "ok": False,
         "error": "iterasi habis", "tools": ["t1", "t2", "t3"]},
        {"goal": "deploy ke server staging dulu", "ok": False,
         "error": "", "tools": ["t1"]},
        {"goal": "halo apa kabar", "ok": True, "tools": []},
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    backlog = weakness_backlog(str(p))
    assert any("deploy" in b["cluster"] for b in backlog)
    assert all(b["count"] >= 1 for b in backlog)


def test_weakness_backlog_empty_on_missing_file(tmp_path):
    assert weakness_backlog(str(tmp_path / "tak-ada.jsonl")) == []
