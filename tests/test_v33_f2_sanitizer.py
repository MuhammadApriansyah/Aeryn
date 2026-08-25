"""Test V33-F2 — Sanitizer context-aware.

Natural answers yang kebetulan nyebut 'error/sistem/none' TIDAK boleh
difallback. Output mesin (JSON/tool-call/code block) TETAP difallback.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.aeryn_daemon import _sanitize_social_answer, _looks_machinelike


# ── Natural answers: harus DIPERTAHANKAN (bukan fallback) ────────────
NATURAL_ANSWERS = [
    "Maaf, kemarin sistemku lagi ngambek~",
    "Iya dulu pernah error waktu belajar coding, lucu banget.",
    "Aku none the less selalu ingat kamu kok.",  # kata 'none' dalam kalimat
    "Server Discord-nya sih jalan, tapi aku di sini tetap Aeryn~",
    "Hmm, API-nya emang gitu. Tapi aku tetap aku~",
    "Kadang aku juga kosong ide, hehe.",
]


@pytest.mark.parametrize("a", NATURAL_ANSWERS)
def test_natural_kept(a):
    result = _sanitize_social_answer(a, "kamu gimana")
    # bukan salah satu fallback generik → jawaban asli dipertahankan
    assert result == a.strip(), f"natural dibuang: {a!r} -> {result!r}"


# ── Machine output: HARUS difallback ─────────────────────────────────
MACHINE_OUTPUTS = [
    '{"name": "web_search", "arguments": {"q": "halo"}}',
    '[{"role": "assistant", "content": "..."}]',
    '```python\nprint("halo")\n```',
    'Traceback (most recent call last): File "<stdin>"',
    'ValueError: invalid input detected',
    '{"status": "ok", "data": []}',
]


@pytest.mark.parametrize("a", MACHINE_OUTPUTS)
def test_machine_fallback(a):
    result = _sanitize_social_answer(a, "apa kabar")
    assert result != a.strip(), f"machine output lolos: {a!r}"


def test_looks_machinelike_unit():
    assert _looks_machinelike('```code```') is True
    assert _looks_machinelike('{"name": "x", "arguments": {}}') is True
    assert _looks_machinelike('"key": 1 dan "key2": 2') is True
    assert _looks_machinelike('Halo, aku Aeryn~') is False
