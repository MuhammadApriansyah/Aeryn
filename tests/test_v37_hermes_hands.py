"""Test V37 — Hermes Hands: delegasi kerja berat ke Hermes via CLI.

Semua subprocess DI-MOCK — tidak pernah memanggil binary `hermes` asli.
"""
import json
import os
import subprocess
import sys
import time
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core import hermes_hands as hh


@pytest.fixture()
def fresh(monkeypatch, tmp_path):
    """Arahkan counter ke tmp + pastikan env bersih."""
    monkeypatch.setattr(hh, "_DB_DIR", str(tmp_path))
    monkeypatch.setattr(hh, "COUNTER_FILE",
                        str(tmp_path / "hermes_hands_usage.json"))
    monkeypatch.delenv("AERYN_HERMES_HANDS_DAILY", raising=False)
    return tmp_path


def _fake_run(stdout="", returncode=0, raises=None):
    if raises is not None:
        def run(argv, **kwargs):
            raise raises
    else:
        def run(argv, **kwargs):
            proc = MagicMock()
            proc.stdout = stdout
            proc.stderr = ""
            proc.returncode = returncode
            assert argv[1:3] == ["chat", "-q"], f"argv salah: {argv}"
            return proc
    return run


def test_success(fresh, monkeypatch):
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        proc = MagicMock()
        proc.stdout = "selesai! semua test hijau."
        proc.returncode = 0
        return proc

    monkeypatch.setattr(hh.subprocess, "run", run)
    res = hh.ask_hermes("perbaiki bug di modul planner sekarang")
    assert res["ok"] is True
    assert "test hijau" in res["output"]
    assert isinstance(res["duration_ms"], int) and res["duration_ms"] >= 0
    # argv benar: [hermes, chat, -q, task]
    assert calls and calls[0][0].endswith("hermes")
    assert calls[0][1:] == ["chat", "-q",
                            "perbaiki bug di modul planner sekarang"]
    # counter tercatat 1x
    with open(hh.COUNTER_FILE) as f:
        assert json.load(f)["count"] == 1


def test_timeout_kills_and_fails(fresh, monkeypatch):
    monkeypatch.setattr(
        hh.subprocess, "run",
        _fake_run(raises=subprocess.TimeoutExpired(cmd="hermes",
                                                   timeout=240)))
    res = hh.ask_hermes("task panjang yang tidak akan selesai cepat ini")
    assert res["ok"] is False
    assert "timeout" in res["error"]


def test_daily_cap_exhausted_no_spawn(fresh, monkeypatch):
    # Prefill counter hari ini sudah penuh (cap default 20)
    with open(hh.COUNTER_FILE, "w") as f:
        json.dump({"date": time.strftime("%Y-%m-%d"), "count": 20}, f)

    called = []
    monkeypatch.setattr(hh.subprocess, "run",
                        lambda *a, **k: called.append(a))
    res = hh.ask_hermes("coba delegasi padahal cap sudah habis")
    assert res == {"ok": False, "error": "daily cap"}
    assert not called  # TIDAK spawn proses

    # Override env menaikkan cap → boleh jalan lagi
    monkeypatch.setenv("AERYN_HERMES_HANDS_DAILY", "25")
    monkeypatch.setattr(hh.subprocess, "run", _fake_run(stdout="oke"))
    assert hh.ask_hermes("delegasi kedua dengan cap dinaikkan")["ok"] is True


def test_task_too_short_rejected(fresh, monkeypatch):
    called = []
    monkeypatch.setattr(hh.subprocess, "run",
                        lambda *a, **k: called.append(a))
    for bad in ("", "   ", "pendek", None):
        res = hh.ask_hermes(bad)
        assert res["ok"] is False
        assert "pendek" in res["error"] or "kosong" in res["error"]
    assert not called


def test_output_truncated_to_last_4000(fresh, monkeypatch):
    long_out = "A" * 6000 + "TAIL" + "B" * 100
    monkeypatch.setattr(hh.subprocess, "run", _fake_run(stdout=long_out))
    res = hh.ask_hermes("hasilkan output sangat panjang untuk uji potong")
    assert len(res["output"]) == 4000
    assert res["truncated"] is True
    # Yang disimpan adalah EKOR (4000 char terakhir), bukan kepala
    assert res["output"].endswith("TAIL" + "B" * 100)


def test_counter_rollover_on_date_change(fresh, monkeypatch):
    # Kemarin penuh → hari baru harus reset dan mengizinkan
    with open(hh.COUNTER_FILE, "w") as f:
        json.dump({"date": "2026-08-24", "count": 20}, f)
    monkeypatch.setattr(hh.subprocess, "run", _fake_run(stdout="lancar"))

    res = hh.ask_hermes("panggilan pertama setelah rollover tanggal")
    assert res["ok"] is True
    data = json.load(open(hh.COUNTER_FILE))
    assert data["date"] == time.strftime("%Y-%m-%d")
    assert data["count"] == 1


def test_schema_shape():
    fn = hh.ASK_HERMES_SCHEMA["function"]
    assert fn["name"] == "ask_hermes"
    assert fn["parameters"]["required"] == ["task"]
    assert fn["parameters"]["properties"]["task"]["type"] == "string"


def test_hermes_binary_missing(fresh, monkeypatch):
    monkeypatch.setattr(hh.shutil, "which", lambda _: None)
    monkeypatch.setattr(
        hh.subprocess, "run",
        _fake_run(raises=FileNotFoundError("hermes")))
    res = hh.ask_hermes("task dengan binary hermes yang hilang")
    assert res["ok"] is False
    assert "tidak ditemukan" in res["error"]
