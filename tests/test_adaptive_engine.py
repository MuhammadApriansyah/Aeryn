#!/usr/bin/env python3
"""Test Adaptive Rule Engine."""
import sys
sys.path.insert(0, '/home/sen/aeryn-core-agent')

from aeryn_engine import AdaptiveEngine

def test_engine_creation():
    engine = AdaptiveEngine()
    assert engine.rule_count() == 0

def test_add_rule():
    engine = AdaptiveEngine()
    rule = '{"id": "r1", "name": "Test", "enabled": true, "priority": 10, "condition": {"type": "always"}, "action": {"type": "allow"}}'
    engine.add_rule(rule)
    assert engine.rule_count() == 1

def test_evaluate_contains():
    engine = AdaptiveEngine()
    rule = '{"id": "r1", "enabled": true, "priority": 10, "condition": {"type": "contains", "value": "spam"}, "action": {"type": "deny"}}'
    engine.add_rule(rule)
    results = engine.evaluate("buy spam")
    assert len(results) == 1

def test_evaluate_no_match():
    engine = AdaptiveEngine()
    rule = '{"id": "r1", "enabled": true, "priority": 10, "condition": {"type": "contains", "value": "spam"}, "action": {"type": "deny"}}'
    engine.add_rule(rule)
    results = engine.evaluate("hello world")
    assert len(results) == 0

def test_evaluate_threshold():
    engine = AdaptiveEngine()
    rule = '{"id": "r1", "enabled": true, "priority": 10, "condition": {"type": "threshold", "value": 10}, "action": {"type": "log"}}'
    engine.add_rule(rule)
    results = engine.evaluate("short")
    assert len(results) == 0
    results = engine.evaluate("this is a very long message")
    assert len(results) == 1

def test_remove_rule():
    engine = AdaptiveEngine()
    rule = '{"id": "r1", "enabled": true, "priority": 10, "condition": {"type": "always"}, "action": {"type": "allow"}}'
    engine.add_rule(rule)
    assert engine.remove_rule("r1") is True
    assert engine.rule_count() == 0

def test_export_import():
    engine = AdaptiveEngine()
    rule = '{"id": "r1", "enabled": true, "priority": 10, "condition": {"type": "always"}, "action": {"type": "allow"}}'
    engine.add_rule(rule)
    exported = engine.export_rules_to_json()
    assert "r1" in exported
    
    engine2 = AdaptiveEngine()
    count = engine2.load_rules_from_json(exported)
    assert count == 1

def test_priority_sorting():
    engine = AdaptiveEngine()
    r1 = '{"id": "low", "enabled": true, "priority": 1, "condition": {"type": "always"}, "action": {"type": "allow"}}'
    r2 = '{"id": "high", "enabled": true, "priority": 100, "condition": {"type": "always"}, "action": {"type": "deny"}}'
    engine.add_rule(r1)
    engine.add_rule(r2)
    rules = engine.list_rules()
    assert len(rules) == 2
    # Higher priority should be first
    import json
    parsed = [json.loads(r) for r in rules]
    assert parsed[0]["id"] == "high"
    assert parsed[1]["id"] == "low"
