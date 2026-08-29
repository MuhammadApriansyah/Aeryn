#!/usr/bin/env python3
"""
V41.0 — Rust VectorDB wrapper.
Menggunakan aeryn-engine untuk performa 10-100x lebih cepat.
"""

from typing import List, Dict, Optional, Sequence, Any
from aeryn_engine import VectorDB as RustVectorDB, Collection as RustCollection

class VectorDB:
    """Wrapper Python untuk Rust VectorDB — drop-in replacement untuk vector_db.py."""
    
    def __init__(self, persist_dir: str = None):
        self._db = RustVectorDB()
        self._collections: Dict[str, Collection] = {}
    
    def get_or_create_collection(self, name: str) -> 'Collection':
        if name not in self._collections:
            rust_coll = self._db.get_or_create_collection(name)
            self._collections[name] = Collection(name, rust_coll, self._db)
        return self._collections[name]
    
    def list_collections(self) -> List[str]:
        return self._db.list_collections()
    
    def delete_collection(self, name: str) -> bool:
        if name in self._collections:
            del self._collections[name]
        return self._db.delete_collection(name)


class Collection:
    """Wrapper Python untuk Rust Collection."""
    
    def __init__(self, name: str, rust_coll: RustCollection, db: RustVectorDB):
        self.name = name
        self._coll = rust_coll
        self._db = db
    
    def add(
        self,
        ids: Sequence[str],
        documents: Optional[Sequence[str]] = None,
        embeddings: Optional[Sequence[List[float]]] = None,
        metadatas: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> None:
        embeddings = embeddings or [None] * len(ids)
        metadatas = [str(m) if m else "{}" for m in (metadatas or [None] * len(ids))]
        documents = documents or [None] * len(ids)
        
        self._coll.add(
            ids=list(ids),
            documents=list(documents),
            embeddings=list(embeddings),
            metadatas=metadatas,
        )
    
    def query(
        self,
        query_embeddings: Optional[Sequence[List[float]]] = None,
        n_results: int = 10,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        results = self._coll.query(
            query_embeddings=list(query_embeddings) if query_embeddings else [],
            n_results=n_results,
        )
        return [
            {
                "id": r.get("id", ""),
                "document": r.get("document", ""),
                "score": float(r.get("score", 0.0)),
            }
            for r in results
        ]
    
    def delete(self, ids: Sequence[str]) -> int:
        return self._coll.delete(list(ids))
    
    def count(self) -> int:
        return self._coll.count()
