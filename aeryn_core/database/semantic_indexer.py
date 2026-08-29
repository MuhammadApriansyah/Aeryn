#!/usr/bin/env python3
"""V41.0 — Phase 1: Semantic Search Indexing.

Indexes all vault entries into the semantic search engine.
Run periodically to keep search up to date.
"""

import os, sys, json, sqlite3, hashlib, math, time
from typing import List, Dict, Optional
from datetime import datetime
from aeryn_core.utils.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(DATABASE_DIR, "semantic_search.db")
VAULT_BASE = VAULT_DIR
LAYERS = ["Raw", "Wiki", "Projects", "System", "Daily", "Skills"]

class SemanticIndexer:
    """Index vault entries into semantic search."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_type TEXT DEFAULT 'vault',
                source_id TEXT,
                metadata TEXT DEFAULT '{}',
                indexed_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS embeddings (
                doc_id TEXT PRIMARY KEY,
                vector BLOB NOT NULL,
                dimensions INTEGER DEFAULT 256,
                FOREIGN KEY (doc_id) REFERENCES documents(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_docs_source ON documents(source_type, source_id);
            CREATE INDEX IF NOT EXISTS idx_docs_indexed ON documents(indexed_at);
        """)
        conn.commit()
        conn.close()
    
    def _embed(self, text: str) -> List[float]:
        """Create deterministic hash-bag embedding (256-dim)."""
        vec = [0.0] * 256
        words = text.lower().split()
        for word in words:
            h = hashlib.md5(word.encode()).hexdigest()
            for i in range(0, 32, 2):
                idx = int(h[i:i+2], 16)
                vec[idx] += 1.0
        
        # L2 normalize
        mag = math.sqrt(sum(x*x for x in vec)) or 1.0
        return [x/mag for x in vec]
    
    def index_vault(self, force: bool = False) -> Dict:
        """Index all vault entries."""
        conn = sqlite3.connect(self.db_path)
        indexed = 0
        updated = 0
        errors = 0
        
        for layer in LAYERS:
            dirpath = os.path.join(VAULT_BASE, layer)
            if not os.path.isdir(dirpath):
                continue
            
            for fname in os.listdir(dirpath):
                if not fname.endswith(".md"):
                    continue
                
                filepath = os.path.join(dirpath, fname)
                doc_id = f"{layer}/{fname}"
                
                try:
                    # Check if already indexed
                    if not force:
                        existing = conn.execute(
                            "SELECT indexed_at FROM documents WHERE id = ?",
                            (doc_id,)
                        ).fetchone()
                        if existing:
                            # Check if file modified since indexing
                            file_mtime = os.path.getmtime(filepath)
                            indexed_time = datetime.fromisoformat(existing[0]).timestamp()
                            if file_mtime < indexed_time:
                                continue
                            else:
                                # Re-index
                                conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                                conn.execute("DELETE FROM embeddings WHERE doc_id = ?", (doc_id,))
                                updated += 1
                    
                    # Read content
                    with open(filepath, encoding="utf-8") as f:
                        content = f.read()
                    
                    title = fname.replace(".md", "").replace("-", " ").replace("_", " ").title()
                    
                    # Store document
                    conn.execute("""
                        INSERT OR REPLACE INTO documents (id, title, content, source_type, source_id, metadata)
                        VALUES (?, ?, ?, 'vault', ?, ?)
                    """, (doc_id, title, content[:5000], fname, json.dumps({
                        "layer": layer,
                        "file": fname,
                        "size": len(content),
                    })))
                    
                    # Store embedding
                    vector = self._embed(title + " " + content[:1000])
                    conn.execute("""
                        INSERT OR REPLACE INTO embeddings (doc_id, vector, dimensions)
                        VALUES (?, ?, ?)
                    """, (doc_id, json.dumps(vector), len(vector)))
                    
                    if not force or updated == 0:
                        indexed += 1
                    
                except Exception as e:
                    errors += 1
        
        conn.commit()
        conn.close()
        
        return {"indexed": indexed, "updated": updated, "errors": errors}
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search documents by cosine similarity."""
        query_vec = self._embed(query)
        
        conn = sqlite3.connect(self.db_path)
        # Use the existing FTS5 memories table or fallback to documents
        rows = conn.execute("""
            SELECT id, content as title, content, '{}' as metadata, NULL as vector
            FROM memories
        """).fetchall()
        
        # Also check documents table
        try:
            doc_rows = conn.execute("""
                SELECT d.id, d.title, d.content, d.metadata, e.vector
                FROM documents d
                LEFT JOIN embeddings e ON d.id = e.memory_id
            """).fetchall()
            if doc_rows:
                rows = doc_rows
        except Exception:
            from aeryn_core.utils.logger import log_exception
            log_exception(e, context=f"{__name__}")
            pass
        
        conn.close()
        
        results = []
        for row in rows:
            try:
                doc_vec = json.loads(row[4])
                score = self._cosine(query_vec, doc_vec)
                results.append({
                    "id": row[0],
                    "title": row[1],
                    "content": row[2][:500],
                    "metadata": json.loads(row[3]),
                    "score": score,
                })
            except Exception:
                from aeryn_core.utils.logger import log_exception
                log_exception(e, context=f"{__name__}")
                pass
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def _cosine(self, a: List[float], b: List[float]) -> float:
        """Cosine similarity between two vectors."""
        dot = sum(x*y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x*x for x in a))
        mag_b = math.sqrt(sum(x*x for x in b))
        if mag_a * mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)
    
    def get_stats(self) -> Dict:
        """Get indexing statistics."""
        conn = sqlite3.connect(self.db_path)
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        embedding_count = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        last_indexed = conn.execute(
            "SELECT MAX(indexed_at) FROM documents"
        ).fetchone()[0]
        conn.close()
        
        return {
            "documents": doc_count,
            "embeddings": embedding_count,
            "last_indexed": last_indexed,
        }


# ── Singleton ─────────────────────────────────

_indexer: Optional[SemanticIndexer] = None

def get_semantic_indexer() -> SemanticIndexer:
    global _indexer
    if _indexer is None:
        _indexer = SemanticIndexer()
    return _indexer


if __name__ == "__main__":
    indexer = get_semantic_indexer()
    print("=== Semantic Search Indexer ===")
    
    # Index vault
    result = indexer.index_vault()
    print(f"Indexed: {result['indexed']}, Updated: {result['updated']}, Errors: {result['errors']}")
    
    # Stats
    stats = indexer.get_stats()
    print(f"Total documents: {stats['documents']}")
    
    # Test search
    results = indexer.search("aeryn development")
    print(f"Search results: {len(results)}")
    for r in results[:3]:
        print(f"  {r['title'][:50]} (score: {r['score']:.3f})")
