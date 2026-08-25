"""Test V37.3 — registry state validation (anti-korupsi file state).

ParityLedger dan ToolGraduationRegistry sempat berbagi satu file dengan
format beda → saling menimpa. Sekarang: file terpisah + _load_state
memvalidasi bentuk entry.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.tool_bridge import ToolGraduationRegistry


def test_load_state_rejects_foreign_format(tmp_path):
    p = str(tmp_path / "tool_graduation.json")
    # file tertimpa format ParityLedger (list bool)
    json.dump({"graph_traverse": [True, True],
               "fs_read": {"status": "native", "success": 5, "fail": 0}},
              open(p, "w"))
    reg = ToolGraduationRegistry(state_path=p)
    assert "graph_traverse" not in reg.grad, "list harus ditolak"
    assert reg.grad["fs_read"]["status"] == "native", "entry valid dipertahankan"


def test_load_state_survives_corrupt(tmp_path):
    p = str(tmp_path / "broken.json")
    open(p, "w").write("{korup")
    reg = ToolGraduationRegistry(state_path=p)
    assert reg.grad == {}


def test_roundtrip_preserves_status(tmp_path):
    p = str(tmp_path / "state.json")
    reg = ToolGraduationRegistry(state_path=p)

    def h():
        return {"ok": True}
    reg.register("demo", h, {"type": "function", "function": {
        "name": "demo", "parameters": {"type": "object", "properties": {}}}})
    reg.execute("demo", {})
    # instance baru membaca balik: status & counter utuh
    reg2 = ToolGraduationRegistry(state_path=p)
    assert reg2.grad["demo"]["success"] == 1
    assert reg2.grad["demo"]["status"] == "bridged"
