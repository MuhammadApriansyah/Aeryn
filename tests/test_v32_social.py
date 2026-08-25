"""Test V32 — Social queries: 100% tanpa tool calls, natural response, no JSON.

18 social queries yang HARUS lolos tanpa tool calls, tanpa JSON, tanpa leak.
"""
import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import dari daemon
from scripts.aeryn_daemon import _is_social_query, _sanitize_social_answer, _generate_social_fallback

# ─── 18 Social Queries ────────────────────────────────────────────────
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


# ─── Helper ───────────────────────────────────────────────────────────
def _contains_json(text: str) -> bool:
    """Cek apakah teks mengandung JSON valid."""
    if not text or not isinstance(text, str):
        return False
    stripped = text.strip()
    if stripped.startswith(("{", "[")):
        try:
            json.loads(stripped)
            return True
        except (ValueError, json.JSONDecodeError):
            pass
    return False


def _contains_tool_call(text: str) -> bool:
    """Cek apakah teks mengandung tool call / tool names."""
    if not text or not isinstance(text, str):
        return False
    tool_names = ['web_search', 'fs_read', 'terminal', 'http_get', 'web_fetch',
                  'tool_call', 'tool_calls', 'execute_function']
    for tool in tool_names:
        if re.search(r'\b' + re.escape(tool) + r'\b', text, re.IGNORECASE):
            return True
    # Cek format tool call JSON
    if re.search(r'\{[^{}]*"name"\s*:\s*"[^"]+"[^{}]*"arguments"', text):
        return True
    return False


def _contains_internal_leak(text: str) -> bool:
    """Cek apakah teks mengandung internal info leak."""
    if not text or not isinstance(text, str):
        return False
    internal_kw = ['error', 'exception', 'API', 'database', 'server',
                   'backend', 'sistem', 'traceback', 'stack trace',
                   'null', 'undefined', 'kosong']
    for kw in internal_kw:
        if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
            return True
    return False


# ─── Test Group 1: _is_social_query detection ─────────────────────────
@pytest.mark.parametrize("query", SOCIAL_QUERIES)
def test_is_social_query_detected(query):
    """Semua social queries terdeteksi sebagai social."""
    assert _is_social_query(query), f"Gagal deteksi social: {query}"


# ─── Test Group 2: _sanitize_social_answer ─────────────────────────────
def test_sanitize_valid_natural_answer():
    """Jawaban natural → tetap dipertahankan."""
    answer = "Aku Aeryn. Salam kenal!"
    result = _sanitize_social_answer(answer, "kamu siapa")
    assert result == "Aku Aeryn. Salam kenal!"


def test_sanitize_json_answer():
    """Jawaban JSON → fallback."""
    answer = '{"tool_calls": [{"name": "web_search"}]}'
    result = _sanitize_social_answer(answer, "halo")
    assert not _contains_json(result)
    assert not _contains_tool_call(result)
    assert isinstance(result, str) and len(result) > 0


def test_sanitize_tool_name_leak():
    """Jabaran dengan tool name → fallback."""
    answer = "Saya akan pakai web_search untuk cari."
    result = _sanitize_social_answer(answer, "halo")
    assert not _contains_tool_call(result)
    assert isinstance(result, str) and len(result) > 0


def test_sanitize_internal_leak():
    """Jawaban dengan internal keyword → fallback."""
    answer = "Error: tidak bisa connect ke database."
    result = _sanitize_social_answer(answer, "apa kabar")
    assert not _contains_internal_leak(result)
    assert isinstance(result, str) and len(result) > 0


def test_sanitize_empty_answer():
    """Jawaban kosong → fallback."""
    result = _sanitize_social_answer("", "halo")
    assert isinstance(result, str) and len(result) > 0


def test_sanitize_none_answer():
    """Jawaban None → fallback."""
    result = _sanitize_social_answer(None, "halo")
    assert isinstance(result, str) and len(result) > 0


def test_sanitize_short_after_cleaning():
    """Terlalu pendek setelah cleaning → fallback."""
    answer = "{}"
    result = _sanitize_social_answer(answer, "halo")
    assert isinstance(result, str) and len(result) > 0


def test_sanitize_tool_call_json_inline():
    """JSON inline tool call → fallback."""
    answer = 'Saya pakai {"name": "fs_read", "arguments": {"path": "/tmp"}}'
    result = _sanitize_social_answer(answer, "halo")
    assert not _contains_tool_call(result)
    assert isinstance(result, str) and len(result) > 0


def test_sanitize_multi_tool_leak():
    """Multiple tool names → fallback."""
    answer = "web_search dan terminal dan fs_read"
    result = _sanitize_social_answer(answer, "apa kabar")
    assert not _contains_tool_call(result)


def test_sanitize_array_tool_calls():
    """Array of tool calls → fallback."""
    answer = '[{"tool_calls": [{"name": "web_search"}]}]'
    result = _sanitize_social_answer(answer, "halo")
    assert not _contains_tool_call(result)
    assert not _contains_json(result)


# ─── Test Group 3: _generate_social_fallback ───────────────────────────
def test_fallback_greeting():
    """Fallback untuk sapaan → greeting natural."""
    result = _generate_social_fallback("halo")
    assert isinstance(result, str) and len(result) > 0
    assert not _contains_json(result)
    assert not _contains_tool_call(result)


def test_fallback_kabar():
    """Fallback untuk tanya kabar → response natural."""
    result = _generate_social_fallback("apa kabar")
    assert isinstance(result, str) and len(result) > 0
    assert not _contains_json(result)
    assert not _contains_tool_call(result)


def test_fallback_kamu_siapa():
    """Fallback untuk 'kamu siapa' → identity natural."""
    result = _generate_social_fallback("kamu siapa")
    assert isinstance(result, str) and len(result) > 0
    assert not _contains_json(result)
    assert not _contains_tool_call(result)


def test_fallback_Generic():
    """Fallback generic → response natural."""
    result = _generate_social_fallback("ngomong")
    assert isinstance(result, str) and len(result) > 0
    assert not _contains_json(result)
    assert not _contains_tool_call(result)


def test_fallback_panggil():
    """Fallback untuk panggil nama → natural."""
    result = _generate_social_fallback("panggil nama aku")
    assert isinstance(result, str) and len(result) > 0
    assert not _contains_json(result)
    assert not _contains_tool_call(result)


def test_fallback_ingat():
    """Fallback untuk ingat → natural."""
    result = _generate_social_fallback("kamu ingat aku")
    assert isinstance(result, str) and len(result) > 0
    assert not _contains_json(result)
    assert not _contains_tool_call(result)


# ─── Test Group 4: Full pipeline simulation ────────────────────────────
@pytest.mark.parametrize("query", SOCIAL_QUERIES)
def test_full_pipeline_no_tool_calls(query):
    """Simulasi pipeline: social query → sanitize → natural response."""
    # Simulasi jawaban model yang bermasalah
    bad_answers = [
        '{"tool_calls": [{"name": "web_search"}]}',
        'Error: server down',
        '',
        'null',
        '{"name": "fs_read"}',
    ]
    for bad_answer in bad_answers:
        result = _sanitize_social_answer(bad_answer, query)
        assert not _contains_json(result), f"JSON leak for '{query}' with answer '{bad_answer}'"
        assert not _contains_tool_call(result), f"Tool call leak for '{query}'"
        assert not _contains_internal_leak(result), f"Internal leak for '{query}'"
        assert isinstance(result, str) and len(result) > 0, f"Empty result for '{query}'"


def test_pipeline_realistic_answers():
    """Test dengan jawaban realistis yang mungkin dari model."""
    test_cases = [
        ("halo", "Eh, halo! Udah makan belum?"),
        ("kamu siapa", "Aku Aeryn. Salam kenal!"),
        ("apa kabar", "Baik, terima kasih! Kamu gimana?"),
    ]
    for query, good_answer in test_cases:
        result = _sanitize_social_answer(good_answer, query)
        assert result == good_answer, f"Valid answer berubah untuk '{query}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])