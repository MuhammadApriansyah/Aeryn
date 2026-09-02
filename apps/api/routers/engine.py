from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/v1/engine", tags=["engine"])

# In-memory stores
_vector_stores: Dict[str, Any] = {}
_graphs: Dict[str, Any] = {}


class VectorInsertRequest(BaseModel):
    id: str
    vector: List[float]
    metadata: Optional[Dict[str, str]] = None


class VectorSearchRequest(BaseModel):
    query: List[float]
    k: int = 10


class TextSplitRequest(BaseModel):
    text: str
    chunk_size: int = 1000
    chunk_overlap: int = 200


class GraphNodeRequest(BaseModel):
    id: str
    label: str
    node_type: str = "entity"


class GraphEdgeRequest(BaseModel):
    source: str
    target: str
    edge_type: str = "related_to"
    weight: float = 1.0


@router.post("/vector/{store_id}/insert")
async def vector_insert(store_id: str, req: VectorInsertRequest):
    """Insert a vector into a store."""
    from aeryn_core.engine import VectorStore
    
    if store_id not in _vector_stores:
        if req.vector:
            dim = len(req.vector)
        else:
            raise HTTPException(400, "Cannot determine vector dimension")
        _vector_stores[store_id] = VectorStore(dim)
    
    store = _vector_stores[store_id]
    store.add(req.id, req.vector, req.metadata)
    return {"status": "ok", "store_id": store_id, "vectors": store.len()}


@router.post("/vector/{store_id}/search")
async def vector_search(store_id: str, req: VectorSearchRequest):
    """Search for similar vectors."""
    if store_id not in _vector_stores:
        raise HTTPException(404, f"Store {store_id} not found")
    
    store = _vector_stores[store_id]
    results = store.search(req.query, req.k)
    return {"results": results}


@router.get("/vector/{store_id}/stats")
async def vector_stats(store_id: str):
    """Get vector store statistics."""
    if store_id not in _vector_stores:
        raise HTTPException(404, f"Store {store_id} not found")
    
    store = _vector_stores[store_id]
    return {"vectors": store.len(), "dimensions": store.dimensions}


@router.post("/text/split")
async def text_split(text: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    """Split text into chunks."""
    from aeryn_core.engine import TextSplitter
    
    splitter = TextSplitter(chunk_size, chunk_overlap)
    chunks = splitter.split(text)
    return {"chunks": chunks, "count": len(chunks)}


@router.get("/text/tokenize")
async def text_tokenize(text: str):
    """Tokenize text."""
    from aeryn_core.engine import Tokenizer
    
    tokenizer = Tokenizer()
    tokens = tokenizer.tokenize(text)
    return {"tokens": tokens, "count": len(tokens)}


@router.post("/graph/create")
async def graph_create(graph_id: str):
    """Create a new graph."""
    from aeryn_core.engine import GraphEngine
    
    _graphs[graph_id] = GraphEngine()
    return {"status": "ok", "graph_id": graph_id}


@router.post("/graph/{graph_id}/node")
async def graph_add_node(graph_id: str, id: str, label: str, node_type: str = "entity"):
    """Add a node to the graph."""
    if graph_id not in _graphs:
        from aeryn_core.engine import GraphEngine
        _graphs[graph_id] = GraphEngine()
    
    graph = _graphs[graph_id]
    graph.add_node(id, label, node_type)
    return {"status": "ok", "nodes": graph.node_count()}


@router.post("/graph/{graph_id}/edge")
async def graph_add_edge(graph_id: str, source: str, target: str, edge_type: str = "related_to"):
    """Add an edge to the graph."""
    if graph_id not in _graphs:
        raise HTTPException(404, f"Graph {graph_id} not found")
    
    graph = _graphs[graph_id]
    graph.add_edge(source, target, edge_type)
    return {"status": "ok", "edges": graph.edge_count()}


@router.get("/graph/{graph_id}/bfs/{start}")
async def graph_bfs(graph_id: str, start: str, max_depth: int = 3):
    """Breadth-first search."""
    if graph_id not in _graphs:
        raise HTTPException(404, f"Graph {graph_id} not found")
    
    graph = _graphs[graph_id]
    visited = graph.bfs(start, max_depth)
    return {"visited": visited, "count": len(visited)}


@router.get("/graph/{graph_id}/dfs/{start}")
async def graph_dfs(graph_id: str, start: str, max_depth: int = 3):
    """Depth-first search."""
    if graph_id not in _graphs:
        raise HTTPException(404, f"Graph {graph_id} not found")
    
    graph = _graphs[graph_id]
    visited = graph.dfs(start, max_depth)
    return {"visited": visited, "count": len(visited)}


@router.get("/graph/{graph_id}/path/{source}/{target}")
async def graph_path(graph_id: str, source: str, target: str, max_depth: int = 10):
    """Find path between two nodes."""
    if graph_id not in _graphs:
        raise HTTPException(404, f"Graph {graph_id} not found")
    
    graph = _graphs[graph_id]
    path = graph.find_path(source, target, max_depth)
    return {"path": path, "found": path is not None}


@router.get("/graph/{graph_id}/stats")
async def graph_stats(graph_id: str):
    """Get graph statistics."""
    if graph_id not in _graphs:
        raise HTTPException(404, f"Graph {graph_id} not found")
    
    graph = _graphs[graph_id]
    return {"nodes": graph.node_count(), "edges": graph.edge_count()}


@router.get("/health")
async def engine_health():
    """Engine health check."""
    return {"status": "healthy", "module": "engine"}
