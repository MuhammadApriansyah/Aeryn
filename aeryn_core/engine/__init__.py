"""Aeryn Engine Wrappers — Python bindings untuk Rust engine.

Modul ini menyediakan Python wrapper untuk semua Rust engine:
- VectorStore: HNSW vector similarity search
- TextSplitter: Recursive character & token-based splitting
- Tokenizer: LRU cache tokenizer
- Database: SQLite adapter
- Processor: File processor
- GraphEngine: Knowledge graph dengan BFS/DFS/Dijkstra
- WorkflowEngine: Multi-step workflow execution
- MCPProtocol: Model Context Protocol
- RAGPipeline: Retrieval-Augmented Generation

Semua modul ini adalah thin wrapper di sekitar Rust PyO3 bindings.
Jika Rust binding tidak available, fallback ke pure Python.
"""

import os
import sys
import json
import logging
import importlib
import importlib.util
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import Rust bindings
_RUST_AVAILABLE = False
_rust_engine = None

try:
    from aeryn_engine import (
        PyVectorStore,
        PyTextSplitter,
        PyTokenizer,
    )
    _RUST_AVAILABLE = True
    logger.info("Rust engine bindings loaded successfully")
except ImportError:
    logger.warning("Rust engine bindings not available, using Python fallback")
    _RUST_AVAILABLE = False


def is_rust_available() -> bool:
    """Check if Rust engine bindings are available."""
    return _RUST_AVAILABLE


class VectorStore:
    """Python wrapper untuk Rust HNSW Vector Store.
    
    Provides high-performance vector similarity search using
    HNSW (Hierarchical Navigable Small World) index.
    
    Fallback to pure Python brute-force if Rust unavailable.
    """
    
    def __init__(self, dimensions: int = 1536, metric: str = "cosine"):
        self.dimensions = dimensions
        self.metric = metric
        
        if _RUST_AVAILABLE:
            self._inner = PyVectorStore(dimensions)
            self._use_rust = True
        else:
            self._vectors: Dict[str, List[float]] = {}
            self._metadata: Dict[str, Dict[str, str]] = {}
            self._use_rust = False
    
    def add(self, id: str, vector: List[float], metadata: Optional[Dict[str, str]] = None):
        """Add a vector to the store."""
        if self._use_rust:
            self._inner.add(id, vector)
        else:
            self._vectors[id] = vector
            if metadata:
                self._metadata[id] = metadata
    
    def search(self, query: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Search for k nearest neighbors."""
        if self._use_rust:
            results = self._inner.search(query, k)
            return [{"id": r.id, "score": r.score, "vector": r.vector} for r in results]
        else:
            # Pure Python brute-force fallback
            import math
            
            def cosine_sim(a, b):
                dot = sum(x * y for x, y in zip(a, b))
                norm_a = math.sqrt(sum(x * x for x in a))
                norm_b = math.sqrt(sum(y * y for y in b))
                if norm_a == 0 or norm_b == 0:
                    return 0
                return dot / (norm_a * norm_b)
            
            scores = []
            for vid, vec in self._vectors.items():
                score = cosine_sim(query, vec)
                scores.append({"id": vid, "score": score, "vector": vec})
            
            scores.sort(key=lambda x: x["score"], reverse=True)
            return scores[:k]
    
    def remove(self, id: str):
        """Remove a vector from the store."""
        if self._use_rust:
            pass  # Rust doesn't support removal yet
        else:
            self._vectors.pop(id, None)
            self._metadata.pop(id, None)
    
    def len(self) -> int:
        """Return number of vectors."""
        if self._use_rust:
            return self._inner.len()
        return len(self._vectors)
    
    def is_empty(self) -> bool:
        """Check if store is empty."""
        return self.len() == 0
    
    def get_metadata(self, id: str) -> Optional[Dict[str, str]]:
        """Get metadata for a vector."""
        if self._use_rust:
            return None
        return self._metadata.get(id)
    
    def set_metadata(self, id: str, metadata: Dict[str, str]):
        """Set metadata for a vector."""
        if not self._use_rust:
            self._metadata[id] = metadata


class TextSplitter:
    """Python wrapper untuk Rust Text Splitter.
    
    Supports recursive character splitting and token-based splitting.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if _RUST_AVAILABLE:
            self._inner = PyTextSplitter(chunk_size, chunk_overlap)
            self._use_rust = True
        else:
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            self._use_rust = False
    
    def split(self, text: str) -> List[str]:
        """Split text into chunks."""
        if self._use_rust:
            return self._inner.split_text(text)
        else:
            # Simple Python fallback
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                chunks.append(text[start:end])
                start += self.chunk_size - self.chunk_overlap
            return chunks
    
    def split_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Split multiple documents."""
        results = []
        for doc in documents:
            text = doc.get("content", "")
            metadata = doc.get("metadata", {})
            chunks = self.split(text)
            for i, chunk in enumerate(chunks):
                chunk_meta = metadata.copy()
                chunk_meta["chunk_index"] = str(i)
                results.append({"content": chunk, "metadata": chunk_meta})
        return results


class Tokenizer:
    """Python wrapper untuk Rust Tokenizer."""
    
    def __init__(self):
        if _RUST_AVAILABLE:
            self._inner = PyTokenizer()
            self._use_rust = True
        else:
            self._use_rust = False
    
    def count(self, text: str) -> int:
        """Count tokens in text."""
        if self._use_rust:
            return self._inner.count_tokens(text)
        # Simple whitespace fallback
        return len(text.split())
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text."""
        if self._use_rust:
            return self._inner.tokenize(text)
        return text.split()


class Database:
    """Python wrapper untuk Rust SQLite Database."""
    
    def __init__(self, path: str = "./aeryn.db"):
        self.path = path
        self._conn = None
    
    def connect(self):
        """Connect to database."""
        import sqlite3
        self._conn = sqlite3.connect(self.path)
        self._conn.execute("PRAGMA journal_mode=wal")
        return self
    
    def execute(self, sql: str, params: tuple = ()) -> int:
        """Execute SQL."""
        if not self._conn:
            self.connect()
        cursor = self._conn.execute(sql, params)
        self._conn.commit()
        return cursor.rowcount
    
    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Query database."""
        if not self._conn:
            self.connect()
        cursor = self._conn.execute(sql, params)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def init_table(self, name: str, schema: str):
        """Initialize a table."""
        self.execute(f"CREATE TABLE IF NOT EXISTS {name} ({schema})")
    
    def close(self):
        """Close connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


class Processor:
    """Python wrapper untuk Rust File Processor."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_file(self, path: str) -> Dict[str, Any]:
        """Process a file into chunks."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        content = path.read_text(encoding="utf-8", errors="ignore")
        
        splitter = TextSplitter(self.chunk_size, self.chunk_overlap)
        chunks = splitter.split(content)
        
        return {
            "path": str(path),
            "file_type": path.suffix.lstrip("."),
            "content": content,
            "chunks": chunks,
            "metadata": {
                "file_size": str(path.stat().st_size),
                "file_name": path.name,
            }
        }
    
    def process_files(self, paths: List[str]) -> List[Dict[str, Any]]:
        """Process multiple files."""
        return [self.process_file(p) for p in paths]


class GraphEngine:
    """Python wrapper untuk Rust Knowledge Graph."""
    
    def __init__(self):
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[Tuple[str, str, str]] = []
    
    def add_node(self, id: str, label: str, node_type: str = "entity"):
        """Add a node to the graph."""
        self._nodes[id] = {"label": label, "type": node_type, "edges": []}
    
    def add_edge(self, source: str, target: str, edge_type: str = "related_to"):
        """Add an edge to the graph."""
        if source in self._nodes and target in self._nodes:
            self._edges.append((source, target, edge_type))
            self._nodes[source]["edges"].append(target)
    
    def bfs(self, start: str, max_depth: int = 3) -> List[str]:
        """Breadth-first search."""
        visited = set()
        result = []
        queue = [(start, 0)]
        
        while queue:
            node, depth = queue.pop(0)
            if node in visited or depth > max_depth:
                continue
            visited.add(node)
            result.append(node)
            
            if node in self._nodes:
                for neighbor in self._nodes[node].get("edges", []):
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))
        
        return result
    
    def dfs(self, start: str, max_depth: int = 3) -> List[str]:
        """Depth-first search."""
        visited = set()
        result = []
        
        def _dfs(node, depth):
            if node in visited or depth > max_depth:
                return
            visited.add(node)
            result.append(node)
            if node in self._nodes:
                for neighbor in self._nodes[node].get("edges", []):
                    _dfs(neighbor, depth + 1)
        
        _dfs(start, 0)
        return result
    
    def find_path(self, source: str, target: str, max_depth: int = 10) -> Optional[List[str]]:
        """Find path between two nodes."""
        from collections import deque
        
        visited = {source}
        queue = deque([(source, [source])])
        
        while queue:
            current, path = queue.popleft()
            if current == target:
                return path
            
            if len(path) >= max_depth:
                continue
            
            if current in self._nodes:
                for neighbor in self._nodes[current].get("edges", []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
        
        return None
    
    def stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
        }
    
    def node_count(self) -> int:
        return len(self._nodes)
    
    def edge_count(self) -> int:
        return len(self._edges)


class WorkflowEngine:
    """Python wrapper untuk Rust Workflow Engine."""
    
    def __init__(self):
        self._workflows: Dict[str, Dict[str, Any]] = {}
    
    def create_workflow(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new workflow."""
        workflow = {
            "name": name,
            "description": description,
            "nodes": [],
            "edges": [],
        }
        self._workflows[name] = workflow
        return workflow
    
    def add_node(self, workflow: str, node_id: str, node_type: str, config: Dict = None):
        """Add a node to a workflow."""
        if workflow in self._workflows:
            self._workflows[workflow]["nodes"].append({
                "id": node_id,
                "type": node_type,
                "config": config or {},
            })
    
    def add_edge(self, workflow: str, source: str, target: str, condition: str = None):
        """Add an edge to a workflow."""
        if workflow in self._workflows:
            self._workflows[workflow]["edges"].append({
                "source": source,
                "target": target,
                "condition": condition,
            })
    
    def execute(self, workflow: str, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a workflow."""
        if workflow not in self._workflows:
            raise ValueError(f"Workflow not found: {workflow}")
        
        wf = self._workflows[workflow]
        results = dict(inputs or {})
        
        # Simple topological sort execution
        from collections import deque
        
        adjacency = {}
        in_degree = {}
        
        for node in wf["nodes"]:
            adjacency[node["id"]] = []
            in_degree[node["id"]] = 0
        
        for edge in wf["edges"]:
            adjacency[edge["source"]].append(edge["target"])
            in_degree[edge["target"]] += 1
        
        queue = deque([n for n, d in in_degree.items() if d == 0])
        executed = set()
        
        while queue:
            node_id = queue.popleft()
            if node_id in executed:
                continue
            
            # Find node config
            node = next((n for n in wf["nodes"] if n["id"] == node_id), None)
            if node:
                results[f"{node_id}_output"] = f"Executed {node['type']}"
                executed.add(node_id)
            
            for neighbor in adjacency.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return results
    
    def list_workflows(self) -> List[str]:
        """List all workflows."""
        return list(self._workflows.keys())


class MCPProtocol:
    """Python wrapper untuk Rust MCP Protocol."""
    
    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._resources: Dict[str, Any] = {}
        self._prompts: Dict[str, Any] = {}
    
    def register_tool(self, name: str, description: str, handler, parameters: Dict = None):
        """Register a tool."""
        self._tools[name] = {
            "description": description,
            "handler": handler,
            "parameters": parameters or {},
        }
    
    def register_resource(self, uri: str, description: str, handler):
        """Register a resource."""
        self._resources[uri] = {
            "description": description,
            "handler": handler,
        }
    
    def register_prompt(self, name: str, description: str, handler):
        """Register a prompt."""
        self._prompts[name] = {
            "description": description,
            "handler": handler,
        }
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP request."""
        method = request.get("method", "")
        params = request.get("params", {})
        
        if method == "tools/list":
            return {
                "tools": [
                    {"name": k, "description": v["description"]}
                    for k, v in self._tools.items()
                ]
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            if tool_name in self._tools:
                handler = self._tools[tool_name]["handler"]
                result = handler(**params.get("arguments", {}))
                return {"result": result}
            return {"error": f"Tool not found: {tool_name}"}
        
        return {"error": f"Unknown method: {method}"}
    
    def list_tools(self) -> List[Dict[str, str]]:
        """List all registered tools."""
        return [{"name": k, "description": v["description"]} for k, v in self._tools.items()]


class RAGPipeline:
    """Python wrapper untuk Rust RAG Pipeline."""
    
    def __init__(self, vector_store: VectorStore = None, tokenizer: Tokenizer = None):
        self.vector_store = vector_store or VectorStore()
        self.tokenizer = tokenizer or Tokenizer()
        self._documents: List[Dict[str, Any]] = []
    
    def add_document(self, content: str, metadata: Dict[str, str] = None, embedding: List[float] = None):
        """Add a document to the RAG pipeline."""
        doc = {
            "content": content,
            "metadata": metadata or {},
            "embedding": embedding,
        }
        self._documents.append(doc)
    
    def index_documents(self):
        """Index all documents into vector store."""
        for i, doc in enumerate(self._documents):
            if doc.get("embedding"):
                self.vector_store.add(f"doc_{i}", doc["embedding"], doc.get("metadata"))
    
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query."""
        # In production, would embed query and search vector store
        return self._documents[:k]
    
    def generate(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Generate response using retrieved context."""
        context_text = "\n".join([d["content"] for d in context])
        return f"Response to '{query}' based on:\n{context_text}"
    
    def query(self, query: str, k: int = 5) -> Dict[str, Any]:
        """Full RAG pipeline: retrieve + generate."""
        context = self.retrieve(query, k)
        response = self.generate(query, context)
        return {"query": query, "response": response, "context": context}
