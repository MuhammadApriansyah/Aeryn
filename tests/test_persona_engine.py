#!/usr/bin/env python3
"""Test for persona_engine module."""
import sys, os
sys.path.insert(0, '/home/sen/aeryn-core-agent')

from aeryn_core.persona_engine import PersonaEngine, load_persona

def test_load_persona():
    persona = load_persona()
    return isinstance(persona, str) and len(persona) > 0

def test_persona_engine():
    pe = PersonaEngine()
    persona = pe.get()
    return isinstance(persona, str) and len(persona) > 0

def test_caching():
    pe = PersonaEngine()
    p1 = pe.get()
    p2 = pe.get()
    return p1 == p2

if __name__ == "__main__":
    tests = [test_load_persona, test_persona_engine, test_caching]
    passed = sum(1 for t in tests if t())
    print(f"persona_engine: {passed}/{len(tests)}")
    sys.exit(0 if passed == len(tests) else 1)
