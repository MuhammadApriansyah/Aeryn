"""Test V37.1 — fine-tuning reliabilitas.

1. Run yang habis iterasi TANPA jawaban kini tercatat sebagai error
   eksplisit (tidak lagi gagal diam-diam).
2. Pertanyaan identitas ("siapa namaku?") masuk jalur memori — tools
   di-strip, tidak ada fs_read/terminal.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from scripts.aeryn_daemon import _is_memory_lookup  # FIXME: not yet implemented


def test_identity_questions_detected():
    for q in ("siapa namaku?", "siapa aku", "kamu tahu aku?",
              "kita kenal?", "ingat aku?", "nama aku apa ya?"):
        assert _is_memory_lookup(q), q


def test_non_identity_not_flagged():
    for q in ("apa itu react", "halo", "kamu agy",
              "buatkan file catatan.md", "gimana cara kerja HNSW"):
        assert not _is_memory_lookup(q), q


def test_memory_write_still_priority():
    """'ingat ini' tetap jalur tulis-memori, bukan lookup."""
    from scripts.aeryn_daemon import _is_memory_write_command
    assert _is_memory_write_command("ingat ini: proyek X")
    assert not _is_memory_lookup("ingat ini: proyek X")


def test_truncated_run_records_error():
    """Simulasi episode truncated: error eksplisit harus ikut terekam."""
    import importlib
    from aeryn_core.memory.episodic_memory import EpisodicMemory

    mem = EpisodicMemory.__new__(EpisodicMemory)  # tanpa init file asli
    mem.path = "/tmp/test_v371_episodes.jsonl"
    if os.path.exists(mem.path):
        os.remove(mem.path)

    # tiru perilaku baru: truncated + pesan error eksplisit
    mem.record("s_test", "goal rumit", "llm", trace=[],
               answer=None,
               error="iterasi habis tanpa jawaban final "
                     "(goal terlalu kompleks atau model berputar)")
    ep = json.loads(open(mem.path).readline())
    assert ep["ok"] is False
    assert "iterasi habis" in ep["error"]
