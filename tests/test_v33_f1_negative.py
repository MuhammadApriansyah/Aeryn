"""Test V33-F1 — Negative cases: pertanyaan TEKNIS/KNOWLEDGE tidak boleh
masuk jalur sosial. Plus regression 18 query sosial lama tetap terdeteksi.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.aeryn_daemon import _is_social_query as daemon_is_social
from scripts.social_generator import _is_social_query as gen_is_social

# ── HARUS BUKAN SOSIAL (knowledge/task → tool path) ──────────────────
TECHNICAL_QUERIES = [
    "apa itu react?",
    "kamu pake library apa buat embedding?",
    "gimana cara kerja HNSW?",
    "apa bedanya sqlite dan postgres",
    "kenapa gateway error terus",
    "kok error pas npm install",
    "cara bikin API endpoint di fastify",
    "bagaimana cara deploy ke proot",
    "jelaskan cara kerja heuristic detection",
    "regex buat split chapter gimana",
    "bedanya fs_read dan terminal apa",
    "bantu debug parser epub dong",
    "cari tutorial docker untuk pemula",
    "config pm2 yang bener kayak gimana",
]


@pytest.mark.parametrize("q", TECHNICAL_QUERIES)
def test_technical_not_social_daemon(q):
    assert daemon_is_social(q) is False, f"salah deteksi sosial: {q!r}"


@pytest.mark.parametrize("q", TECHNICAL_QUERIES)
def test_technical_not_social_generator(q):
    assert gen_is_social(q) is False, f"salah deteksi sosial: {q!r}"


# ── REGRESSION: 18 query sosial lama TETAP sosial ────────────────────
SOCIAL_QUERIES = [
    "halo agy chan",
    "kan kamu agy",
    "halo",
    "hai",
    "hi",
    "hey",
    "helo",
    "hello",
    "apa kabar",
    "gimana kabar",
    "gmn kabar",
    "kamu siapa",
    "kamu agy",
    "kamu aeryn",
    "panggil nama aku",
    "siapa aku",
    "kamu tau siapa aku",
    "kamu ingat aku",
]


@pytest.mark.parametrize("q", SOCIAL_QUERIES)
def test_social_still_detected_daemon(q):
    assert daemon_is_social(q) is True, f"sosial gak ke-deteksi: {q!r}"


@pytest.mark.parametrize("q", SOCIAL_QUERIES)
def test_social_still_detected_generator(q):
    # pengecualian generator: "kamu aeryn"/"kamu agy" match KNOWN_RESPONSES
    # lewat deterministic path, tapi _is_social_query harus True juga
    assert gen_is_social(q) is True, f"sosial gak ke-deteksi: {q!r}"
