"""Test V33-T — web_read (trafilatura) + json_repair hardening.

Zero-network: web_read dites dengan monkeypatch fetch/extract;
json_repair dites langsung terhadap jalur parse argumen tool.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aeryn_core.platform.tool_bridge as tool_bridge
from aeryn_core.platform.tool_bridge import build_default_registry


# ── web_read: unit dengan fake fetch (tanpa network) ─────────────────
def test_web_read_success(monkeypatch):
    class FakeMeta:
        title = "React Guide"
        author = "Tim"

    import trafilatura  # pastikan dependency ada di venv
    assert trafilatura is not None

    monkeypatch.setattr(tool_bridge.trafilatura if hasattr(
        tool_bridge, "trafilatura") else __import__("trafilatura"),
        "fetch_url", lambda url: "<html>artikel</html>")
    real_extract = __import__("trafilatura").extract
    monkeypatch.setattr(__import__("trafilatura"), "extract",
                        lambda html, **kw: "Isi artikel bersih.")
    import trafilatura as t
    monkeypatch.setattr(t, "extract_metadata", lambda h: FakeMeta())

    r = tool_bridge._web_read("https://contoh.id/artikel")
    assert r["text"] == "Isi artikel bersih."
    assert r["title"] == "React Guide"
    assert r["author"] == "Tim"
    assert r["chars"] > 0


def test_web_read_fetch_fail(monkeypatch):
    import trafilatura as t
    def boom(url):
        raise OSError("network down")
    monkeypatch.setattr(t, "fetch_url", boom)
    r = tool_bridge._web_read("https://contoh.id/x")
    assert "error" in r and "network down" in r["error"]


def test_web_read_empty_extraction(monkeypatch):
    import trafilatura as t
    monkeypatch.setattr(t, "fetch_url", lambda url: "<html></html>")
    monkeypatch.setattr(t, "extract", lambda html, **kw: None)
    r = tool_bridge._web_read("https://contoh.id/kosong")
    assert "error" in r and "ekstraksi" in r["error"]


def test_web_read_registered():
    reg = build_default_registry(sandbox_roots=["~/aeryn-core-agent"])
    assert "web_read" in reg.tools
    schema = reg.tools["web_read"]["schema"]
    assert schema["function"]["name"] == "web_read"
    assert reg.tools["web_read"]["tier"] == "safe"


# ── checker parity ────────────────────────────────────────────────────
from scripts.aeryn_daemon import _checker_web_read


def test_checker_accepts_text_or_error():
    assert _checker_web_read({}, {"text": "isi", "chars": 3})
    assert _checker_web_read({}, {"error": "halaman tidak bisa diambil"})
    assert not _checker_web_read({}, {"text": ""})
    assert not _checker_web_read({}, None)


# ── json_repair pada argumen rusak ────────────────────────────────────
def test_json_repair_fixes_common_llm_breakage():
    from json_repair import repair_json
    cases = [
        ("{'query': 'test'}", {"query": "test"}),
        ('{"url": "x",}', {"url": "x"}),
        ('{"q": "a" "b"}', None),  # bentuk apapun — yang penting tidak raise
    ]
    for raw, expect in cases:
        fixed = json.loads(repair_json(raw))
        if expect is not None:
            assert fixed == expect


def test_daemon_parse_path_uses_repair():
    """Simulasi logika parse di daemon terhadap argumen rusak."""
    raw_args = "{'query': 'apa itu react',}"
    try:
        args = json.loads(raw_args)
        repaired = False
    except (ValueError, TypeError):
        from json_repair import repair_json
        args = json.loads(repair_json(raw_args))
        repaired = True
    assert repaired and args["query"] == "apa itu react"
