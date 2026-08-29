"""Test V39.10 — DriftGuard: deteksi Hermes-drift otomatis."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))) + "/scripts")

from scripts.archive.drift_guard import CHECKS, main


def test_all_checks_run_and_return_tuple():
    for name, fn in CHECKS:
        ok, msg = fn()
        assert isinstance(ok, bool) and msg, name


def test_current_environment_is_healthy():
    """Kondisi sekarang: semua titik integrasi harus hijau."""
    assert main() == 0


def test_drift_detected_when_db_missing(monkeypatch):
    from scripts.archive import drift_guard as dg
    monkeypatch.setattr(dg, "STATE_DB", "/nonexistent/state.db")
    ok, msg = dg.check_state_db()
    assert not ok


def test_auth_missing_key_flagged(tmp_path):
    from scripts.archive import drift_guard as dg
    fake = tmp_path / "auth.json"
    fake.write_text('{"providers": {"nous": {}}}')
    old = dg.AUTH
    dg.AUTH = str(fake)
    try:
        ok, msg = dg.check_auth()
        assert not ok and "hilang" in msg
    finally:
        dg.AUTH = old


def test_corrupt_index_flagged(tmp_path):
    from scripts.archive import drift_guard as dg
    fake = tmp_path / "INDEX.json"
    fake.write_text("{bukan json")
    old = dg.INDEX
    dg.INDEX = str(fake)
    try:
        ok, msg = dg.check_index()
        assert not ok and "korup" in msg.lower()
    finally:
        dg.INDEX = old
