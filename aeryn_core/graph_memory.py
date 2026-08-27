"""V39.48 — Graph Memory Edges (Uteke-style memory relationships).

Implements:
1. Memory-to-memory edges (related_to, supersedes, depends_on, etc.)
2. Entity nodes (people, projects, concepts)
3. Graph traversal for context expansion
4. Auto-linking based on shared tags/content
"""

import os
import sqlite3
import time
from typing import List, Dict, Optional, Set

import sys
sys.path.insert(0, '/home/sen/aeryn-core-agent')

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/graph_memory.db")


class GraphMemory:
    """Graph-based memory relationships."""
    
    EDGE_TYPES = {
        "related_to": "Generic relationship",
        "supersedes": "Replaces/overrides another memory",
        "depends_on": "Requires another memory to be true",
        "contradicts": "Opposes another memory",
        "extends": "Builds upon another memory",
        "causes": "Leads to another memory",
    }
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize graph database."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Memory nodes
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT DEFAULT 'memory',
                    label TEXT,
                    metadata TEXT DEFAULT '{}',
                    created_at REAL
                )
            """)
            
            # Edges between memories
            conn.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT,
                    target_id TEXT,
                    edge_type TEXT,
                    weight REAL DEFAULT 1.0,
                    reason TEXT,
                    created_at REAL,
                    FOREIGN KEY (source_id) REFERENCES nodes(id),
                    FOREIGN KEY (target_id) REFERENCES nodes(id)
                )
            """)
            
            # Entity nodes (people, projects, concepts)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    entity_type TEXT,
                    name TEXT,
                    description TEXT,
                    created_at REAL
                )
            """)
            
            # Memory-Entity relationships
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entities (
                    memory_id TEXT,
                    entity_id TEXT,
                    role TEXT,
                    FOREIGN KEY (memory_id) REFERENCES nodes(id),
                    FOREIGN KEY (entity_id) REFERENCES entities(id)
                )
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def add_memory_node(self, memory_id: str, label: str, metadata: dict = None):
        """Add a memory node to the graph."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO nodes (id, type, label, metadata, created_at)
                VALUES (?, 'memory', ?, ?, ?)
            """, (memory_id, label, str(metadata or {}), time.time()))
            conn.commit()
        finally:
            conn.close()
    
    def add_edge(self, source_id: str, target_id: str, edge_type: str, 
                 weight: float = 1.0, reason: str = ""):
        """Create an edge between two memories."""
        if edge_type not in self.EDGE_TYPES:
            raise ValueError(f"Invalid edge type: {edge_type}")
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO edges (source_id, target_id, edge_type, weight, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (source_id, target_id, edge_type, weight, reason, time.time()))
            conn.commit()
        finally:
            conn.close()
    
    def get_neighbors(self, memory_id: str, edge_type: str = None, 
                      max_depth: int = 1) -> List[Dict]:
        """Get neighboring memories up to N hops away."""
        conn = sqlite3.connect(self.db_path)
        try:
            visited = set()
            frontier = {memory_id}
            results = []
            
            for depth in range(max_depth):
                if not frontier:
                    break
                
                next_frontier = set()
                for node_id in frontier:
                    if node_id in visited:
                        continue
                    visited.add(node_id)
                    
                    # Query edges
                    if edge_type:
                        cursor = conn.execute("""
                            SELECT e.source_id, e.target_id, e.edge_type, e.weight, e.reason,
                                   n.label, n.metadata
                            FROM edges e
                            JOIN nodes n ON (e.target_id = n.id OR e.source_id = n.id)
                            WHERE (e.source_id = ? OR e.target_id = ?) AND e.edge_type = ?
                        """, (node_id, node_id, edge_type))
                    else:
                        cursor = conn.execute("""
                            SELECT e.source_id, e.target_id, e.edge_type, e.weight, e.reason,
                                   n.label, n.metadata
                            FROM edges e
                            JOIN nodes n ON (e.target_id = n.id OR e.source_id = n.id)
                            WHERE e.source_id = ? OR e.target_id = ?
                        """, (node_id, node_id))
                    
                    for row in cursor.fetchall():
                        other_id = row[1] if row[0] == node_id else row[0]
                        if other_id not in visited:
                            next_frontier.add(other_id)
                            results.append({
                                "memory_id": other_id,
                                "label": row[5],
                                "edge_type": row[2],
                                "weight": row[3],
                                "reason": row[4],
                                "depth": depth + 1
                            })
                
                frontier = next_frontier
            
            return results
        finally:
            conn.close()
    
    def find_path(self, source_id: str, target_id: str, max_depth: int = 5) -> List[str]:
        """Find path between two memories using BFS."""
        conn = sqlite3.connect(self.db_path)
        try:
            visited = {source_id}
            queue = [(source_id, [source_id])]
            
            while queue:
                current, path = queue.pop(0)
                
                if len(path) > max_depth:
                    continue
                
                cursor = conn.execute("""
                    SELECT target_id FROM edges WHERE source_id = ?
                    UNION
                    SELECT source_id FROM edges WHERE target_id = ?
                """, (current, current))
                
                for row in cursor.fetchall():
                    neighbor = row[0]
                    if neighbor == target_id:
                        return path + [neighbor]
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
            
            return []
        finally:
            conn.close()
    
    def add_entity(self, entity_id: str, entity_type: str, name: str, 
                   description: str = ""):
        """Add an entity node."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO entities (id, entity_type, name, description, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (entity_id, entity_type, name, description, time.time()))
            conn.commit()
        finally:
            conn.close()
    
    def link_memory_to_entity(self, memory_id: str, entity_id: str, role: str = ""):
        """Link a memory to an entity."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO memory_entities (memory_id, entity_id, role)
                VALUES (?, ?, ?)
            """, (memory_id, entity_id, role))
            conn.commit()
        finally:
            conn.close()
    
    def get_entity_memories(self, entity_id: str) -> List[str]:
        """Get all memories linked to an entity."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT memory_id FROM memory_entities WHERE entity_id = ?",
                (entity_id,)
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def auto_link_related(self, memory_id: str, tags: List[str], content: str):
        """Auto-link memory to existing memories with similar tags/content."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Find memories with shared tags
            tag_placeholders = ",".join("?" * len(tags))
            cursor = conn.execute(f"""
                SELECT id, metadata FROM nodes
                WHERE type = 'memory' AND id != ?
            """, (memory_id,))
            
            for row in cursor.fetchall():
                other_id = row[0]
                other_meta = eval(row[1]) if row[1] else {}
                other_tags = other_meta.get("tags", [])
                
                shared = set(tags) & set(other_tags)
                if shared:
                    weight = len(shared) / max(len(tags), len(other_tags))
                    self.add_edge(memory_id, other_id, "related_to", 
                                  weight, f"Shared tags: {', '.join(shared)}")
        finally:
            conn.close()
    
    def get_stats(self) -> Dict:
        """Get graph statistics."""
        conn = sqlite3.connect(self.db_path)
        try:
            nodes = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            edges = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            return {"nodes": nodes, "edges": edges, "entities": entities}
        finally:
            conn.close()


# Singleton
_graph = None

def get_graph_memory() -> GraphMemory:
    global _graph
    if _graph is None:
        _graph = GraphMemory()
    return _graph
