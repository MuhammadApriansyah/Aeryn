"""Aeryn Engine — Python bindings via C API.

Loads the Rust shared library and exposes Python-friendly wrappers.
"""

import ctypes
import os
import subprocess
from pathlib import Path
from typing import List, Optional

def _find_library() -> Optional[Path]:
    """Find the aeryn_engine shared library."""
    base = Path(os.path.expanduser("~")) / "aeryn-core-agent" / "aeryn-engine"
    candidates = [
        base / "target" / "release" / "libaeryn_engine.so",
        base / "libaeryn_engine.so",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _build_library() -> Path:
    """Build the Rust library if not found."""
    base = Path(os.path.expanduser("~")) / "aeryn-core-agent" / "aeryn-engine"
    print("Building aeryn-engine...")
    subprocess.run(["cargo", "build", "--release"], cwd=base, check=True)
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
_lib.cosine_similarity.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
_lib.cosine_similarity.restype = ctypes.c_float

_lib.euclidean_distance.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
_lib.euclidean_distance.restype = ctypes.c_float

_lib.hash_text.argtypes = [ctypes.c_char_p]
_lib.hash_text.restype = ctypes.c_char_p

_lib.free_string.argtypes = [ctypes.c_char_p]
_lib.free_string.restype = None

_lib.word_count.argtypes = [ctypes.c_char_p]
_lib.word_count.restype = ctypes.c_size_t

_lib.find_top_k.argtypes = [
    ctypes.POINTER(ctypes.c_float), ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_float), ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_float)
]
_lib.find_top_k.restype = ctypes.c_size_t


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors using Rust."""
    if len(a) != len(b):
        return 0.0
    arr_a = (ctypes.c_float * len(a))(*a)
    arr_b = (ctypes.c_float * len(b))(*b)
    return _lib.cosine_similarity(arr_a, arr_b, len(a))


def euclidean_distance(a: List[float], b: List[float]) -> float:
    """Compute Euclidean distance between two vectors using Rust."""
    if len(a) != len(b):
        return float('inf')
    arr_a = (ctypes.c_float * len(a))(*a)
    arr_b = (ctypes.c_float * len(b))(*b)
    return _lib.euclidean_distance(arr_a, arr_b, len(a))


def hash_text(text: str) -> str:
    """Compute SHA-256 hash of a string using Rust."""
    result = _lib.hash_text(text.encode("utf-8"))
    if result is None:
        return ""
    return result.decode("utf-8")


def word_count(text: str) -> int:
    """Count words in a string using Rust."""
    return _lib.word_count(text.encode("utf-8"))


def find_top_k(query: List[float], vectors: List[List[float]], k: int = 5) -> List[tuple]:
    """Find top k similar vectors using Rust."""
    if not vectors or not query:
        return []
    
    dim = len(query)
    num_vectors = len(vectors)
    
    # Flatten vectors
    flat_vectors = []
    for v in vectors:
        flat_vectors.extend(v)
    
    arr_query = (ctypes.c_float * len(query))(*query)
    arr_vectors = (ctypes.c_float * len(flat_vectors))(*flat_vectors)
    out_indices = (ctypes.c_size_t * k)()
    out_scores = (ctypes.c_float * k)()
    
    result_k = _lib.find_top_k(
        arr_query, len(query),
        arr_vectors, num_vectors, dim, k,
        out_indices, out_scores
    )
    
    results = []
    for i in range(result_k):
        results.append((out_indices[i], out_scores[i]))
    
    return results


class VectorStore:
    """Vector store using Rust cosine similarity."""
    
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
        
        vectors = [data["vector"] for data in self._vectors.values()]
        ids = list(self._vectors.keys())
        
        results = find_top_k(query, vectors, k)
        
        output = []
        for idx, score in results:
            output.append({
                "id": ids[idx],
                "score": score,
                "metadata": self._vectors[ids[idx]]["metadata"],
            })
        
        return output
    
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
