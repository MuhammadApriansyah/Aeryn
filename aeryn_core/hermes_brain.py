#!/usr/bin/env python3
"""
hermes_brain.py — V33 "Shared Brain": Aeryn membaca memori kolektif Hermes.

Tiga tool tier-safe yang menjembatani otak Aeryn ke knowledge base Hermes
(library RAG + graph + pitfalls). Semuanya read-only, tanpa network,
via CLI script ~/.hermes/scripts/ — satu sumber kebenaran untuk dua agen.

Prinsip Hermes: "extend, don't duplicate" — tidak ada memori kedua;
hanya jembatan.
"""
import os
import re
import subprocess

HERMES_SCRIPTS = os.path.expanduser("~/.hermes/scripts")
_PY = "python3"
_TIMEOUT = 30


def _run(script: str, *args: str) -> str:
    proc = subprocess.run(
        [_PY, os.path.join(HERMES_SCRIPTS, script), *args],
        capture_output=True, text=True, timeout=_TIMEOUT)
    if proc.returncode != 0:
        raise RuntimeError(f"{script} exit {proc.returncode}: {proc.stderr[:200]}")
    return proc.stdout


def _memory_search(query: str, top: int = 3):
    """Cari pengalaman/pengetahuan di library kolektif (RAG-lite)."""
    if not query or not query.strip():
        return {"results": [], "note": "query kosong"}
    try:
        # LLM kadang mengirim angka sebagai string ("top": "3")
        top_n = max(1, min(int(top), 10))
    except (TypeError, ValueError):
        top_n = 3
    out = _run("memory_library.py", "search", query.strip(), "--top", str(top_n))
    results = []
    for block in re.split(r"\n(?=### )", out):
        m = re.match(r"###\s+(\S+)\s+\[([^\]]+)\]\s+\(score ([\d.]+)\)", block)
        if not m:
            continue
        body = block[m.end():].strip()
        # baris pertama = judul, sisanya ringkasan
        lines = body.splitlines()
        title = lines[0].lstrip("# ").strip() if lines else ""
        summary = "\n".join(lines[1:]).strip()[:500]
        results.append({"id": m.group(1), "meta": m.group(2),
                        "score": float(m.group(3)),
                        "title": title, "summary": summary})
    return {"results": results}


def _graph_traverse(entity: str):
    """Telusuri relasi entitas di knowledge graph (tetangga + edge)."""
    if not entity or not entity.strip():
        return {"node": "", "edges": [], "note": "entity kosong"}
    out = _run("graph_rag.py", "traverse", entity.strip())
    lines = [ln.rstrip() for ln in out.splitlines() if ln.strip()]
    edges = []
    node = ""
    for ln in lines:
        e = re.match(r"\s*--(\w[\w_]*)--+>\s*(\S+)", ln)
        if e:
            edges.append({"relation": e.group(1), "target": e.group(2)})
        elif not node:
            node = ln.strip()
    return {"node": node, "edges": edges}


def _pitfall_search(symptom: str):
    """Cek pitfall tercatat sebelum debug ulang masalah yang sama."""
    if not symptom or not symptom.strip():
        return {"pitfalls": [], "note": "symptom kosong"}
    out = _run("pitfalls.py", "search", symptom.strip())
    pitfalls = []
    for block in re.split(r"\n(?=#\d+ \[)", out):
        m = re.match(r"#(\d+) \[([^\]]+)\]", block)
        if not m:
            continue
        def grab(label):
            mm = re.search(rf"{label}\s*:\s*(.+)", block)
            return mm.group(1).strip() if mm else ""
        pitfalls.append({"n": int(m.group(1)), "id": m.group(2),
                         "symptom": grab("symptom"),
                         "root_cause": grab("root cause"),
                         "fix": grab("fix")})
    return {"pitfalls": pitfalls}


MEMORY_SEARCH_SCHEMA = {
    "type": "function", "function": {"name": "memory_search",
    "description": ("Cari pengetahuan/pengalaman di memori kolektif "
                    "(library RAG lintas sesi). Untuk konteks project "
                    "dan keputusan lampau."),
    "parameters": {"type": "object", "properties": {
        "query": {"type": "string"},
        "top": {"type": "integer", "description": "jumlah hasil, default 3"}},
        "required": ["query"]}}}

GRAPH_TRAVERSE_SCHEMA = {
    "type": "function", "function": {"name": "graph_traverse",
    "description": ("Telusuri entitas di knowledge graph: tetangga dan "
                    "relasinya (belongs_to, evolved_into, builds_with...)."),
    "parameters": {"type": "object", "properties": {
        "entity": {"type": "string", "description": "nama node, mis. aeryn-core"}},
        "required": ["entity"]}}}

PITFALL_SEARCH_SCHEMA = {
    "type": "function", "function": {"name": "pitfall_search",
    "description": ("Cek pitfall/error yang pernah dicatat SEBELUM debug. "
                    "Selalu panggil ini dulu saat menemui error."),
    "parameters": {"type": "object", "properties": {
        "symptom": {"type": "string", "description": "gejala error, mis. SSL EOF"}},
        "required": ["symptom"]}}}


def register(registry):
    """Daftarkan ketiga tool ke ToolGraduationRegistry (tier safe)."""
    registry.register("memory_search", _memory_search, MEMORY_SEARCH_SCHEMA)
    registry.register("graph_traverse", _graph_traverse, GRAPH_TRAVERSE_SCHEMA)
    registry.register("pitfall_search", _pitfall_search, PITFALL_SEARCH_SCHEMA)
    return registry
