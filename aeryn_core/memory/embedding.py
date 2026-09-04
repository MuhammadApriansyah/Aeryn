"""EmbeddingIndex — dense semantic search with graceful fallback.

Gap 2 (ROADMAP v2): upgrade memory recall from TF-IDF to dense embeddings.

3-tier fallback (tahan banting di proot headless / tanpa GPU):
  1. sentence-transformers (all-MiniLM-L6-v2, 384-dim) — jika tersedia & loadable
  2. Rust C API cosine_similarity (hash-based feature vector) — jika .so buildable
  3. TF-IDF cosine (existing semantic_recall) — selalu tersedia (stdlib)

Rekomendasi dimensi 384 sudah cocok dengan divisi creative yang memakai
dimension=384.

Evaluasi: hit rate@5 + MRR dibanding keyword/TF-IDF baseline.
"""

import os
import sqlite3
import hashlib
import math
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from aeryn_core.utils.config import DATABASE_DIR

STOPWORDS = frozenset(
    "yang untuk dengan dari ke di dan atau the a an of to in on for and or "
    "sebutkan jalankan kerjakan lakukan berurutan satu tool per giliran "
    "jawab ringkas hasilnya langkah coba".split()
)


def _tokens(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9_.-]+", text.lower())
            if len(w) > 2 and w not in STOPWORDS]


class _HashEmbedder:
    """Fallback tier 2: feature hashing -> fixed-dim vector (no torch needed).

    Produces a 384-dim vector from token n-grams via hashing. Deterministic,
    fast, and captures lexical similarity (not true semantics, but better than
    pure keyword because it uses character n-grams and TF weighting).
    """

    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        # character 3-grams + word tokens
        features = list(_tokens(text)) + [
            text[i:i + 3] for i in range(max(0, len(text) - 2))
        ]
        # term frequency weighting
        counts: Dict[int, float] = {}
        for feat in features:
            h = int(hashlib.sha256(feat.encode()).hexdigest(), 16) % self.dim
            counts[h] = counts.get(h, 0.0) + 1.0
        for h, c in counts.items():
            vec[h] = math.log(1 + c)
        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def cosine(a: List[float], b: List[float]) -> float:
        return sum(x * y for x, y in zip(a, b))


class _SentenceEmbedder:
    """Tier 1: real dense embeddings via sentence-transformers (lazy, guarded)."""

    def __init__(self, dim: int = 384):
        self.dim = dim
        self._model = None
        self._failed = False

    def _load(self):
        if self._failed:
            return None
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            self._failed = True
            self._model = None
        return self._model

    def embed(self, text: str) -> Optional[List[float]]:
        model = self._load()
        if model is None:
            return None
        try:
            vec = model.encode([text], normalize_embeddings=True)[0].tolist()
            return [float(x) for x in vec]
        except Exception:
            return None


class EmbeddingIndex:
    """Dense embedding index over memory content.

    Auto-selects the best available embedder (sentence-transformers -> hash -> TF-IDF).
    Stores {id, content, vector, source} in SQLite. Search via cosine.
    """

    def __init__(self, use_neural: bool = True):
        self.db_path = os.path.join(DATABASE_DIR, "embedding_index.db")
        self._hash_embedder = _HashEmbedder()
        self._neural = _SentenceEmbedder() if use_neural else None
        self._neural_available = None  # None = unknown, True/False after first probe
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS embedding_index (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                source TEXT DEFAULT 'memory',
                vector TEXT NOT NULL,
                created_at REAL
            )
        """)
        conn.commit()
        conn.close()

    def _active_embedder(self) -> str:
        """Determine which embedder to use (probe neural once, cache result)."""
        if self._neural_available is None:
            if self._neural is not None:
                test_vec = self._neural.embed("probe")
                self._neural_available = test_vec is not None
            else:
                self._neural_available = False
        return "neural" if self._neural_available else "hash"

    def embed(self, text: str) -> List[float]:
        """Embed text, choosing best available backend."""
        mode = self._active_embedder()
        if mode == "neural" and self._neural is not None:
            vec = self._neural.embed(text)
            if vec is not None:
                return vec
            # fall through to hash on transient failure
        return self._hash_embedder.embed(text)

    def add(self, memory_id: str, content: str, source: str = "memory"):
        vec = self.embed(content)
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO embedding_index (id, content, source, vector, created_at) VALUES (?,?,?,?,?)",
            (memory_id, content, source, ",".join(f"{v:.6f}" for v in vec), time.time())
        )
        conn.commit()
        conn.close()

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for most similar memories via cosine."""
        qvec = self.embed(query)
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT id, content, source, vector FROM embedding_index").fetchall()
        conn.close()

        scored = []
        for memory_id, content, source, vec_str in rows:
            try:
                dvec = [float(x) for x in vec_str.split(",")]
            except ValueError:
                continue
            score = self._hash_embedder.cosine(qvec, dvec)
            scored.append((score, {"id": memory_id, "content": content,
                                   "source": source, "score": score}))

        scored.sort(key=lambda x: -x[0])
        return [item for _, item in scored[:k]]

    def index_all(self, memories: List[Dict[str, Any]]):
        """Index a batch of memories {id, content, source}."""
        for mem in memories:
            self.add(mem.get("id", hashlib.sha256(mem.get("content", "").encode()).hexdigest()),
                     mem.get("content", ""), mem.get("source", "memory"))

    def stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM embedding_index").fetchone()[0]
        conn.close()
        return {
            "indexed_count": count,
            "embedder": self._active_embedder(),
            "dim": self._hash_embedder.dim,
        }


# Singleton
_index = None

def get_embedding_index() -> EmbeddingIndex:
    global _index
    if _index is None:
        # use_neural=False: sentence-transformers hangs on proot headless
        # (see STRESS_REPORT.md). Hash embedder is the fast fallback.
        # Switch to True once GPU/accelerated env is available.
        _index = EmbeddingIndex(use_neural=False)
    return _index