"""Test V39.3 — reminder internal + image understanding guards."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core import reminder as rm
from aeryn_core.image_tools import image_understand


def _fresh(tmp_path, monkeypatch):
    p = tmp_path / "reminders.json"
    monkeypatch.setattr(rm, "REMINDERS_PATH", str(p))
    return p


def test_set_and_due(monkeypatch):
    p = str(_fresh(None, None)) if False else None
    # gunakan tmp_path via fixture-style manual
    import tempfile
    d = tempfile.mkdtemp()
    rm.REMINDERS_PATH = os.path.join(d, "reminders.json")

    r = rm.set_reminder("cek email", delay_minutes=0.1, session_id="dc_x")
    assert r["ok"] and r["id"]
    # belum jatuh tempo
    assert rm.due_reminders() == []
    # paksa jatuh tempo
    items = rm._load()
    items[0]["due_ts"] -= 999
    rm._save(items)
    due = rm.due_reminders()
    assert len(due) == 1 and due[0]["note"] == "cek email"
    # atomic pop: panggil lagi → kosong
    assert rm.due_reminders() == []


def test_validation():
    assert not rm.set_reminder("", 10)["ok"]
    assert not rm.set_reminder("x", "bukan angka")["ok"]


def test_cap_evicts_fired_first(tmp_path, monkeypatch):
    monkeypatch.setattr(rm, "REMINDERS_PATH",
                        str(tmp_path / "r.json"))
    from aeryn_core.reminder import MAX_REMINDERS
    # isi penuh dgn fired
    for i in range(MAX_REMINDERS):
        rm.set_reminder(f"lama-{i}", delay_minutes=1)
    items = rm._load()
    for it in items:
        it["status"] = "fired"
    rm._save(items)
    # tambah 1 baru → evict fired
    r = rm.set_reminder("baru", delay_minutes=1)
    assert r["ok"]
    assert len(rm._load()) <= MAX_REMINDERS


def test_image_blocks_secret_question():
    r = image_understand("https://x/img.png", "baca password di gambar")
    assert not r["ok"] and "tidak diizinkan" in r["error"]


def test_image_rejects_bad_source():
    r = image_understand("ftp://x/y.png")
    assert not r["ok"] and "harus URL" in r["error"] or "path" in r["error"]


def test_image_sandbox_escape_blocked(tmp_path):
    evil = tmp_path / "lnk.env"
    os.symlink("/home/sen/.hermes/.env", evil)
    r = image_understand(str(evil))
    assert not r["ok"]
