"""Test V39.9b — cerewet parity di jalur sosial."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "scripts"))

import aeryn_core.reasoning.cerewet_mode as cm


def test_social_nudge_appends_when_pending(tmp_path, monkeypatch):
    monkeypatch.setattr(cm, "COMMITMENTS_PATH",
                        str(tmp_path / "c.json"))
    from scripts.archive.social_generator import _cerewet_social_nudge
    uid = "1541581954439454850"
    cm.add_commitment(f"dc_{uid}_chan", "nanti aku install docker")
    nudge = _cerewet_social_nudge(uid)
    assert nudge and "install docker" in nudge and "😏" in nudge


def test_social_nudge_empty_when_none(tmp_path, monkeypatch):
    monkeypatch.setattr(cm, "COMMITMENTS_PATH",
                        str(tmp_path / "none.json"))
    from scripts.archive.social_generator import _cerewet_social_nudge
    assert _cerewet_social_nudge("000000") == ""


def test_nudge_marks_nagged_no_double(tmp_path, monkeypatch):
    monkeypatch.setattr(cm, "COMMITMENTS_PATH",
                        str(tmp_path / "c.json"))
    from scripts.archive.social_generator import _cerewet_social_nudge
    uid = "555000111"
    cm.add_commitment(f"dc_{uid}", "besok gue rapat")
    first = _cerewet_social_nudge(uid)
    second = _cerewet_social_nudge(uid)  # cooldown → kosong
    assert first and second == ""
