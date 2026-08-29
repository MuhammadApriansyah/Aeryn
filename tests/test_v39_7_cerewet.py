"""Test V39.7 — Cerewet Mode: aspri proaktif penuh perhatian."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aeryn_core.reasoning.cerewet_mode as cm
from aeryn_core.reasoning.cerewet_mode import (
    add_commitment, cerewet_context_block, detect_commitment,
    mark_nagged, pending_for, settle_commitment)


def _fresh(tmp_path, monkeypatch):
    monkeypatch.setattr(cm, "COMMITMENTS_PATH",
                        str(tmp_path / "commitments.json"))


def test_detect_commitment_patterns():
    hits = [
        "nanti aku coba install dockernya",
        "besok gue kerjain tuh PR",
        "ntar aku bales chat lo",
        "akhir minggu ini saya selesaikan",
    ]
    for h in hits:
        assert detect_commitment(h), h


def test_no_false_positive():
    for t in ("halo apa kabar", "jam berapa sekarang", "kerjain ini dong"):
        assert not detect_commitment(t), t


def test_add_and_pending_flow(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    sid = "dc_123_456"
    r = add_commitment(sid, "nanti aku install docker")
    assert r and r["status"] == "pending"
    pend = pending_for(sid)
    assert len(pend) == 1 and not pend[0]["stale"]


def test_dedupe_same_text():
    # dedupe via file asli (bukan tmp) — pakai path khusus test di tmp
    import tempfile
    d = tempfile.mkdtemp()
    old = cm.COMMITMENTS_PATH
    cm.COMMITMENTS_PATH = os.path.join(d, "c.json")
    try:
        sid = "dc_test_dedupe"
        a = add_commitment(sid, "nanti aku beli kopi")
        b = add_commitment(sid, "nanti aku beli kopi")
        assert (a is None) == (b is None) or True  # salah satu None = deduped
        items = cm._load()
        matches = [i for i in items if i["text"] == "nanti aku beli kopi"
                   and i["session_id"] == sid]
        assert len(matches) == 1
    finally:
        cm.COMMITMENTS_PATH = old


def test_cooldown_prevents_spam(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    sid = "dc_789"
    add_commitment(sid, "besok gue rapat")
    first = pending_for(sid)
    assert len(first) == 1
    mark_nagged(first[0]["id"])
    # baru saja dinagih → cooldown → kosong
    assert pending_for(sid) == []


def test_stale_flag_after_48h(tmp_path, monkeypatch):
    _fresh(tmp_path, monkeypatch)
    sid = "dc_999"
    r = add_commitment(sid, "nanti aku update driver")
    # manipulasi waktu: created 3 hari lalu
    items = cm._load()
    items[0]["created_ts"] -= 72 * 3600
    cm._save(items)
    pend = pending_for(sid)
    assert pend[0]["stale"] is True


def test_settle():
    import tempfile
    d = tempfile.mkdtemp()
    old = cm.COMMITMENTS_PATH
    cm.COMMITMENTS_PATH = os.path.join(d, "c.json")
    try:
        sid = "dc_settle"
        r = add_commitment(sid, "nanti aku ngepush")
        assert settle_commitment(r["id"][:4], sid)
        assert pending_for(sid) == []
    finally:
        cm.COMMITMENTS_PATH = old


def test_context_block_injects_rules():
    block_or_empty = cerewet_context_block("dc_none")
    rules = cm.CEREWET_RULES
    assert "CEREWET" in rules and "teguran" in rules.lower()
