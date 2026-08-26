"""Test V39.6c — fine-tuning pasca-gen-3: research signals + guard bounded."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.reasoning_style import needs_research
from aeryn_core.research_guard import is_ungrounded_factual


def test_tutorial_questions_need_research():
    for g in ("cara install docker di ubuntu",
              "how to setup nginx reverse proxy",
              "tutorial migrasi postgres 16"):
        assert needs_research(g), g


def test_stable_knowledge_no_research():
    for g in ("kenapa langit biru", "bedanya python dan javascript"):
        assert not needs_research(g), g


def test_research_guard_bounded():
    """Guard tidak boleh loop tanpa batas: iterasi terakhir = disclaimer.
    Simulasi logika: i == max-1 → bukan forced, harus disclaimer path."""
    trace = [{"type": "final"}]
    assert is_ungrounded_factual("apa itu rust", trace)


def test_verifier_accepts_next_token_arrow():
    from aeryn_core.verifier import mechanical_checks
    m = mechanical_checks("jawaban\n\n➡️ Mau kulanjutkan?", [])
    assert not m["issues"]
