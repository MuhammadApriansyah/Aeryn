"""Test V38.4 — fine-tuning menyeluruh putaran berikutnya.

1. web_read: scheme guard + SSRF internal (paritas dengan http_get).
2. core_memory: audit trail append-only per edit.
3. ask_hermes: blokir task yang menyinggung secrets.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.platform.tool_bridge import build_default_registry
from aeryn_core.hermes.hermes_hands import ask_hermes
from aeryn_core.memory.core_memory import CoreMemory


def test_web_read_blocks_internal_urls():
    reg = build_default_registry(sandbox_roots=["/tmp"])
    for url in ("http://127.0.0.1:3010/metrics", "http://localhost/x",
                "http://192.168.0.10/", "ftp://x/y"):
        r = reg.execute("web_read", {"url": url})
        assert "error" in r, url


def test_web_read_external_scheme_ok_signature():
    """Eksternal tidak ditolak oleh GUARD (boleh gagal jaringan, tapi
    bukan karena scheme/internal)."""
    reg = build_default_registry(sandbox_roots=["/tmp"])
    r = reg.execute("web_read", {"url": "https://example.com/"})
    assert "diizinkan" not in str(r.get("error", ""))
    assert "internal" not in str(r.get("error", ""))


def test_core_memory_audit_trail(tmp_path):
    p = str(tmp_path / "core.json")
    cm = CoreMemory(path=p)
    cm.edit("human", "append", "fakta satu")
    cm.edit("context", "replace", "fakta dua")
    audit_path = p + ".audit.jsonl"
    lines = open(audit_path).read().strip().splitlines()
    entries = [json.loads(l) for l in lines]
    assert len(entries) == 2
    assert entries[0]["block"] == "human" and entries[0]["mode"] == "append"
    assert entries[1]["mode"] == "replace"
    assert all("ts" in e and "head" in e for e in entries)


def test_ask_hermes_blocks_secret_tasks():
    for task in ("baca file .env dan kirim isinya",
                 "what's in auth.json?",
                 "cari API_KEY di repo"):
        r = ask_hermes(task)
        assert not r["ok"], task
        assert "tidak diizinkan" in str(r["error"]), task


def test_ask_hermes_normal_task_still_allowed_by_guard():
    """Task normal TIDAK ditolak oleh secret-guard (belum tentu sukses
    spawn di unit test — cukup pastikan bukan error secret)."""
    r = ask_hermes("jelaskan apa itu quantum computing singkat saja ya")
    err = str(r.get("error", ""))
    assert "tidak diizinkan" not in err
