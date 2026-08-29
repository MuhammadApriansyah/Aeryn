"""Test V38.2 — SOP enforcement untuk sub-agen.

Sub-agen bukan pekerja lepas: wajib terima SOP dan laporkan dalam format.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.platform.sub_agent_runner import build_sop, spawn_subagents


def test_sop_contains_scope_and_limits():
    sop = build_sop(1, "teliti X")
    assert "teliti X" in sop
    assert "3 langkah" in sop and "90s" in sop
    assert "HASIL:" in sop  # format pelaporan wajib


def test_compliant_answer_marked_ok():
    def runner(sop, goal, sid, mi, mw):
        assert "SOP #" in sop, "SOP harus diterima runner"
        return {"answer": "HASIL: ketemu | STATUS: SELESAI", "ok": True}

    r = spawn_subagents(["tugas"], runner=runner)
    item = r["results"][0]
    assert item["ok"] and item["sop_compliant"]


def test_noncompliant_answer_rejected():
    """Jawaban tanpa format HASIL/STATUS → dianggap melanggar SOP."""
    def runner(sop, goal, sid, mi, mw):
        return {"answer": "kayanya sih gitu deh", "ok": True}

    r = spawn_subagents(["tugas"], runner=runner)
    item = r["results"][0]
    assert not item["ok"]
    assert not item["sop_compliant"]
    assert "melanggar" in str(item["error"])


def test_anti_recursion_still_works():
    def evil_runner(sop, goal, sid, mi, mw):
        inner = spawn_subagents([f"{goal}-anak"], runner=lambda *a: {})
        assert "anti-rekursi" in str(inner.get("error", "")) or \
               all(not x["ok"] for x in inner["results"])
        return {"answer": "HASIL: x | STATUS: SELESAI", "ok": True}

    r = spawn_subagents(["induk"], runner=evil_runner)
    assert r["results"][0]["ok"]
