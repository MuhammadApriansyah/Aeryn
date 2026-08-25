"""Test V33 Shared Brain — hermes_brain bridge.

Tiga tool (memory_search, graph_traverse, pitfall_search) harus:
- terdaftar di registry
- mengembalikan struktur dict yang benar dari CLI Hermes
- tahan query kosong / output tak terduga
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.tool_bridge import build_default_registry
from aeryn_core.hermes_brain import (
    register,
    _memory_search,
    _graph_traverse,
    _pitfall_search,
)


@pytest.fixture(scope="module")
def tools():
    reg = build_default_registry(sandbox_roots=["~/aeryn-core-agent"])
    return register(reg)


def test_all_registered(tools):
    for name in ("memory_search", "graph_traverse", "pitfall_search"):
        assert name in tools.tools, f"{name} gak ke-daftar"
        assert tools.tools[name]["tier"] == "safe"


def test_memory_search_real(tools):
    r = tools.execute("memory_search", {"query": "webnovel stack", "top": 1})
    assert "error" not in r or "results" in r
    if "results" in r:
        for item in r["results"]:
            assert {"id", "score", "summary"} <= set(item)


def test_graph_traverse_real(tools):
    r = tools.execute("graph_traverse", {"entity": "aeryn-core"})
    assert isinstance(r.get("edges"), list)
    assert isinstance(r.get("node"), str)
    assert any(e["relation"] and e["target"] for e in r["edges"][:3])


def test_pitfall_search_real(tools):
    r = tools.execute("pitfall_search", {"symptom": "SSL EOF"})
    assert isinstance(r.get("pitfalls"), list)
    if r["pitfalls"]:
        p = r["pitfalls"][0]
        assert {"n", "id", "symptom"} <= set(p)


def test_empty_queries_tolerated():
    m = _memory_search("")
    assert m == {"results": [], "note": "query kosong"}
    g = _graph_traverse("  ")
    assert g.get("edges") == []
    p = _pitfall_search("")
    assert p.get("pitfalls") == []


# ── parity checkers dari daemon ──────────────────────────────────────
from scripts.aeryn_daemon import (
    _checker_memory_search,
    _checker_graph_traverse,
    _checker_pitfall_search,
)


def test_checkers_accept_valid():
    assert _checker_memory_search({}, {"results": []})
    assert _checker_graph_traverse({}, {"node": "x", "edges": []})
    assert _checker_pitfall_search({}, {"pitfalls": []})


def test_checkers_reject_invalid():
    assert not _checker_memory_search({}, {"nope": 1})
    assert not _checker_graph_traverse({}, {"node": "x"})
    assert not _checker_pitfall_search({}, {"wrong": []})
    assert not _checker_memory_search({}, None)


def test_top_as_string_coerced(tools):
    """LLM kadang kirim "top": "2" sebagai string — tidak boleh TypeError."""
    r = tools.execute("memory_search", {"query": "aeryn", "top": "2"})
    assert isinstance(r, dict) and "results" in r
    r2 = tools.execute("memory_search", {"query": "aeryn", "top": "bukan-angka"})
    assert isinstance(r2, dict) and "results" in r2
