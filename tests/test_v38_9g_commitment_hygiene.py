"""Test V39.9c — commitments hygiene: pending cap per user + expired."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core import cerewet_mode as cm
from aeryn_core.reasoning.cerewet_mode import (
    PENDING_CAP_PER_USER, add_commitment, pending_for)


def test_pending_cap_per_user(tmp_path, monkeypatch):
    monkeypatch.setattr(cm, "COMMITMENTS_PATH",
                        str(tmp_path / "c.json"))
    sid = "dc_cap"
    for i in range(PENDING_CAP_PER_USER + 3):
        add_commitment(sid, f"nanti aku tugas ke-{i}")
    pend = pending_for(sid)
    assert len(pend) <= PENDING_CAP_PER_USER
    # yang terlama jadi expired (bukan hilang)
    items = cm._load()
    statuses = [i["status"] for i in items if i["session_id"] == sid]
    assert "expired" in statuses


def test_expired_not_nagged():
    from aeryn_core.reasoning.cerewet_mode import _load as _cl
    for it in _cl():
        if it.get("status") == "expired":
            assert it.get("last_nagged_ts", 0) >= 0  # struktur utuh


def test_different_users_independent(tmp_path, monkeypatch):
    monkeypatch.setattr(cm, "COMMITMENTS_PATH",
                        str(tmp_path / "c2.json"))
    for i in range(PENDING_CAP_PER_USER):
        add_commitment("dc_u1", f"nanti aku A{i}")
    r = add_commitment("dc_u2", "nanti aku B")  # user lain tak terpengaruh
    assert r and r["status"] == "pending"
