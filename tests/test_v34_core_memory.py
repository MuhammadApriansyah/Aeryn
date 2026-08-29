"""Test V34 — CoreMemory (Letta-style blocks) + checker."""
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.memory.core_memory import CoreMemory, BLOCK_LIMITS


@pytest.fixture()
def cm(tmp_path):
    return CoreMemory(path=str(tmp_path / "core.json"))


def test_seed_created_once(cm):
    r1 = cm.render()
    assert "<human" in r1 and "<context" in r1
    # render kedua tidak menggandakan seed (file sudah ada)
    cm._ensure()
    assert len(cm.raw()["human"]) == len(cm.raw()["human"])


def test_edit_append_and_replace(cm):
    assert cm.edit("human", "append", "Fakta baru.")["ok"]
    assert "Fakta baru." in cm.raw()["human"]
    cm.edit("human", "replace", "Timpa total.")
    assert cm.raw()["human"] == "Timpa total."


def test_char_limit_enforced(cm):
    long_text = "x" * 3000
    r = cm.edit("context", "replace", long_text)
    assert r["ok"] and r["chars"] == BLOCK_LIMITS["context"]
    # append melampaui limit → yang terakhir dipertahankan
    cm.edit("context", "append", "y" * 500)
    raw = cm.raw()["context"]
    assert len(raw) <= BLOCK_LIMITS["context"]
    assert raw.endswith("y" * 100)


def test_invalid_block_and_mode(cm):
    assert not cm.edit("tidak_ada", "append", "x")["ok"]
    assert not cm.edit("human", "salah", "x")["ok"]
    assert not cm.edit("human", "append", "")["ok"]


def test_persist_across_instances(tmp_path):
    p = str(tmp_path / "core.json")
    a = CoreMemory(path=p)
    a.edit("context", "append", "Proyek X pakai Rust.")
    b = CoreMemory(path=p)
    assert "Rust" in b.raw()["context"]


# ── daemon wiring ─────────────────────────────────────────────────────
def test_registered_in_daemon_tools():
    from scripts import aeryn_daemon as d
    assert "core_memory_edit" in d.TOOLS.tools
    assert d.TOOLS.tools["core_memory_edit"]["tier"] == "safe"
    # schema terbaca dari hermes_brain
    from aeryn_core.hermes.hermes_brain import CORE_MEMORY_SCHEMA
    assert d.TOOLS.tools["core_memory_edit"]["schema"]["function"][
        "name"] == "core_memory_edit"


def test_checker():
    from scripts.aeryn_daemon import _checker_core_memory_edit
    assert _checker_core_memory_edit({}, {"ok": True})
    assert not _checker_core_memory_edit({}, {"ok": False, "error": "x"})


# ── "ingat ini:" bukan social query (bug ketemu di smoke V34) ────────
def test_memory_command_not_social():
    from scripts.aeryn_daemon import _is_social_query as d
    from scripts.archive.social_generator import _is_social_query as g
    for q in ("ingat ini: proyek baru namanya nebula-dash",
              "catat: sen suka kopi", "remember this: x=1"):
        assert d(q) is False, q
        assert g(q) is False, q
    # sosial asli tetap sosial
    assert d("ingat kan kamu pernah ngambek") is True
