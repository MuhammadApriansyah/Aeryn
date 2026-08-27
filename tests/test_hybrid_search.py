#!/usr/bin/env python3
"""Test for hybrid_search module."""
import sys, os, uuid
sys.path.insert(0, '/home/sen/aeryn-core-agent')

from aeryn_core.hybrid_search import HybridSearchEngine

def test_index_and_search():
    hse = HybridSearchEngine()
    uid = uuid.uuid4().hex[:6]
    hse.index_memory(f"doc_{uid}", "Test Document", f"Hello world {uid}", ["tag1"], "test")
    results = hse.search(f"Hello world {uid}", limit=5)
    assert len(results) >= 1

def test_author_attribution():
    hse = HybridSearchEngine()
    uid = uuid.uuid4().hex[:6]
    hse.index_memory(f"doc_{uid}", "Author Test", f"Content {uid}", [], "sen")
    results = hse.search(f"Content {uid}", limit=5)
    assert any(r.get("author") == "sen" for r in results)

def test_deprecation():
    hse = HybridSearchEngine()
    uid = uuid.uuid4().hex[:6]
    hse.index_memory(f"doc_{uid}", "Dep Test", f"content {uid}", [], "test")
    hse.deprecate_memory(f"doc_{uid}")
    dep = hse.get_deprecated(f"Dep {uid}", limit=5)
    assert isinstance(dep, list)