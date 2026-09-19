#!/data/data/com.termux/files/usr/bin/python3
"""V61.4 — FW1: Internal tools bridge (memory_search/graph_traverse/pitfall_search/battery).

Wraps CLI-style memory_library functions (stdout-printing) into structured
tool results for the plugin registry. Real APIs only — no test doubles.
"""

import os
import sys
import io
import contextlib
import subprocess
import json

REPO = os.environ.get(
    "AERYN_REPO",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."),
)
REPO = os.path.abspath(REPO)

# Memory library paths — env override wins (portable), else $HOME/hermes-memory-library
HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")
os.environ.setdefault("MEMORY_LIBRARY", os.path.join(HOME, "hermes-memory-library"))
os.environ.setdefault(
    "MEMORY_GRAPH_DB", os.path.join(HOME, "hermes-memory-library", "memory_graph.db")
)

if REPO not in sys.path:
    sys.path.insert(0, REPO)


def _capture(fn, *args, **kwargs) -> dict:
    """Run a stdout-printing function and capture its output as structured result."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            fn(*args, **kwargs)
        out = buf.getvalue().strip()
        ok = bool(out) and "no matches" not in out and "no pitfalls match" not in out
        return {"ok": ok, "output": out[:5000], "error": "" if ok else "no results"}
    except Exception as e:
        return {"ok": False, "output": buf.getvalue()[:2000], "error": str(e)}


def tool_memory_search(query: str, limit: int = 5) -> dict:
    """Search the memory library (RAG-style, hybrid keyword + embeddings)."""
    if not query:
        return {"ok": False, "output": "", "error": "query kosong"}
    from aeryn_core.memory_library import memory_library as ml

    return _capture(ml.search, query, top=limit)


def tool_graph_traverse(entity: str, depth: int = 2) -> dict:
    """Traverse the memory graph (nerve) around an entity."""
    if not entity:
        return {"ok": False, "output": "", "error": "entity kosong"}
    from aeryn_core.memory_library import graph_rag as gr

    return _capture(gr.cmd_traverse, entity, depth)


def tool_graph_status() -> dict:
    """Memory graph status: nodes/edges/mode."""
    from aeryn_core.memory_library import graph_rag as gr

    return _capture(gr.cmd_status)


def tool_pitfall_search(query: str, limit: int = 5) -> dict:
    """Search pitfalls DB (known bugs + fixes, jangan re-diagnose)."""
    if not query:
        return {"ok": False, "output": "", "error": "query kosong"}
    from aeryn_core.memory_library import pitfalls as pf

    return _capture(pf.search, query, limit)


def tool_battery() -> dict:
    """Read device battery status (termux-api — Aeryn punya akses tubuh HP)."""
    try:
        out = subprocess.run(
            ["termux-battery-status"], capture_output=True, text=True, timeout=15
        )
        if out.returncode != 0 or not out.stdout.strip():
            return {"ok": False, "output": "", "error": out.stderr.strip() or "termux-api unavailable"}
        data = json.loads(out.stdout)
        pct = data.get("percentage")
        status = data.get("status")
        return {
            "ok": True,
            "output": f"Baterai {pct}% ({status})",
            "error": "",
            "data": data,
        }
    except FileNotFoundError:
        return {"ok": False, "output": "", "error": "termux-battery-status tidak ada (pkg install termux-api)"}
    except Exception as e:
        return {"ok": False, "output": "", "error": str(e)}


def register(registry) -> None:
    """Register FW1 internal tools into the PluginRegistry."""
    registry.register(
        "memory_search",
        "Search memory library (RAG hybrid: keyword + embeddings, lintas-sesi)",
        handler=lambda query, limit=5, **kw: tool_memory_search(query, limit),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
        tags=["memory", "search", "rag", "vault"],
        category="memory",
    )
    registry.register(
        "graph_traverse",
        "Traverse memory graph (nerve 429 nodes) around an entity",
        handler=lambda entity, depth=2, **kw: tool_graph_traverse(entity, depth),
        parameters={
            "type": "object",
            "properties": {
                "entity": {"type": "string"},
                "depth": {"type": "integer"},
            },
            "required": ["entity"],
        },
        tags=["memory", "graph", "nerve"],
        category="memory",
    )
    registry.register(
        "graph_status",
        "Memory graph status (nodes/edges/mode)",
        handler=lambda **kw: tool_graph_status(),
        parameters={"type": "object", "properties": {}},
        tags=["memory", "graph", "status"],
        category="memory",
    )
    registry.register(
        "pitfall_search",
        "Search pitfalls DB (known bug patterns + fixes — jangan re-diagnose)",
        handler=lambda query, limit=5, **kw: tool_pitfall_search(query, limit),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
        tags=["debug", "pitfall", "memory"],
        category="memory",
    )
    registry.register(
        "battery",
        "Read device battery status (termux-api)",
        handler=lambda **kw: tool_battery(),
        parameters={"type": "object", "properties": {}},
        tags=["body", "battery", "device", "sensor"],
        category="body",
    )
