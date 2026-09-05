#!/usr/bin/env python3
"""Embedding server — runs NATIVE on Termux (no proot) to serve neural embeddings.

Proot headless hangs on `sentence_transformers` import (torch spawn / missing
accel). Termux native can load all-MiniLM-L6-v2 on CPU. This tiny FastAPI server
exposes a single endpoint Aeryn (proot) calls over HTTP.

Run on Termux:
    python embedding_server.py          # listens 127.0.0.1:8081
    POST /embed  {"text": "..."}  ->  {"vector": [384 floats], "model": "all-MiniLM-L6-v2"}

Aeryn side (proot) calls this via aeryn_core/memory/embedding.py (neural tier),
with hash-embedder as fallback when this service is down.
"""

import os
from typing import Optional

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise SystemExit(f"Missing deps. On Termux run: pip install fastapi uvicorn sentence-transformers\n{e}")

app = FastAPI(title="Aeryn Embedding Server (Termux native)")

MODEL_NAME = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")
_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
        _model.encode(["warmup"], normalize_embeddings=True)
    return _model


class EmbedRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/embed")
def embed(req: EmbedRequest):
    model = get_model()
    vec = model.encode([req.text], normalize_embeddings=True)[0].tolist()
    return {"vector": [float(x) for x in vec], "dim": len(vec), "model": MODEL_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("EMBED_PORT", "8081")))