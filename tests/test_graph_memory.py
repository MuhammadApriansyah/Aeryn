#!/usr/bin/env python3
"""Test for graph_memory module."""
import sys, os, uuid
sys.path.insert(0, '/home/sen/aeryn-core-agent')

from aeryn_core.graph_memory import GraphMemory, get_graph_memory

def test_add_node():
    gm = GraphMemory()
    gm.add_memory_node(f"t1_{uuid.uuid4().hex[:4]}", "Test Node", {"tag": "test"})
    stats = gm.get_stats()
    return stats["nodes"] >= 1

def test_add_edge():
    gm = GraphMemory()
    n1, n2 = f"e1_{uuid.uuid4().hex[:4]}", f"e2_{uuid.uuid4().hex[:4]}"
    gm.add_memory_node(n1, "Node 1")
    gm.add_memory_node(n2, "Node 2")
    gm.add_edge(n1, n2, "related_to", 0.5, "test")
    stats = gm.get_stats()
    return stats["edges"] >= 1

def test_neighbors():
    gm = GraphMemory()
    n1 = f"n1_{uuid.uuid4().hex[:4]}"
    gm.add_memory_node(n1, "Node 1")
    neighbors = gm.get_neighbors(n1)
    return isinstance(neighbors, list)

def test_entities():
    gm = GraphMemory()
    eid = f"ent_{uuid.uuid4().hex[:4]}"
    gm.add_entity(eid, "test", "Test Entity")
    return eid in [e for e in dir(gm) if not e.startswith('_')]

if __name__ == "__main__":
    tests = [test_add_node, test_add_edge, test_neighbors, test_entities]
    passed = sum(1 for t in tests if t())
    print(f"graph_memory: {passed}/{len(tests)}")
    sys.exit(0 if passed == len(tests) else 1)
