"""Test V39.9 — fallback map lengkap (16/16 tool) + nightly metrik baru."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.utils.fallback_router import FALLBACK_MAP


def test_all_16_tools_have_fallback():
    expected = {"web_search", "web_read", "http_get", "fs_read", "fs_write",
                "terminal", "ask_hermes", "spawn_subagents", "memory_search",
                "graph_traverse", "pitfall_search", "core_memory_edit",
                "datetime_now", "math_calc", "set_reminder",
                "image_understand"}
    missing = expected - set(FALLBACK_MAP.keys())
    assert not missing, f"tool tanpa fallback map: {missing}"


def test_reminder_fallback_mentions_range():
    r = FALLBACK_MAP["set_reminder"][0]
    assert "rentang" in r["when"] and "Tanyakan" in r["say"]


def test_image_fallback_no_bypass():
    for rule in FALLBACK_MAP["image_understand"]:
        say = rule["say"].lower()
        assert "jangan" in say or "laporkan" in say or "minta user" in say


def test_nightly_counts_new_features():
    """Fungsi agregasi nightly harus mengenali trace verifier/research."""
    import ast
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))),
        "scripts", "nightly_reflection.py")).read()
    assert '"verifier"' in src and "v39_features" in src
    tree = ast.parse(src)
    fn_names = {n.name for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef)}
    assert any("aggregate" in n for n in fn_names)
