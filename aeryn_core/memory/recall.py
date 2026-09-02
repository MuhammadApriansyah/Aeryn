"""Memory Recall — retrieve relevant memories before LLM call."""

import os
import json
import sqlite3
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from aeryn_core.utils.config import DATABASE_DIR, VAULT_DIR


class MemoryRecall:
    """Retrieve relevant memories from all memory stores."""
    
    def __init__(self):
        self.vault_dir = VAULT_DIR
        self.db_path = os.path.join(DATABASE_DIR, "memories.db")
        self._init_db()
    
    def _init_db(self):
        """Initialize memory database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                source TEXT DEFAULT 'vault',
                relevance_score REAL DEFAULT 0.0,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source)")
        conn.commit()
        conn.close()
    
    def search_vault(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search vault files by content."""
        results = []
        if not os.path.exists(self.vault_dir):
            return results
        
        # Extract keywords from query
        keywords = re.findall(r'\b\w+\b', query.lower())
        if not keywords:
            return results
        
        for root, dirs, files in os.walk(self.vault_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__')]
            
            for filename in files:
                if not filename.endswith(('.md', '.txt', '.json')):
                    continue
                
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    
                    # Simple relevance scoring
                    score = sum(1 for kw in keywords if kw in content.lower())
                    if score > 0:
                        results.append({
                            "content": content[:500],
                            "path": filepath,
                            "source": "vault",
                            "score": score,
                        })
                except:
                    continue
        
        # Sort by relevance
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def search_semantic(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search semantic memory."""
        try:
            from aeryn_core.memory.semantic_recall import SemanticRecall
            recall = SemanticRecall()
            return recall.search(query, limit)
        except:
            return []
    
    def search_graph(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search graph memory."""
        try:
            from aeryn_core.memory.graph_memory import GraphMemory
            graph = GraphMemory()
            nodes = graph.search_nodes(query, limit)
            return [{"content": str(n), "source": "graph", "score": 1.0} for n in nodes]
        except:
            return []
    
    def search_episodic(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search episodic memory."""
        try:
            from aeryn_core.memory.episodic_memory import EpisodicMemory
            memory = EpisodicMemory()
            results = memory.recall(query, limit)
            return [{"content": str(r), "source": "episodic", "score": 1.0} for r in results]
        except:
            return []
    
    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recall relevant memories from all sources."""
        all_results = []
        
        # Search all memory sources
        all_results.extend(self.search_vault(query, limit))
        all_results.extend(self.search_semantic(query, limit))
        all_results.extend(self.search_graph(query, limit))
        all_results.extend(self.search_episodic(query, limit))
        
        # Deduplicate by content hash
        seen = set()
        unique = []
        for r in all_results:
            content_hash = hash(r.get("content", "")[:100])
            if content_hash not in seen:
                seen.add(content_hash)
                unique.append(r)
        
        # Sort by score and return top results
        unique.sort(key=lambda x: x.get("score", 0), reverse=True)
        return unique[:limit]
    
    def format_for_prompt(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories for system prompt injection."""
        if not memories:
            return ""
        
        lines = ["## Relevant Memories:"]
        for i, mem in enumerate(memories, 1):
            source = mem.get("source", "unknown")
            content = mem.get("content", "")[:200]
            lines.append(f"{i}. [{source}] {content}")
        
        return "\n".join(lines)


# Global instance
_recall = None

def get_memory_recall() -> MemoryRecall:
    """Get global memory recall instance."""
    global _recall
    if _recall is None:
        _recall = MemoryRecall()
    return _recall
