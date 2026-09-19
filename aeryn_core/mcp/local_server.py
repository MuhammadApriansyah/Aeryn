#!/usr/bin/env python3
"""V61.4 — FW3: MCP local server (FastMCP, official SDK).

Serves Aeryn's real capabilities as MCP tools (streamable-http).
Tools: battery, memory_search, graph_status, pitfall_search, redis_stats.
Run standalone: python aeryn_core/mcp/local_server.py  (atau via `mcp run`).
Real APIs only — no test doubles.
"""

import os
import sys
import json
import asyncio
import subprocess

REPO = os.environ.get(
    "AERYN_REPO",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."),
)
REPO = os.path.abspath(REPO)
# local_server.py = <repo>/aeryn_core/mcp/ → REPO = <repo>. FastMCP bisa
# mengganti cwd/module context — pastikan repo root importable.
if REPO not in sys.path:
    sys.path.insert(0, REPO)

HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")
os.environ.setdefault("MEMORY_LIBRARY", os.path.join(HOME, "hermes-memory-library"))
os.environ.setdefault(
    "MEMORY_GRAPH_DB", os.path.join(HOME, "hermes-memory-library", "memory_graph.db")
)

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("aeryn", host="127.0.0.1", port=8090)


@mcp.tool()
def battery() -> str:
    """Read device battery status (termux-api — real device sensor)."""
    try:
        out = subprocess.run(
            ["termux-battery-status"], capture_output=True, text=True, timeout=15
        )
        if out.returncode != 0 or not out.stdout.strip():
            return json.dumps({"ok": False, "error": "termux-api unavailable"})
        data = json.loads(out.stdout)
        return json.dumps({
            "ok": True,
            "percentage": data.get("percentage"),
            "status": data.get("status"),
            "temperature": data.get("temperature"),
            "technology": data.get("technology"),
        })
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


@mcp.tool()
def memory_search(query: str, limit: int = 5) -> str:
    """Search Aeryn's memory library (RAG hybrid keyword + embeddings)."""
    try:
        from aeryn_core.platform.internal_tools import tool_memory_search
        return json.dumps(tool_memory_search(query, limit))
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


@mcp.tool()
def graph_status() -> str:
    """Aeryn memory graph status (nodes/edges/mode)."""
    try:
        from aeryn_core.platform.internal_tools import tool_graph_status
        return json.dumps(tool_graph_status())
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


@mcp.tool()
def pitfall_search(query: str, limit: int = 5) -> str:
    """Search Aeryn's pitfalls DB (known bugs + fixes)."""
    try:
        from aeryn_core.platform.internal_tools import tool_pitfall_search
        return json.dumps(tool_pitfall_search(query, limit))
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


@mcp.tool()
def redis_stats() -> str:
    """Aeryn redis job-queue stats (jobs/processing/dlq)."""
    try:
        from aeryn_core.platform.redis_queue import stats
        return json.dumps(stats())
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


@mcp.tool()
def api_health() -> str:
    """Aeryn API health check."""
    try:
        out = subprocess.run(
            ["curl", "-s", "-m", "5", "http://127.0.0.1:3010/health"],
            capture_output=True, text=True, timeout=8,
        )
        return out.stdout.strip() or json.dumps({"ok": False})
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


if __name__ == "__main__":
    # streamable-http transport (official MCP SDK)
    mcp.run(transport="streamable-http")
