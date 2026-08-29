#!/usr/bin/env python3
"""V39.68 — Semantic Recall: Hybrid search with vector fallback.

Search lanes:
1. FTS5 keyword search — always available
2. Vector similarity — optional (falls back gracefully)

When embedding model is available, both lanes run and fuse via RRF.
When not available, keyword search alone is used.
"""

import os
import sys
import re
import json
import time
import sqlite3
import threading
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(DATABASE_DIR, "semantic_search.db")


class SemanticSearchEngine:
    """Hybrid search: FTS5 + optional vector similarity."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
        self._embedding_model = None  # Lazy load
        self._idf = {}
        self._doc_count = 0
        self._cache = {}
        self._cache_ttl = 30
        self._cache_timestamps = {}
    
    def _init_db(self):
        """Initialize database with FTS5 and vector table."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT DEFAULT 'vault',
                    author TEXT DEFAULT 'aeryn',
                    created_at REAL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
                    memory_id,
                    title,
                    content,
                    source,
                    author
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    memory_id TEXT PRIMARY KEY,
                    vector BLOB,
                    model TEXT,
                    created_at REAL,
                    FOREIGN KEY (memory_id) REFERENCES memories(id)
                )
            """)
            conn.commit()
        finally:
            conn.close()
    
    @property
    def has_embedding_model(self) -> bool:
        """Check if embedding model is available."""
        return self._load_embedding_model() is not None
    
    def _load_embedding_model(self):
        """Try to load embedding model (lazy)."""
        if self._embedding_model is not None:
            return self._embedding_model
        
        try:
            # Try sentence-transformers first
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            return self._embedding_model
        except (ImportError, Exception):
            pass
        
        try:
            # Fallback: use TF-IDF-based pseudo-embeddings
            self._embedding_model = "tfidf"
            return self._embedding_model
        except Exception:
            return None
    
    def index_memory(self, memory_id: str, title: str, content: str,
                     source: str = "vault", author: str = "aeryn",
                     metadata: dict = None) -> bool:
        """Index a memory entry."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO memories (id, title, content, source, author, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (memory_id, title, content, source, author, time.time(),
                      json.dumps(metadata or {})))
                
                # Manually insert into FTS index (no trigger)
                conn.execute("""
                    INSERT OR REPLACE INTO search_index (memory_id, title, content, source, author)
                    VALUES (?, ?, ?, ?, ?)
                """, (memory_id, title, content, source, author))
                
                conn.commit()
                
                # Generate embedding if model available
                self._generate_embedding(conn, memory_id, title, content)
                
                return True
            except Exception as e:
                return False
            finally:
                conn.close()
    
    def _generate_embedding(self, conn, memory_id: str, title: str, content: str):
        """Generate and store embedding for a memory."""
        model = self._load_embedding_model()
        if model is None:
            return
        
        try:
            text = f"{title} {content}"
            if model == "tfidf":
                # TF-IDF pseudo-embedding fallback
                vector = self._tfidf_vector(text)
            else:
                vector = model.encode(text, show_progress_bar=False)
            
            vector_bytes = vector.tobytes() if hasattr(vector, 'tobytes') else bytes(vector)
            
            conn.execute("""
                INSERT OR REPLACE INTO embeddings (memory_id, vector, model, created_at)
                VALUES (?, ?, ?, ?)
            """, (memory_id, vector_bytes, str(type(model).__name__), time.time()))
            conn.commit()
        except Exception:
            pass  # Embedding is optional
    
    def _tfidf_vector(self, text: str) -> list:
        """TF-IDF pseudo-embedding (fallback when no model)."""
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * 64  # Fixed-size zero vector
        
        # Simple hash-based vector (deterministic)
        vector = [0.0] * 64
        for token in tokens:
            idx = hash(token) % 64
            vector[idx] += 1.0
        
        # Normalize
        magnitude = sum(v**2 for v in vector) ** 0.5
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        if not text:
            return []
        text = text.lower()
        tokens = re.findall(r'\b[a-z]{2,}\b', text)
        return tokens
    
    def search(self, query: str, limit: int = 10, 
               keyword_weight: float = 0.5, vector_weight: float = 0.5) -> List[Dict]:
        """Hybrid search: keyword + vector (if available)."""
        # Check cache
        cache_key = f"{query}:{limit}:{keyword_weight}:{vector_weight}"
        now = time.time()
        if cache_key in self._cache:
            if now - self._cache_timestamps.get(cache_key, 0) < self._cache_ttl:
                return self._cache[cache_key]
        
        # Keyword search
        keyword_results = self._keyword_search(query, limit * 3)
        
        # Vector search (if available)
        if self.has_embedding_model:
            vector_results = self._vector_search(query, limit * 3)
            # Fuse results
            fused = self._rrf_fusion(keyword_results, vector_results, 
                                      keyword_weight, vector_weight)
            results = self._fetch_records(fused[:limit])
        else:
            results = self._fetch_records(keyword_results[:limit])
        
        # Cache
        self._cache[cache_key] = results
        self._cache_timestamps[cache_key] = now
        
        return results
    
    def _keyword_search(self, query: str, limit: int) -> List[Tuple[str, float]]:
        """FTS5 keyword search."""
        conn = sqlite3.connect(self.db_path)
        try:
            clean_query = re.sub(r'[^\w\s]', ' ', query).strip()
            if not clean_query:
                return []
            
            # FTS5 query needs proper quoting
            # Wrap each word in double quotes for exact matching
            words = clean_query.split()
            fts_query = " OR ".join(f'"{w}"' for w in words)
            
            rows = conn.execute("""
                SELECT memory_id, rank
                FROM search_index
                WHERE search_index MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (fts_query, limit)).fetchall()
            
            results = []
            for row in rows:
                memory_id = row[0]
                rank = row[1] if row[1] else -100.0
                score = 1.0 / (1.0 + abs(rank))
                results.append((memory_id, score))
            
            return results
        except Exception as e:
            return []
        finally:
            conn.close()
    
    def _vector_search(self, query: str, limit: int) -> List[Tuple[str, float]]:
        """Vector similarity search."""
        model = self._load_embedding_model()
        if model is None:
            return []
        
        try:
            # Encode query
            if model == "tfidf":
                query_vector = self._tfidf_vector(query)
            else:
                query_vector = model.encode(query, show_progress_bar=False).tolist()
            
            # Fetch all embeddings
            conn = sqlite3.connect(self.db_path)
            try:
                rows = conn.execute("""
                    SELECT e.memory_id, e.vector, m.title, m.content
                    FROM embeddings e
                    JOIN memories m ON e.memory_id = m.id
                """).fetchall()
            finally:
                conn.close()
            
            # Compute cosine similarity
            results = []
            for memory_id, vector_bytes, title, content in rows:
                try:
                    import numpy as np
                    stored_vector = np.frombuffer(vector_bytes, dtype=np.float32)
                    if len(stored_vector) != len(query_vector):
                        continue
                    # Cosine similarity
                    dot = sum(a * b for a, b in zip(query_vector, stored_vector))
                    magnitude_a = sum(a**2 for a in query_vector) ** 0.5
                    magnitude_b = sum(b**2 for b in stored_vector) ** 0.5
                    if magnitude_a * magnitude_b == 0:
                        continue
                    similarity = dot / (magnitude_a * magnitude_b)
                    results.append((memory_id, similarity))
                except Exception:
                    continue
            
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
        except Exception:
            return []
    
    def _rrf_fusion(self, list_a: List[Tuple], list_b: List[Tuple],
                    weight_a: float = 0.5, weight_b: float = 0.5,
                    k: int = 60) -> List[Tuple[str, float]]:
        """Reciprocal Rank Fusion."""
        scores = {}
        
        for rank, (doc_id, score) in enumerate(list_a):
            rrf_score = weight_a * score / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score
        
        for rank, (doc_id, score) in enumerate(list_b):
            rrf_score = weight_b * score / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score
        
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results
    
    def _fetch_records(self, results: List[Tuple[str, float]]) -> List[Dict]:
        """Fetch full records for results."""
        if not results:
            return []
        
        conn = sqlite3.connect(self.db_path)
        try:
            records = []
            for memory_id, score in results:
                row = conn.execute("""
                    SELECT id, title, content, source, author, created_at, metadata
                    FROM memories WHERE id = ?
                """, (memory_id,)).fetchone()
                
                if row:
                    records.append({
                        "memory_id": row[0],
                        "title": row[1],
                        "content": row[2][:500],
                        "source": row[3],
                        "author": row[4],
                        "created_at": row[5],
                        "metadata": json.loads(row[6]) if row[6] else {},
                        "score": round(score, 4),
                    })
            
            return records
        except Exception:
            return []
        finally:
            conn.close()
    
    def get_stats(self) -> dict:
        """Get engine statistics."""
        conn = sqlite3.connect(self.db_path)
        try:
            memory_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            embedding_count = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
            return {
                "total_memories": memory_count,
                "total_embeddings": embedding_count,
                "has_vector_model": self.has_embedding_model,
                "status": "hybrid" if self.has_embedding_model else "keyword_only",
            }
        finally:
            conn.close()


# Singleton
_engine = None

def get_semantic_search() -> SemanticSearchEngine:
    global _engine
    if _engine is None:
        _engine = SemanticSearchEngine()
    return _engine


if __name__ == "__main__":
    sse = SemanticSearchEngine()
    print("=== Semantic Search Engine ===")
    print(f"Stats: {sse.get_stats()}")
    
    # Index test
    sse.index_memory("test1", "Docker Guide", "How to install Docker on Ubuntu", "vault", "sen")
    sse.index_memory("test2", "Python Tips", "Python best practices and tips", "vault", "sen")
    
    print(f"After indexing: {sse.get_stats()}")
    
    # Search
    results = sse.search("install docker compose", limit=5)
    print(f"Search 'install docker compose': {len(results)} results")
    for r in results:
        print(f"  {r['title']} (score: {r['score']})")
    
    # Fallback test
    results2 = sse.search("python programming", limit=3)
    print(f"Search 'python programming': {len(results2)} results")
    for r in results2:
        print(f"  {r['title']} (score: {r['score']})")
