"""Test V39.2 — basic tools (datetime/math) + fallback map lengkap."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.utils.basic_tools import datetime_now, math_calc
from aeryn_core.utils.fallback_router import FALLBACK_MAP


def test_datetime_now_wib():
    r = datetime_now()
    assert r["ok"] and r["tz"] == "Asia/Jakarta"
    assert r["hari"] in ("Senin", "Selasa", "Rabu", "Kamis", "Jumat",
                         "Sabtu", "Minggu")
    assert len(r["tanggal"]) == 10 and len(r["jam"]) == 8


def test_math_safe_expressions():
    assert math_calc("2+3*4")["result"] == 14
    assert math_calc("(10-4)/3")["result"] == 2
    assert math_calc("2**10")["result"] == 1024


def test_math_rejects_dangerous():
    for expr in ("__import__('os').system('ls')", "__class__",
                 "open('/etc/passwd')", "exec('x=1')"):
        r = math_calc(expr)
        assert not r["ok"], expr


def test_all_daemon_tools_have_fallback_map():
    """TIDAK ADA tool tanpa arahan error — kontrak V39.1 penuh."""
    expected = {"web_search", "web_read", "http_get", "fs_read", "fs_write",
                "terminal", "ask_hermes", "spawn_subagents", "memory_search",
                "graph_traverse", "pitfall_search", "core_memory_edit",
                "datetime_now", "math_calc"}
    missing = expected - set(FALLBACK_MAP.keys())
    assert not missing, f"tool tanpa fallback map: {missing}"
