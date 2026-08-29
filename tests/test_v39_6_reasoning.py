"""Test V39.6 — research-first + next-token prediction style."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.reasoning.reasoning_style import (
    NEXT_TOKEN_RULE, RESEARCH_FIRST_RULE, build_next_token_hint,
    needs_research)


def test_factual_question_needs_research():
    assert needs_research("apa itu react dan gimana cara pakainya")
    assert needs_research("versi terakhir fastify berapa")


def test_local_intent_no_research():
    for g in ("ingatkan aku minum", "namaku siapa?", "hitung 2+2",
              "jam berapa sekarang", "ingat ini: sen suka kopi"):
        assert not needs_research(g), g


def test_empty_goal():
    assert not needs_research("")
    assert not needs_research(None)


def test_rules_content():
    assert "RISET DULU" in RESEARCH_FIRST_RULE
    assert "JANGAN menebak" in RESEARCH_FIRST_RULE
    assert "➡️" in NEXT_TOKEN_RULE


def test_hint_fallback():
    h = build_next_token_hint()
    assert h.startswith("➡️")
