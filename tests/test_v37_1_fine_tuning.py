#!/usr/bin/env python3
"""
Test V37.1 — Fine-tuning reliabilitas.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.aeryn_daemon import _is_memory_lookup, _is_memory_write_command


def test_identity_questions_detected():
    """Pertanyaan identitas harus terdeteksi sebagai memory lookup."""
    for q in ("siapa namaku?", "siapa aku", "kamu tahu aku?",
              "kita kenal?", "ingat aku?", "nama aku apa ya?"):
        assert _is_memory_lookup(q), q


def test_non_identity_not_flagged():
    """Pertanyaan biasa tidak boleh terdeteksi sebagai memory lookup."""
    for q in ("apa itu react", "halo", "kamu agy",
              "buatkan file catatan.md", "gimana cara kerja HNSW"):
        assert not _is_memory_lookup(q), q


def test_memory_write_still_priority():
    """'ingat ini' tetap jalur tulis-memori, bukan lookup."""
    assert _is_memory_write_command("ingat ini: proyek X")
    assert not _is_memory_lookup("ingat ini: proyek X")


def test_truncated_run_records_error():
    """Simulasi episode truncated: error eksplisit harus ikut terekam."""
    from aeryn_core.memory.episodic_memory import EpisodicMemory

    mem = EpisodicMemory.__new__(EpisodicMemory)
    mem.path = "/tmp/test_v371_episodes.jsonl"
    if os.path.exists(mem.path):
        os.remove(mem.path)

    mem.record("s_test", "goal rumit", "llm", trace=[],
               answer=None, error="LLM_ERROR: truncated")

    with open(mem.path) as f:
        entry = json.loads(f.readline())

    assert entry["error"] == "LLM_ERROR: truncated"
    os.remove(mem.path)
