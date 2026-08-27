"""Test V38.8 — privacy lintas-user: episode & sessions dilindungi."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.safety_engine import check_path
from aeryn_core.tool_bridge import build_default_registry


def test_episodes_jsonl_protected():
    p = ("/home/sen/aeryn-core-agent/Personalisasi/Database/"
         "episodes/episodes.jsonl")
    ok, why = check_path(p, "read", ["~/aeryn-core-agent"])
    assert not ok and ("episodes" in why or "sensitif" in why)


def test_sessions_dir_read_blocked():
    d = "/home/sen/aeryn-core-agent/Personalisasi/Database/sessions"
    ok, why = check_path(d + "/dc_x.jsonl", "read",
                         ["~/aeryn-core-agent"])
    assert not ok and "privat" in why


def test_live_registry_blocks_episode_read():
    reg = build_default_registry(sandbox_roots=["~/aeryn-core-agent"])
    r = reg.execute("fs_read", {
        "path": "~/aeryn-core-agent/Personalisasi/Database/"
                "episodes/episodes.jsonl"})
    assert "error" in r
    assert r.get("content") is None
