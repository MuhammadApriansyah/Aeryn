#!/usr/bin/env python3
"""VectorDB — Chromadb/Qdrant-style vector storage with automatic fallback.

API (mirrors Chromadb collection interface):
    db = VectorDB(persist_dir="~/.aeryn/vector_store")
    coll = db.get_or_create_collection("knowledge")
    coll.add(ids=["a", "b"], documents=["hello world", "foo bar"])
    results = coll.query(query_texts=["hello"], n_results=5)
    db.delete_collection("knowledge")

Backends (auto-selected at import time):
    1. chromadb — full-featured, persistent, HNSW index
    2. sqlite  — pure-stdlib fallback, exact cosine similarity
"""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------
_CHROMADB_AVAILABLE = False
try:
    import chromadb  # type: ignore
    _CHROMADB_AVAILABLE = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Pure-Python embedding (hash-bag, no model needed)
# ---------------------------------------------------------------------------
_EMBED_DIM = 256


def _tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, split on whitespace."""
    if not text:
        return []
    text = text.lower()
    tokens = re.findall(r"\b[a-z0-9]{2,}\b", text)
    return tokens


def _embed(text: str) -> List[float]:
    """Deterministic hash-bag embedding — works without any model."""
    vector = [0.0] * _EMBED_DIM
    for token in _tokenize(text):
        idx = hash(token) % _EMBED_DIM
        vector[idx] += 1.0
    # L2-normalize
    mag = math.sqrt(sum(v * v for v in vector))
    if mag > 0:
        vector = [v / mag for v in vector]
    return vector


# ---------------------------------------------------------------------------
# Cosine similarity (pure Python)
# ---------------------------------------------------------------------------
def _cosine(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two equal-length vectors."""
    if len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    denom = math.sqrt(na * nb)
    return dot / denom if denom > 0 else 0.0


def _bytes_to_vector(buf: bytes) -> List[float]:
    """Deserialize float32 blob to list."""
    n = len(buf) // 4
    # struct.unpack is faster than manual bit-twiddling
    import struct
    return list(struct.unpack(f"<{n}f", buf))


def _vector_to_bytes(v: List[float]) -> bytes:
    """Serialize float32 list to blob."""
    import struct
    return struct.pack(f"<{len(v)}f", *v)


# ---------------------------------------------------------------------------
# Chromadb backend — thin wrapper
# ---------------------------------------------------------------------------
class _ChromadbCollection:
    """Wraps a Chromadb Collection to present a uniform interface."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    def add(
        self,
        ids: Sequence[str],
        documents: Optional[Sequence[str]] = None,
        embeddings: Optional[Sequence[List[float]]] = None,
        metadatas: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> None:
        kwargs: Dict[str, Any] = {"ids": list(ids)}
        if documents is not None:
            kwargs["documents"] = list(documents)
        if embeddings is not None:
            kwargs["embeddings"] = [list(e) for e in embeddings]
        if metadatas is not None:
            kwargs["metadatas"] = [dict(m) for m in metadatas]
        self._inner.add(**kwargs)

    def query(
        self,
        query_texts: Optional[Sequence[str]] = None,
        query_embeddings: Optional[Sequence[List[float]]] = None,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        kwargs: Dict[str, Any] = {"n_results": n_results}
        if query_texts is not None:
            kwargs["query_texts"] = list(query_texts)
        if query_embeddings is not None:
            kwargs["query_embeddings"] = [list(e) for e in query_embeddings]
        if where is not None:
            kwargs["where"] = where
        raw = self._inner.query(**kwargs)
        # Chromadb returns nested lists (one list per query). Flatten for 1 query.
        docs = raw.get("documents", [[]])[0]
        ids = raw.get("ids", [[]])[0]
        distances = raw.get("distances", [[0.0] * len(ids)])[0]
        metadatas = raw.get("metadatas", [[{}] * len(ids)])[0]
        results = []
        for i, doc_id in enumerate(ids):
            results.append({
                "id": doc_id,
                "document": docs[i] if i < len(docs) else "",
                "score": 1.0 - distances[i] if i < len(distances) else 0.0,
                "metadata": metadatas[i] if i < len(metadatas) and metadatas[i] else {},
            })
        return results

    def delete(self, ids: Sequence[str]) -> None:
        self._inner.delete(ids=list(ids))

    def count(self) -> int:
        return self._inner.count()


# ---------------------------------------------------------------------------
# SQLite backend — pure-stdlib fallback
# ---------------------------------------------------------------------------
class _SqliteCollection:
    """SQLite-backed vector collection with exact cosine search."""

    def __init__(self, conn: sqlite3.Connection, name: str, lock: threading.Lock) -> None:
        self._conn = conn
        self._name = self._sanitize_table_name(name)
        self._lock = lock
        self._ensure_table()
    
    @staticmethod
    def _sanitize_table_name(name: str) -> str:
        """Sanitize table name — only alphanumeric and underscore allowed."""
        if not name or not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
            raise ValueError(f"Invalid table name: {name!r}")
        return name

    def _ensure_table(self) -> None:
        with self._lock:
            self._conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._name} (
                    id TEXT PRIMARY KEY,
                    document TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    metadata TEXT DEFAULT '{{}}',
                    created_at REAL
                )
            """)
            self._conn.commit()

    def add(
        self,
        ids: Sequence[str],
        documents: Optional[Sequence[str]] = None,
        embeddings: Optional[Sequence[List[float]]] = None,
        metadatas: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> None:
        now = time.time()
        with self._lock:
            for i, doc_id in enumerate(ids):
                doc = documents[i] if documents else ""
                emb = embeddings[i] if embeddings else _embed(doc)
                meta = metadatas[i] if metadatas else {}
                self._conn.execute(
                    f"""INSERT OR REPLACE INTO {self._name}
                        (id, document, embedding, metadata, created_at)
                        VALUES (?, ?, ?, ?, ?)""",
                    (doc_id, doc, _vector_to_bytes(emb), json.dumps(meta), now),
                )
            self._conn.commit()

    def query(
        self,
        query_texts: Optional[Sequence[str]] = None,
        query_embeddings: Optional[Sequence[List[float]]] = None,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not query_texts and not query_embeddings:
            return []
        # We only handle the first query for simplicity
        if query_embeddings:
            q_emb = list(query_embeddings[0])
        else:
            q_emb = _embed(query_texts[0])  # type: ignore[index]

        with self._lock:
            rows = self._conn.execute(
                f"SELECT id, document, embedding, metadata FROM {self._sanitize_table_name(self._name)}"
            ).fetchall()

        scored: List[Tuple[float, str, str, Dict[str, Any]]] = []
        for row in rows:
            doc_id, doc_text, emb_blob, meta_json = row
            vec = _bytes_to_vector(emb_blob)
            score = _cosine(q_emb, vec)
            meta = json.loads(meta_json) if meta_json else {}
            if where and not self._match_where(meta, where):
                continue
            scored.append((score, doc_id, doc_text, meta))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, doc_id, doc_text, meta in scored[:n_results]:
            results.append({
                "id": doc_id,
                "document": doc_text,
                "score": round(score, 6),
                "metadata": meta,
            })
        return results

    def delete(self, ids: Sequence[str]) -> None:
        with self._lock:
            for doc_id in ids:
                self._conn.execute(
                    f"DELETE FROM {self._sanitize_table_name(self._name)} WHERE id = ?", (doc_id,)
                )
            self._conn.commit()

    def count(self) -> int:
        with self._lock:
            row = self._conn.execute(
                f"SELECT COUNT(*) FROM {self._name}"
            ).fetchone()
            return row[0] if row else 0

    def _match_where(self, metadata: Dict[str, Any], where: Dict[str, Any]) -> bool:
        """Simple equality match (supports Chromadb's $eq style)."""
        for key, condition in where.items():
            val = metadata.get(key)
            if isinstance(condition, dict):
                if "$eq" in condition and val != condition["$eq"]:
                    return False
                if "$ne" in condition and val == condition["$ne"]:
                    return False
                if "$in" in condition and val not in condition["$in"]:
                    return False
            else:
                if val != condition:
                    return False
        return True


# ---------------------------------------------------------------------------
# VectorDB — top-level manager
# ---------------------------------------------------------------------------
class VectorDB:
    """Chromadb/Qdrant-style vector database with automatic backend selection.

    Usage:
        db = VectorDB(persist_dir="~/.aeryn/vector_store")
        coll = db.get_or_create_collection("knowledge")
        coll.add(ids=["1"], documents=["Aeryn is an AI agent framework"])
        results = coll.query(query_texts=["what is aeryn"], n_results=5)
        db.delete_collection("knowledge")
    """

    def __init__(
        self,
        persist_dir: str = "~/.aeryn/vector_store",
        backend: Optional[str] = None,
    ) -> None:
        self._persist_dir = os.path.expanduser(persist_dir)
        os.makedirs(self._persist_dir, exist_ok=True)
        self._lock = threading.Lock()

        # Resolve backend
        if backend is None:
            self._backend = "chromadb" if _CHROMADB_AVAILABLE else "sqlite"
        elif backend == "chromadb" and not _CHROMADB_AVAILABLE:
            self._backend = "sqlite"
        else:
            self._backend = backend

        # Init backend-specific state
        self._chromadb_client: Optional[Any] = None
        self._sqlite_conn: Optional[sqlite3.Connection] = None
        self._collections: Dict[str, Any] = {}

        if self._backend == "chromadb":
            settings = chromadb.Settings(
                persist_directory=self._persist_dir,
                is_persistent=True,
                anonymized_telemetry=False,
            )
            self._chromadb_client = chromadb.Client(settings)
        else:
            db_path = os.path.join(self._persist_dir, "vector_store.db")
            self._sqlite_conn = sqlite3.connect(db_path, check_same_thread=False)

    # -- Collection management ----------------------------------------------

    def get_or_create_collection(self, name: str) -> Any:
        """Get or create a collection by name."""
        if name in self._collections:
            return self._collections[name]

        if self._backend == "chromadb":
            inner = self._chromadb_client.get_or_create_collection(name)
            coll = _ChromadbCollection(inner)
        else:
            coll = _SqliteCollection(self._sqlite_conn, name, self._lock)

        self._collections[name] = coll
        return coll

    def delete_collection(self, name: str) -> None:
        """Delete a collection and all its data."""
        if self._backend == "chromadb":
            try:
                self._chromadb_client.delete_collection(name)
            except Exception:
                pass
        else:
            with self._lock:
                self._sqlite_conn.execute(f"DROP TABLE IF EXISTS {name}")
                self._sqlite_conn.commit()
        self._collections.pop(name, None)

    def list_collections(self) -> List[str]:
        """List all collection names."""
        if self._backend == "chromadb":
            return [c.name for c in self._chromadb_client.list_collections()]
        else:
            with self._lock:
                rows = self._sqlite_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            return [r[0] for r in rows]

    # -- Convenience helpers ------------------------------------------------

    def add_documents(
        self,
        collection_name: str,
        documents: Sequence[str],
        ids: Optional[Sequence[str]] = None,
        metadatas: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Add documents to a collection. Returns the IDs used."""
        coll = self.get_or_create_collection(collection_name)
        if ids is None:
            ids = [str(uuid.uuid4())[:12] for _ in documents]
        coll.add(ids=list(ids), documents=list(documents), metadatas=metadatas)
        return list(ids)

    def similarity_search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 10,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Search a collection for documents similar to *query*."""
        coll = self.get_or_create_collection(collection_name)
        return coll.query(query_texts=[query], n_results=n_results, **kwargs)

    def delete_documents(self, collection_name: str, ids: Sequence[str]) -> None:
        """Delete documents by ID from a collection."""
        coll = self.get_or_create_collection(collection_name)
        coll.delete(ids=list(ids))

    # -- Cleanup ------------------------------------------------------------

    def close(self) -> None:
        """Close underlying connections."""
        if self._backend == "chromadb" and self._chromadb_client:
            self._chromadb_client.persist()
        elif self._sqlite_conn:
            self._sqlite_conn.close()

    def __repr__(self) -> str:
        return (
            f"<VectorDB backend={self._backend!r} "
            f"dir={self._persist_dir!r}>"
        )


# ---------------------------------------------------------------------------
# Singleton helper
# ---------------------------------------------------------------------------
_default_db: Optional[VectorDB] = None


def get_vector_db(persist_dir: str = "~/.aeryn/vector_store") -> VectorDB:
    """Return a process-wide VectorDB singleton."""
    global _default_db
    if _default_db is None:
        _default_db = VectorDB(persist_dir=persist_dir)
    return _default_db


# ---------------------------------------------------------------------------
# CLI / self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    db = VectorDB()
    print(f"Backend: {db._backend}")

    # Add documents
    ids = db.add_documents(
        "demo",
        documents=[
            "Aeryn is an AI agent framework built for autonomous tasks",
            "Docker containers are lightweight and portable",
            "Python is a versatile programming language",
            "Vector databases enable semantic search at scale",
        ],
        metadatas=[
            {"category": "ai"},
            {"category": "devops"},
            {"category": "programming"},
            {"category": "databases"},
        ],
    )
    print(f"Added {len(ids)} documents: {ids}")

    # Search
    results = db.similarity_search("demo", "AI agent autonomous", n_results=3)
    print("\nSearch results:")
    for r in results:
        print(f"  [{r['score']:.4f}] {r['document'][:60]}...")

    # List collections
    print(f"\nCollections: {db.list_collections()}")

    # Delete and verify
    db.delete_collection("demo")
    print(f"After delete: {db.list_collections()}")
    db.close()
    print("\nDone.")