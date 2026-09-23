#!/usr/bin/env python3
"""V62.10 — G3: embedder.py — semantic embeddings untuk memory_library.

Model all-MiniLM-L6-v2 (384-dim) via sentence-transformers — jalan DI DALAM
AlmaLinux glibc-worker via proot (wheel prebuilt, detik). Embeddings cache di
sqlite (memory library dir). Dipakai memory_library.search vector lane.
Real APIs only — no test doubles.
"""

import os
import sys
import json
import math
import hashlib

REPO = os.environ.get(
    "AERYN_REPO",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."),
)
REPO = os.path.abspath(REPO)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")
LIB = os.environ.get("MEMORY_LIBRARY", os.path.join(HOME, "hermes-memory-library"))
ALMA_ROOT = os.environ.get("AERYN_ALMA_ROOT", os.path.join(HOME, "almalinux"))
EMBED_DB = os.environ.get("AERYN_EMBED_DB", os.path.join(LIB, "embeddings.db"))
MODEL = os.environ.get("AERYN_EMBED_MODEL", "all-MiniLM-L6-v2")

_EMBED_CONN = None


def _conn():
    """Cache sqlite connection untuk embeddings cache."""
    global _EMBED_CONN
    if _EMBED_CONN is None:
        import sqlite3
        conn = sqlite3.connect(EMBED_DB)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS embeddings ("
            "text_hash TEXT PRIMARY KEY, method TEXT, vector BLOB, created_at REAL)"
        )
        conn.commit()
        _EMBED_CONN = conn
    return _EMBED_CONN


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:24]


def _entry_text(raw: str) -> str:
    """Extract embeddable text dari SKILL.md entry (frontmatter + body condense)."""
    lines = [l for l in raw.split("\n") if not l.startswith("```")][:60]
    return " ".join(lines)[:2000]


def _proot_embed(texts: list) -> dict:
    """Embed texts via sentence-transformers DI DALAM AlmaLinux (proot).

    Karena torch (2.1 GB) hanya ada di rootfs — embedding jalan via proot.
    Output: JSON via stdout.
    """
    import subprocess
    import tempfile

    # Tulis texts ke tmp file (avoid shell escaping)
    tmp_in = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(texts, tmp_in)
    tmp_in.close()

    cmd = (
        "python3.12 -c \""
        "import sys, json; "
        f"from sentence_transformers import SentenceTransformer; "
        f"m = SentenceTransformer('{MODEL}'); "
        "texts = json.load(open('" + tmp_in.name + "')); "
        "vecs = m.encode(texts).tolist(); "
        "print(json.dumps(vecs))\""
    )
    out = subprocess.run(
        [
            "env", "-u", "LD_LIBRARY_PATH", "LD_PRELOAD=",
            "proot", "-0", "-w", "/root",
            "-b", "/dev", "-b", "/proc", "-b", "/sys",
            "-b", f"{tmp_in.name}:{tmp_in.name}",
            "-r", ALMA_ROOT,
            "/usr/bin/env", "PATH=/usr/local/bin:/usr/bin:/bin",
            "sh", "-c", cmd,
        ],
        capture_output=True, text=True, timeout=300,
    )
    try:
        os.unlink(tmp_in.name)
    except OSError:
        pass
    if out.returncode != 0:
        raise RuntimeError(f"proot embed fail: {out.stderr[:200]}")
    # Parse JSON dari stdout (baris terakhir yang valid)
    for line in reversed(out.stdout.strip().split("\n")):
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            return {"vectors": json.loads(line), "method": f"st:{MODEL}"}
    raise RuntimeError("proot embed: no valid output")


def cosine(a: list, b: list) -> float:
    """Cosine similarity antara 2 vector."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def embed(query: str) -> tuple:
    """Embed satu query. Returns (vector, method).

    Cache: cek sqlite dulu — miss → ORT LOKAL (RM5, ~10ms tanpa proot)
    → fallback proot embed (batch of 1, 82s) bila ORT gagal.
    """
    h = _hash(query)
    conn = _conn()
    row = conn.execute("SELECT method, vector FROM embeddings WHERE text_hash=?", (h,)).fetchone()
    if row:
        return json.loads(row[1].decode()), row[0]
    # RM5: ORT lokal dulu (cepat, tanpa proot) — fallback proot bila gagal
    vec = None
    method = None
    try:
        from aeryn_core.memory_library.local_embedder import embed_local
        vec, method = embed_local(query)
    except Exception:
        vec = None  # ORT gagal (model belum ada / init error) → proot
    if vec is None:
        result = _proot_embed([query])
        vec = result["vectors"][0]
        method = result["method"]
    conn.execute(
        "INSERT OR REPLACE INTO embeddings (text_hash, method, vector, created_at) VALUES (?,?,?,?)",
        (h, method, json.dumps(vec).encode(), __import__("time").time()),
    )
    conn.commit()
    return vec, method


def embed_batch(texts: list) -> dict:
    """Embed batch texts (untuk index_build). Cache per-text."""
    conn = _conn()
    uncached = []
    for t in texts:
        h = _hash(t)
        row = conn.execute("SELECT 1 FROM embeddings WHERE text_hash=?", (h,)).fetchone()
        if not row:
            uncached.append(t)
    if uncached:
        result = _proot_embed(uncached)
        method = result["method"]
        import time as _time
        for t, vec in zip(uncached, result["vectors"]):
            conn.execute(
                "INSERT OR REPLACE INTO embeddings (text_hash, method, vector, created_at) VALUES (?,?,?,?)",
                (_hash(t), method, json.dumps(vec).encode(), _time.time()),
            )
        conn.commit()
    return {"embedded": len(uncached), "total": len(texts), "method": f"st:{MODEL}"}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "redis watchdog"
    vec, method = embed(q)
    print(f"EMBED_OK dim={len(vec)} method={method}")
