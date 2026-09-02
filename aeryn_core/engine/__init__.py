"""Aeryn Engine — Python bindings via C API.

Loads the Rust shared library and exposes Python-friendly wrappers.
"""

import ctypes
import os
import subprocess
from pathlib import Path
from typing import List, Optional

# Try to find the Rust shared library
def _find_library() -> Optional[Path]:
    """Find the aeryn_engine shared library."""
    base = Path(__file__).parent.parent.parent.parent / "aeryn-engine"
    candidates = [
        base / "target" / "release" / "libaeryn_engine.so",
        base / "target" / "release" / "libaeryn_engine.dylib",
        base / "libaeryn_engine.so",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _build_library() -> Path:
    """Build the Rust library if not found."""
    base = Path(__file__).parent.parent.parent.parent / "aeryn-engine"
    print("Building aeryn-engine...")
    subprocess.run(
        ["cargo", "build", "--release"],
        cwd=base,
        check=True,
    )
    lib = base / "target" / "release" / "libaeryn_engine.so"
    if not lib.exists():
        raise RuntimeError("Failed to build aeryn-engine")
    return lib


# Load the library
_lib_path = _find_library()
if _lib_path is None:
    _lib_path = _build_library()

_lib = ctypes.CDLL(str(_lib_path))

# Define function signatures
_lib.cosine_similarity.argtypes = [
    ctypes.POINTER(ctypes.c_float),
    ctypes.POINTER(ctypes.c_float),
    ctypes.c_size_t,
]
_lib.cosine_similarity.restype = ctypes.c_float

_lib.hash_text.argtypes = [ctypes.c_char_p]
_lib.hash_text.restype = ctypes.c_char_p

_lib.free_string.argtypes = [ctypes.c_char_p]
_lib.free_string.restype = None


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        return 0.0
    arr_a = (ctypes.c_float * len(a))(*a)
    arr_b = (ctypes.c_float * len(b))(*b)
    return _lib.cosine_similarity(arr_a, arr_b, len(a))


def hash_text(text: str) -> str:
    """Compute SHA-256 hash of a string."""
    result = _lib.hash_text(text.encode("utf-8"))
    if result is None:
        return ""
    return result.decode("utf-8")


class VectorStore:
    """Simple vector store using Rust cosine similarity."""
    
    def __init__(self, dimensions: int):
        self.dimensions = dimensions
        self._vectors = {}
    
    def add(self, id: str, vector: List[float], metadata: Optional[dict] = None):
        if len(vector) != self.dimensions:
            raise ValueError(f"Dimension mismatch: expected {self.dimensions}, got {len(vector)}")
        self._vectors[id] = {
            "vector": vector,
            "metadata": metadata or {},
        }
    
    def search(self, query: List[float], k: int = 5) -> List[dict]:
        if len(query) != self.dimensions:
            return []
        results = []
        for id, data in self._vectors.items():
            score = cosine_similarity(query, data["vector"])
            results.append({
                "id": id,
                "score": score,
                "metadata": data["metadata"],
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]
    
    def len(self) -> int:
        return len(self._vectors)
    
    def is_empty(self) -> bool:
        return len(self._vectors) == 0


class TextSplitter:
    """Text splitter with overlap."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split(self, text: str) -> List[str]:
        if not text:
            return []
        chars = list(text)
        chunks = []
        start = 0
        while start < len(chars):
            end = min(start + self.chunk_size, len(chars))
            chunk = "".join(chars[start:end])
            chunks.append(chunk)
            if end >= len(chars):
                break
            start += self.chunk_size - self.chunk_overlap
        return chunks


class Tokenizer:
    """Simple tokenizer."""
    
    def __init__(self):
        self.stopwords = set()
    
    def tokenize(self, text: str) -> List[str]:
        return text.lower().split()
    
    def count_tokens(self, text: str) -> int:
        return len(self.tokenize(text))


if __name__ == "__main__":
    print("🦀 Aeryn Engine Python Wrapper")
    print("=" * 40)
    
    # Test cosine similarity
    a = [1.0, 2.0, 3.0]
    b = [1.0, 2.0, 3.0]
    sim = cosine_similarity(a, b)
    print(f"Cosine similarity: {sim:.4f}")
    
    # Test hash
    hash1 = hash_text("Hello World")
    print(f"Hash: {hash1}")
    
    # Test vector store
    store = VectorStore(3)
    store.add("a", [1.0, 0.0, 0.0])
    store.add("b", [0.0, 1.0, 0.0])
    store.add("c", [0.5, 0.5, 0.0])
    
    results = store.search([1.0, 0.0, 0.0], 2)
    print(f"\nSearch results:")
    for r in results:
        print(f"  {r['id']}: {r['score']:.4f}")
    
    print("\n✅ All working!")
