"""V39.46 — Hybrid Search Engine (Uteke-style) for Aeryn.

Implements:
1. FTS5 keyword search (SQLite built-in)
2. TF-IDF vector search (lightweight, no heavy deps)
3. Reciprocal Rank Fusion (RRF) for result merging
4. Memory aging/decay (salience + recency boost)

Inspired by Uteke's hybrid search architecture.
"""

import math
import os
import re
import sqlite3
import time
from collections import Counter
from typing import List, Dict, Tuple, Optional

import sys
from aeryn_core.utils.config import BASE_DIR, VAULT_DIR, DATABASE_DIR
sys.path.insert(0, '/home/sen/aeryn-core-agent')

DB_PATH = os.path.join(DATABASE_DIR, "hybrid_search.db")


class HybridSearchEngine:
    """Hybrid search: FTS5 + TF-IDF + RRF fusion."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
        self._idf = {}
        self._doc_count = 0
        self._cache = {}  # V39.60: query cache
        self._cache_ttl = 30  # seconds
        self._cache_timestamps = {}
    
    def _init_db(self):
        """Initialize SQLite database with FTS5 and metadata tables."""
        conn = sqlite3.connect(self.db_path)
        try:
            # FTS5 virtual table for full-text search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
                    memory_id,
                    title,
                    content,
                    tags,
                    author,
                    tokenize='porter unicode61'
                )
            """)
            
            # Metadata table for aging/decay
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_meta (
                    memory_id TEXT PRIMARY KEY,
                    created_at REAL,
                    last_accessed REAL,
                    access_count INTEGER DEFAULT 0,
                    salience REAL DEFAULT 1.0,
                    is_deprecated INTEGER DEFAULT 0
                )
            """)
            
            # Document frequency table for TF-IDF
            conn.execute("""
                CREATE TABLE IF NOT EXISTS term_df (
                    term TEXT PRIMARY KEY,
                    doc_count INTEGER DEFAULT 0
                )
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def index_memory(self, memory_id: str, title: str, content: str, 
                     tags: List[str] = None, author: str = "aeryn"):
        """Index a memory for search."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Delete existing index for this memory
            conn.execute("DELETE FROM search_index WHERE memory_id = ?", (memory_id,))
            
            # Insert into FTS5
            tags_str = " ".join(tags or [])
            conn.execute(
                "INSERT INTO search_index (memory_id, title, content, tags, author) VALUES (?, ?, ?, ?, ?)",
                (memory_id, title, content, tags_str, author)
            )
            
            # Update metadata
            now = time.time()
            conn.execute("""
                INSERT OR REPLACE INTO memory_meta (memory_id, created_at, last_accessed, access_count)
                VALUES (?, ?, ?, COALESCE((SELECT access_count FROM memory_meta WHERE memory_id = ?), 0))
            """, (memory_id, now, now, memory_id))
            
            # Update document frequencies
            tokens = self._tokenize(content + " " + title + " " + tags_str)
            for term in set(tokens):
                conn.execute("""
                    INSERT INTO term_df (term, doc_count) VALUES (?, 1)
                    ON CONFLICT(term) DO UPDATE SET doc_count = doc_count + 1
                """, (term,))
            
            conn.commit()
            self._update_idf()
        finally:
            conn.close()
    
    def search(self, query: str, limit: int = 10, 
               fts_weight: float = 0.5, tfidf_weight: float = 0.5,
               aging_boost: bool = True) -> List[Dict]:
        """
        Hybrid search combining FTS5 + TF-IDF with RRF fusion.
        
        Args:
            query: Search query
            limit: Max results
            fts_weight: Weight for FTS5 results (0-1)
            tfidf_weight: Weight for TF-IDF results (0-1)
            aging_boost: Apply recency/salience boost
        
        Returns:
            List of results with score, memory_id, title, content
        """
        # V39.60: Check cache
        cache_key = f"{query}:{limit}:{fts_weight}:{tfidf_weight}:{aging_boost}"
        now = time.time()
        if cache_key in self._cache:
            if now - self._cache_timestamps.get(cache_key, 0) < self._cache_ttl:
                return self._cache[cache_key]
        
        # FTS5 search
        fts_results = self._fts_search(query, limit * 3)
        
        # TF-IDF search
        tfidf_results = self._tfidf_search(query, limit * 3)
        
        # RRF fusion
        fused = self._rrf_fusion(fts_results, tfidf_results, 
                                  fts_weight, tfidf_weight, k=60)
        
        # Apply aging boost
        if aging_boost:
            fused = self._apply_aging_boost(fused)
        
        # Fetch full records
        results = self._fetch_records(fused[:limit])
        
        # Update access counts
        self._update_access([r["memory_id"] for r in results])
        
        # V39.60: Store in cache
        self._cache[cache_key] = results
        self._cache_timestamps[cache_key] = now
        
        return results
    
    def _fts_search(self, query: str, limit: int) -> List[Tuple[str, float]]:
        """FTS5 full-text search."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Clean query for FTS5
            clean_query = re.sub(r'[^\w\s]', ' ', query).strip()
            if not clean_query:
                return []
            
            # FTS5 ranking (lower rank = better, so we negate for score)
            cursor = conn.execute("""
                SELECT memory_id, -rank as score
                FROM search_index
                WHERE search_index MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (clean_query, limit))
            
            return [(row[0], row[1]) for row in cursor.fetchall()]
        except Exception:
            return []
        finally:
            conn.close()
    
    def _tfidf_search(self, query: str, limit: int) -> List[Tuple[str, float]]:
        """TF-IDF cosine similarity search."""
        conn = sqlite3.connect(self.db_path)
        try:
            query_tokens = self._tokenize(query)
            if not query_tokens:
                return []
            
            # Get all memory IDs
            cursor = conn.execute("SELECT memory_id FROM search_index")
            memory_ids = [row[0] for row in cursor.fetchall()]
            
            if not memory_ids:
                return []
            
            # Calculate TF-IDF scores
            scores = []
            for mid in memory_ids:
                cursor = conn.execute(
                    "SELECT title, content, tags FROM search_index WHERE memory_id = ?", (mid,)
                )
                row = cursor.fetchone()
                if not row:
                    continue
                
                doc_tokens = self._tokenize(f"{row[0]} {row[1]} {row[2]}")
                score = self._cosine_similarity(query_tokens, doc_tokens)
                if score > 0:
                    scores.append((mid, score))
            
            scores.sort(key=lambda x: -x[1])
            return scores[:limit]
        finally:
            conn.close()
    
    def _rrf_fusion(self, fts_results: List[Tuple[str, float]], 
                    tfidf_results: List[Tuple[str, float]],
                    fts_weight: float, tfidf_weight: float,
                    k: int = 60) -> List[Tuple[str, float]]:
        """Reciprocal Rank Fusion."""
        scores = {}
        
        for rank, (mid, _) in enumerate(fts_results):
            scores[mid] = scores.get(mid, 0) + fts_weight / (k + rank + 1)
        
        for rank, (mid, _) in enumerate(tfidf_results):
            scores[mid] = scores.get(mid, 0) + tfidf_weight / (k + rank + 1)
        
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return ranked
    
    def _apply_aging_boost(self, results: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """Apply recency and salience boost to scores."""
        conn = sqlite3.connect(self.db_path)
        try:
            boosted = []
            now = time.time()
            
            for mid, score in results:
                cursor = conn.execute(
                    "SELECT created_at, access_count, salience FROM memory_meta WHERE memory_id = ?",
                    (mid,)
                )
                row = cursor.fetchone()
                
                if row:
                    created_at, access_count, salience = row
                    # Recency boost: newer memories get higher boost
                    days_old = (now - created_at) / 86400
                    recency_factor = 1.0 / (1.0 + days_old * 0.1)  # Decay over time
                    
                    # Salience boost: frequently accessed memories get higher boost
                    salience_factor = 1.0 + math.log(1 + access_count) * 0.1
                    
                    # Combined boost
                    boost = recency_factor * salience_factor * (salience or 1.0)
                    score *= boost
                
                boosted.append((mid, score))
            
            boosted.sort(key=lambda x: -x[1])
            return boosted
        finally:
            conn.close()
    
    def _fetch_records(self, results: List[Tuple[str, float]]) -> List[Dict]:
        """Fetch full records for results."""
        conn = sqlite3.connect(self.db_path)
        try:
            records = []
            for mid, score in results:
                cursor = conn.execute(
                    "SELECT memory_id, title, content, tags, author FROM search_index WHERE memory_id = ?",
                    (mid,)
                )
                row = cursor.fetchone()
                if row:
                    records.append({
                        "memory_id": row[0],
                        "title": row[1],
                        "content": row[2],
                        "tags": row[3].split() if row[3] else [],
                        "author": row[4],
                        "score": round(score, 4)
                    })
            return records
        finally:
            conn.close()
    
    def _update_access(self, memory_ids: List[str]):
        """Update access counts for memories."""
        conn = sqlite3.connect(self.db_path)
        try:
            now = time.time()
            for mid in memory_ids:
                conn.execute("""
                    UPDATE memory_meta 
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE memory_id = ?
                """, (now, mid))
            conn.commit()
        finally:
            conn.close()
    
    def deprecate_memory(self, memory_id: str):
        """Mark a memory as deprecated."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "UPDATE memory_meta SET is_deprecated = 1 WHERE memory_id = ?",
                (memory_id,)
            )
            conn.commit()
        finally:
            conn.close()
    
    def get_deprecated(self, query: str, limit: int = 5) -> List[Dict]:
        """Search deprecated memories (for supersession)."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT s.memory_id, s.title, s.content, s.tags, s.author
                FROM search_index s
                JOIN memory_meta m ON s.memory_id = m.memory_id
                WHERE s.search_index MATCH ? AND m.is_deprecated = 1
                LIMIT ?
            """, (query, limit))
            
            return [{
                "memory_id": row[0],
                "title": row[1],
                "content": row[2],
                "tags": row[3].split() if row[3] else [],
                "author": row[4]
            } for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for TF-IDF."""
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        # Remove stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'could', 'should', 'may', 'might', 'can', 'shall',
                     'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                     'as', 'into', 'through', 'during', 'before', 'after', 'above',
                     'below', 'between', 'out', 'off', 'over', 'under', 'again',
                     'further', 'then', 'once', 'and', 'but', 'or', 'nor', 'not',
                     'so', 'than', 'too', 'very', 'just', 'about', 'this', 'that',
                     'these', 'those', 'it', 'its', 'i', 'we', 'you', 'they', 'he',
                     'she', 'my', 'your', 'his', 'her', 'our', 'their', 'what',
                     'which', 'who', 'whom', 'when', 'where', 'why', 'how'}
        return [t for t in tokens if t not in stopwords and len(t) > 2]
    
    def _cosine_similarity(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        """Calculate cosine similarity between query and document."""
        if not query_tokens or not doc_tokens:
            return 0.0
        
        query_vec = Counter(query_tokens)
        doc_vec = Counter(doc_tokens)
        
        # Calculate dot product
        dot_product = sum(query_vec[t] * doc_vec[t] for t in query_vec if t in doc_vec)
        
        # Calculate magnitudes
        query_mag = math.sqrt(sum(v ** 2 for v in query_vec.values()))
        doc_mag = math.sqrt(sum(v ** 2 for v in doc_vec.values()))
        
        if query_mag == 0 or doc_mag == 0:
            return 0.0
        
        return dot_product / (query_mag * doc_mag)
    
    def _update_idf(self):
        """Update IDF cache."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM search_index")
            self._doc_count = cursor.fetchone()[0]
            
            if self._doc_count == 0:
                return
            
            cursor = conn.execute("SELECT term, doc_count FROM term_df")
            for term, count in cursor.fetchall():
                self._idf[term] = math.log(self._doc_count / (1 + count))
        finally:
            conn.close()


# Singleton
_engine = None

def get_search_engine() -> HybridSearchEngine:
    global _engine
    if _engine is None:
        _engine = HybridSearchEngine()
    return _engine
