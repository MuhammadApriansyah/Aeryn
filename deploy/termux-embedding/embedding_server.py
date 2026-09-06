#!/usr/bin/env python3
"""Embedding server — RUNS NATIVE on Termux (no proot) to serve neural embeddings.

Dependency-light: stdlib `http.server` + `sentence_transformers` ONLY.
No FastAPI/pydantic/starlette/uvicorn — those have broken wheels on Python 3.14
in Termux (see ROADMAP_V4.md pitfall). One endpoint is all we need.

Run on Termux (python3 = 3.14):
    HF_HUB_DISABLE_XET=1 python3 embedding_server.py   # listens 8081
    POST /embed  {"text": "..."}  ->  {"vector": [384], "model": "..."}
    GET  /health               ->  {"status": "ok"}

Aeryn (proot) calls this via aeryn_core/memory/embedding.py (neural tier).
"""

import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

MODEL_NAME = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")
PORT = int(os.environ.get("EMBED_PORT", "8081"))

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default logging noise

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._json({"status": "ok", "model": MODEL_NAME})
        else:
            self._json({"error": "not found"}, status=404)

    def do_POST(self):
        if self.path != "/embed":
            self._json({"error": "not found"}, status=404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            req = json.loads(raw.decode("utf-8"))
            text = req.get("text", "")
            if not text:
                self._json({"error": "empty text"}, status=400)
                return
            model = get_model()
            vec = model.encode([text], normalize_embeddings=True)[0].tolist()
            self._json({"vector": [float(x) for x in vec],
                        "dim": len(vec), "model": MODEL_NAME})
        except Exception as e:
            self._json({"error": f"{type(e).__name__}: {e}"}, status=500)


if __name__ == "__main__":
    print(f"[embedding_server] model={MODEL_NAME} port={PORT} (loading on first request)")
    srv = HTTPServer(("127.0.0.1", PORT), Handler)
    srv.serve_forever()