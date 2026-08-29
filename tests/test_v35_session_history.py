"""Test V35 INFRA-1 — SessionHistory: riwayat multi-turn + budget."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aeryn_core.memory.session_history as sh


@pytest.fixture()
def fresh(monkeypatch, tmp_path):
    monkeypatch.setattr(sh, "_DB_DIR", str(tmp_path / "sessions"))
    return tmp_path


def test_record_and_load_roundtrip(fresh):
    sh.record("s1", "user", "halo")
    sh.record("s1", "assistant", "hai juga!")
    hist = sh.load("s1")
    assert len(hist) == 2
    assert hist[0]["role"] == "user" and hist[0]["content"] == "halo"
    assert hist[1]["content"] == "hai juga!"


def test_budget_keeps_recent_drops_old(fresh):
    for i in range(50):
        sh.record("s2", "user", f"pertanyaan nomor {i} " + "x" * 200)
        sh.record("s2", "assistant", "jawaban " + "y" * 200)
    hist = sh.load("s2", char_budget=3000)
    joined = json.dumps(hist, ensure_ascii=False)
    assert len(joined) < 4500  # dalam budget + ringkasan
    assert "nomor 49" in joined  # terbaru utuh
    assert "[ringkasan" in joined  # lama diringkas
    assert "nomor 5 " not in joined  # tua tidak ikut utuh


def test_corrupt_lines_skipped(fresh):
    p = os.path.join(str(fresh), "sessions", "s3.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write('{"role": "user", "content": "ok"}\n')
        f.write("BUKAN JSON\n")
        f.write('"juga rusak"\n')
    hist = sh.load("s3")
    assert len(hist) == 1


def test_reset_and_empty(fresh):
    assert sh.load("tak_ada") == []
    sh.record("s4", "user", "x")
    sh.reset("s4")
    assert sh.load("s4") == []


def test_session_id_sanitized(fresh):
    sh.record("../../etc/passwd", "user", "x")
    files = os.listdir(os.path.join(str(fresh), "sessions"))
    assert all("/" not in f and ".." not in f for f in files)
