"""Test V39.12 — CoT rule present + reasoning intact."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.reasoning_style import (
    COGNITIVE_CHAIN_OF_THOUGHT_RULE,
    RESEARCH_FIRST_RULE,
    NEXT_TOKEN_RULE,
    needs_research,
)


def test_cot_rule_exists():
    assert COGNITIVE_CHAIN_OF_THOUGHT_RULE
    assert "COGNITIVE PROTOCOL" in COGNITIVE_CHAIN_OF_THOUGHT_RULE


def test_cot_rule_content():
    rule = COGNITIVE_CHAIN_OF_THOUGHT_RULE
    assert "## PLAN" in rule
    assert "## CRITIC" in rule
    assert "## CONFIDENCE" in rule
    assert "NON-NEGOTIABLE" in rule


def test_cot_not_in_next_token():
    assert "COGNITIVE PROTOCOL" not in NEXT_TOKEN_RULE
    assert "COGNITIVE PROTOCOL" in COGNITIVE_CHAIN_OF_THOUGHT_RULE


def test_needs_research_still_works():
    assert needs_research("berapa harga ETH hari ini") is True
    assert needs_research("ingatkan aku beli kopi") is False


def test_cot_import_from_daemon():
    """Verify daemon can import CoT rule without error."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "scripts"))
    # The daemon imports reasoning_style — if CoT rule exists,
    # daemon will inject it into system prompt
    from scripts.aeryn_daemon import _build_system_prompt
    assert True  # import succeeded
