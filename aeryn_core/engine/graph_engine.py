#!/usr/bin/env python3
"""GraphEngine — in-memory adjacency graph untuk /v1/engine/graph/* routes.

Murni stdlib (dict + deque). Dibuat V62.16 karena aeryn_core.engine tidak punya
GraphEngine sebelumnya → graph/create 500.
"""

from collections import deque
from typing import Dict, List, Optional


class GraphEngine:
    def __init__(self):
        self._nodes: Dict[str, Dict] = {}
        self._adj: Dict[str, List[str]] = {}

    def add_node(self, node_id: str, label: str = "", node_type: str = "entity") -> None:
        self._nodes[node_id] = {"label": label, "type": node_type}
        self._adj.setdefault(node_id, [])

    def add_edge(self, source: str, target: str, edge_type: str = "related_to") -> None:
        if source not in self._nodes:
            self.add_node(source)
        if target not in self._nodes:
            self.add_node(target)
        if target not in self._adj[source]:
            self._adj[source].append(target)

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return sum(len(v) for v in self._adj.values())

    def bfs(self, start: str, max_depth: int = 3) -> List[str]:
        if start not in self._nodes:
            return []
        visited = {start}
        q: deque = deque([(start, 0)])
        order = []
        while q:
            nid, d = q.popleft()
            order.append(nid)
            if d >= max_depth:
                continue
            for nxt in self._adj.get(nid, []):
                if nxt not in visited:
                    visited.add(nxt)
                    q.append((nxt, d + 1))
        return order

    def dfs(self, start: str, max_depth: int = 3) -> List[str]:
        if start not in self._nodes:
            return []
        visited: set = set()
        order = []

        def _go(nid: str, d: int) -> None:
            if d > max_depth or nid in visited:
                return
            visited.add(nid)
            order.append(nid)
            for nxt in self._adj.get(nid, []):
                _go(nxt, d + 1)

        _go(start, 0)
        return order

    def path(self, source: str, target: str, max_depth: int = 10) -> Optional[List[str]]:
        if source not in self._nodes or target not in self._nodes:
            return None
        q: deque = deque([(source, [source])])
        visited = {source}
        while q:
            nid, p = q.popleft()
            if nid == target:
                return p
            if len(p) > max_depth:
                continue
            for nxt in self._adj.get(nid, []):
                if nxt not in visited:
                    visited.add(nxt)
                    q.append((nxt, p + [nxt]))
        return None

    # Alias untuk engine router (find_path) — V62.16
    find_path = path
