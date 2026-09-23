"""RM5: Local embedder — onnxruntime (Termux aarch64) tanpa proot.

Modul: aeryn_core/memory_library/local_embedder.py
- ORT InferenceSession (model.onnx 90MB all-MiniLM-L6-v2, quantizable)
- Tokenizer: tokenizers (HuggingFace Rust tokenizer) dari tokenizer.json
- Output: 384-dim mean-pooled embedding (sama dengan sentence-transformers)
- Fallback ke proot embedder bila ORT gagal (error handling eksplisit).

Real inference only — no test doubles: model.onnx nyata dijalankan.
"""

import json
import os
from typing import List, Optional, Tuple

MODEL_DIR = os.path.expanduser(
    "~/aeryn-core-agent/data/models")
MODEL_PATH = os.path.join(MODEL_DIR, "minilm.onnx")
TOKENIZER_PATH = os.path.join(MODEL_DIR, "tokenizer.json")

MAX_SEQ_LEN = 256  # all-MiniLM-L6-v2 default 256 word pieces

_session = None
_tokenizer = None
_init_error: Optional[str] = None


def _get_session():
    """ORT InferenceSession (lazy, cached)."""
    global _session, _init_error
    if _session is not None:
        return _session
    if _init_error is not None:
        raise RuntimeError(_init_error)
    if not os.path.exists(MODEL_PATH):
        _init_error = f"model.onnx tidak ada di {MODEL_PATH} — download dulu"
        raise RuntimeError(_init_error)
    try:
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.intra_op_num_threads = 2  # hemat CPU Termux (8 core dibagi service)
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        _session = ort.InferenceSession(MODEL_PATH, sess_options=so,
                                        providers=["CPUExecutionProvider"])
        return _session
    except Exception as e:
        _init_error = f"ORT init gagal: {str(e)[:200]}"
        raise RuntimeError(_init_error)


def _get_tokenizer():
    """HuggingFace Rust tokenizer (lazy, cached)."""
    global _tokenizer
    if _tokenizer is not None:
        return _tokenizer
    if not os.path.exists(TOKENIZER_PATH):
        raise RuntimeError(f"tokenizer.json tidak ada di {TOKENIZER_PATH}")
    from tokenizers import Tokenizer
    _tokenizer = Tokenizer.from_file(TOKENIZER_PATH)
    _tokenizer.enable_truncation(max_length=MAX_SEQ_LEN)
    _tokenizer.enable_padding(length=None)  # padding manual per batch
    return _tokenizer


def _mean_pool(token_embeddings, attention_mask) -> List[float]:
    """Mean pooling dengan attention mask (sama dengan sentence-transformers)."""
    mask = attention_mask
    summed = [0.0] * len(token_embeddings[0])
    total = 0.0
    for i, tok in enumerate(token_embeddings):
        w = mask[i]
        total += w
        for j, v in enumerate(tok):
            summed[j] += v * w
    if total == 0:
        total = 1.0
    return [v / total for v in summed]


def embed_local(text: str) -> Tuple[List[float], str]:
    """Embed satu teks via ORT lokal (tanpa proot). Returns (vector, method)."""
    sess = _get_session()
    tok = _get_tokenizer()
    enc = tok.encode(text)
    ids = enc.ids
    mask = enc.attention_mask
    inp = {
        "input_ids": [ids],
        "attention_mask": [mask],
        "token_type_ids": [[0] * len(ids)],
    }
    # Nama input dari session (model BERT punya 3 input)
    input_names = [i.name for i in sess.get_inputs()]
    feed = {k: v for k, v in inp.items() if k in input_names}
    out = sess.run(None, feed)
    # output shape (1, seq, 384) — token embeddings (float32 → float konversi)
    token_embeddings = out[0][0].tolist()
    vec = _mean_pool(token_embeddings, mask)
    return vec, "ort:all-MiniLM-L6-v2"


def is_available() -> bool:
    """Cek ORT lokal siap (model + tokenizer ada + session init OK)."""
    try:
        _get_session()
        _get_tokenizer()
        return True
    except Exception:
        return False


def availability_reason() -> str:
    """Alasan (error terakhir) — untuk diagnostics."""
    try:
        _get_session()
        _get_tokenizer()
        return "ok"
    except Exception as e:
        return str(e)[:200]
