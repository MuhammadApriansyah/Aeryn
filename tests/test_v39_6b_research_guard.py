"""Test V39.6b — research guard enforcement."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.research_guard import (
    FORCED_RESEARCH_DIRECTIVE, UNGROUNDED_DISCLAIMER,
    is_ungrounded_factual, used_research_tools)


def test_factual_no_research_is_ungrounded():
    trace = [{"type": "tool", "name": "fs_read"}]
    assert is_ungrounded_factual("apa itu react?", trace)


def test_with_research_not_ungrounded():
    trace = [{"type": "tool", "name": "web_search"},
             {"type": "tool", "name": "web_read"}]
    assert not is_ungrounded_factual("apa itu react?", trace)


def test_local_intent_never_ungrounded():
    assert not is_ungrounded_factual("hitung 2+2", [])
    assert not is_ungrounded_factual("ingatkan aku minum", [])


def test_directive_mentions_riset():
    assert "web_search" in FORCED_RESEARCH_DIRECTIVE
    assert "DILARANG" in FORCED_RESEARCH_DIRECTIVE


def test_disclaimer_honest():
    assert "belum kucek" in UNGROUNDED_DISCLAIMER
