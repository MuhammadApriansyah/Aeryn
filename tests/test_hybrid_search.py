#!/usr/bin/env python3
"""Test for hybrid_search module."""
import sys, os
sys.path.insert(0, '/home/sen/aeryn-core-agent')

from aeryn_core.hybrid_search import HybridSearchEngine, get_search_engine

def test_index_and_search():
    hse = HybridSearchEngine()
    hse.index_memory("doc1", "Test Document", "Hello world content", ["tag1"], "test")
    results = hse.search("hello", limit=5)
    return len(results) >= 1

def test_author_attribution():
    hse = HybridSearchEngine()
    hse.index_memory("doc2", "Author Test", "Content here", [], "sen")
    results = hse.search("content", limit=5)
    return any(r.get("author") == "sen" for r in results)

def test_deprecation():
    hse = HybridSearchEngine()
    hse.index_memory("doc3", "Dep Test", "content", [], "test")
    hse.deprecate_memory("doc3")
    return hse.is_deprecated("doc3")

if __name__ == "__main__":
    tests = [test_index_and_search, test_author_attribution, test_deprecation]
    passed = sum(1 for t in tests if t())
    print(f"hybrid_search: {passed}/{len(tests)}")
    sys.exit(0 if passed == len(tests) else 1)
