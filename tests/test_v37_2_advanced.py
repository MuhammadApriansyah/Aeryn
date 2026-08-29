"""Test V37.2 — fine-tuning tingkat lanjut.

1. ParityLedger persist: streak selamat dari restart (dulu reset tiap
   restart → tool shadowing tak pernah graduate).
2. prompt_block membawa balik field `strategy` (loop pembelajaran tertutup).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.safety.shadow_mode import ParityLedger


class _FakeRegistry:
    tools = {}


def test_ledger_persists_across_instances(tmp_path):
    p = str(tmp_path / "ledger.json")
    a = ParityLedger(_FakeRegistry(), path=p)
    for _ in range(5):
        a.record("graph_traverse", True)
    assert a.summary()["graph_traverse"]["graduation_ready"]
    # "restart": instance baru dari file yang sama
    b = ParityLedger(_FakeRegistry(), path=p)
    s = b.summary()["graph_traverse"]
    assert s["graduation_ready"], "streak harus selamat dari restart"


def test_ledger_corrupt_file_starts_fresh(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("{bukan json")
    led = ParityLedger(_FakeRegistry(), path=str(p))
    assert led.records == {}
    led.record("x", True)  # tetap berfungsi setelahnya


def test_strategy_injected_back_into_prompt():
    from aeryn_core.memory.episodic_memory import EpisodicMemory
    eps = [{"goal": "cari X", "ok": True, "tools": ["web_search"],
            "lessons": [], "strategy":
            "GOAL_NEW: boros tool 5/2 - pakai heuristik dulu"}]
    block = EpisodicMemory.prompt_block(eps)
    assert "strategi GOAL_NEW" in block


def test_prompt_block_without_strategy_unchanged():
    from aeryn_core.memory.episodic_memory import EpisodicMemory
    eps = [{"goal": "halo", "ok": True, "tools": [], "lessons": []}]
    block = EpisodicMemory.prompt_block(eps)
    assert "strategi" not in block
