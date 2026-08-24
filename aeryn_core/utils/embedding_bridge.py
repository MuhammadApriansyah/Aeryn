"""EmbeddingBridge — Generator vektor semantik tanpa dependensi berat.

Menggantikan fastembed (onnxruntime terlalu berat untuk proot ARM64).
Metode: character n-gram hashing (hashing vectorizer) → proyeksi deterministik
ke ruang dimensi-D, L2-normalized. Lexical-similarity yang layak untuk retrieval
memori percakapan, cepat, tanpa model eksternal, deterministik lintas-run.
"""
from __future__ import annotations

import hashlib
import math
import re

_TOKEN_RE = re.compile(r"[\w']+")
_NGRAM_RE = re.compile(r".{1,4}", re.UNICODE)


class HashingEmbedder:
    """Char n-gram hashing embedder. Deterministik, tanpa model eksternal."""

    def __init__(self, dimension: int = 384, ngram_size: int = 3):
        self.dimension = dimension
        self.ngram_size = ngram_size

    def _bucket(self, token: str) -> int:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "little") % self.dimension

    def _sign(self, token: str) -> float:
        # Simpan arah (bipolar) supaya distribusi tidak biased positif
        digest = hashlib.blake2b(("s:" + token).encode("utf-8"), digest_size=8).digest()
        return 1.0 if (int.from_bytes(digest, "little") & 1) else -1.0

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dimension
        clean = re.sub(r"\s+", " ", text.lower()).strip()
        tokens = _TOKEN_RE.findall(clean)

        features: list[str] = []
        for tok in tokens:
            features.append(tok)
            padded = f"<{tok}>"
            for i in range(len(padded) - self.ngram_size + 1):
                features.append(padded[i:i + self.ngram_size])

        for feat in features:
            idx = self._bucket(feat)
            vec[idx] += self._sign(feat)

        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [round(v / norm, 6) for v in vec]

    def embed_pair(self, a: str, b: str) -> float:
        """Cosine similarity — karena ternormalisasi L2, cukup dot product."""
        va, vb = self.embed(a), self.embed(b)
        return sum(x * y for x, y in zip(va, vb))
