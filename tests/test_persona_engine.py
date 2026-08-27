#!/usr/bin/env python3
"""Test for persona_engine module."""
import sys, os
sys.path.insert(0, '/home/sen/aeryn-core-agent')

from aeryn_core.persona_engine import PersonaEngine, load_persona

def test_load_persona():
    persona = load_persona()
    assert isinstance(persona, str) and len(persona) > 0

def test_persona_engine():
    pe = PersonaEngine()
    persona = pe.get()
    assert isinstance(persona, str) and len(persona) > 0

def test_caching():
    pe = PersonaEngine()
    p1 = pe.get()
    p2 = pe.get()
    assert p1 == p2