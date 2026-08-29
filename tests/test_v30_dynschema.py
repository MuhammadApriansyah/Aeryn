"""Test V30.3 — dynamic schema: enrich description per goal."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aeryn_core.utils.dynamic_schema import (build_dynamic_schemas, relevant_tools,
                                       schema_stats, _goal_paths)

BASE = [
    {"type": "function", "function": {
        "name": "fs_read", "description": "Baca file lokal",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "http_get", "description": "GET URL",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "web_search", "description": "Cari web",
        "parameters": {"type": "object", "properties": {"q": {"type": "string"}}}}},
]


def test_goal_paths_ekstraksi():
    paths = _goal_paths("baca /etc/hostname dan https://example.com/api x")
    assert "/etc/hostname" in paths
    assert "https://example.com/api" in paths


def test_relevant_tools_deteksi_intent():
    assert "fs_read" in relevant_tools("readme file proyek apa isinya")
    assert "web_search" in relevant_tools("cari berita terbaru")
    # tanpa hint kuat → kosong (semua tool dianggap relevan)
    assert relevant_tools("halo dunia") == set()


def test_enrich_fs_read_dengan_path_kandidat():
    out = build_dynamic_schemas(BASE, "baca Cargo.toml versi")
    fs = next(s for s in out
              if s["function"]["name"] == "fs_read")
    desc = fs["function"]["description"]
    assert "Cargo.toml" in desc or "path kandidat" in desc


def test_enrich_http_get_dengan_url():
    out = build_dynamic_schemas(
        BASE, "fetch https://api.example.com/data sekarang")
    hg = next(s for s in out if s["function"]["name"] == "http_get")
    assert "https://api.example.com/data" in hg["function"]["description"]


def test_irrelevan_tool_ditandai():
    out = build_dynamic_schemas(BASE, "cari berita teknologi hari ini")
    ws_desc = next(s for s in out
                   if s["function"]["name"] == "web_search")["function"]["description"]
    fs_desc = next(s for s in out
                   if s["function"]["name"] == "fs_read")["function"]["description"]
    # web_search relevan → tidak ditandai; fs_read ditandai tak relevan
    assert "tidak relevan" not in ws_desc
    assert "tidak relevan" in fs_desc


def test_base_schema_tidak_termutasi():
    original = json_str = str(BASE)
    build_dynamic_schemas(BASE, "baca /etc/hostname pakai file config .json")
    assert str(BASE) == json_str   # deepcopy — registry aman


def test_schema_stats():
    out = build_dynamic_schemas(BASE, "cari harga bitcoin")
    st = schema_stats(out)
    assert st["count"] == 3
    assert st["enriched"] >= 1
