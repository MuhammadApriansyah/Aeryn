#!/usr/bin/env python3
"""V39.76 — MCP Server: Expose Aeryn tools to Claude Code, Codex, Cursor, etc.

Aeryn becomes a platform via MCP (Model Context Protocol).
Any MCP-compatible client can use Aeryn's tools:
- Claude Code
- OpenAI Codex
- Cursor
- Gemini CLI
- Cline
- And 50+ other tools

Usage:
  python aeryn_core/mcp_server.py              # stdio mode (for CLI tools)
  python aeryn_core/mcp_server.py --http 3011  # HTTP mode (for web clients)
"""

import os
import sys
import json
import asyncio
import argparse
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.server.sse import SseServerTransport
    from mcp.types import Tool, TextContent, Resource, ResourceTemplate
    from mcp.client.streamable_http import streamablehttp_client
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

from aeryn_core.safety.safety_engine import get_safety_engine, sanitize_output, check_path
from aeryn_core.utils.adapters import get_active_adapter, render_adapter_context
from aeryn_core.reasoning.reasoning_style import needs_research
from aeryn_core.memory.vault import AerynVault, VaultEntry, LAYER_WIKI
from aeryn_core.memory.social_memory import SocialMemory
from aeryn_core.database.shared_db import get_shared_db
from aeryn_core.database.semantic_search import get_semantic_search
from aeryn_core.utils.structured_output import StructuredOutput
from aeryn_core.reasoning.context_specialization import ContextBuilder
from aeryn_core.utils.config import ensure_dirs

# ── Tool Implementations ────────────────────────────────────────

class AerynToolHandler:
    """Handler for all Aeryn tools exposed via MCP."""
    
    def __init__(self):
        self.eng = get_safety_engine()
        self.vault = AerynVault()
        self.sm = SocialMemory()
        self.search = get_semantic_search()
        self.db = get_shared_db()
        self.ctx_builder = ContextBuilder()
    
    def safety_check(self, text: str) -> Optional[str]:
        """Run safety check, return error message if blocked."""
        result = self.eng.check_input(text)
        if not result.safe:
            return f"Blocked: {result.reason}. Fallback: {result.fallback}"
        return None
    
    # ── Information Tools ─────────────────────────────────────────
    
    def web_search(self, query: str) -> str:
        """Search the web for information."""
        error = self.safety_check(query)
        if error:
            return json.dumps({"ok": False, "error": error})
        
        try:
            import urllib.request
            import urllib.parse
            search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="replace")
                results = []
                for match in __import__('re').finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html):
                    url, title = match.groups()
                    title = __import__('re').sub(r'<[^>]+>', '', title)
                    results.append({"title": title[:100], "url": url[:200]})
                    if len(results) >= 5:
                        break
                return json.dumps({"ok": True, "results": results, "query": query}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    
    def web_read(self, url: str) -> str:
        """Read content from a URL."""
        error = self.safety_check(url)
        if error:
            return json.dumps({"ok": False, "error": error})
        
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                text = __import__('re').sub(r'<script[^>]*>.*?</script>', '', content, flags=__import__('re').DOTALL | __import__('re').I)
                text = __import__('re').sub(r'<style[^>]*>.*?</style>', '', text, flags=__import__('re').DOTALL | __import__('re').I)
                text = __import__('re').sub(r'<[^>]+>', ' ', text)
                text = __import__('re').sub(r'\s+', ' ', text).strip()
                return json.dumps({"ok": True, "content": text[:5000], "url": url}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    
    # ── Memory Tools ─────────────────────────────────────────────
    
    def memory_search(self, query: str, limit: int = 5) -> str:
        """Search memories using hybrid search (keyword + semantic)."""
        try:
            results = self.search.search(query, limit=limit)
            return json.dumps({"ok": True, "results": results, "count": len(results)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    
    def vault_read(self, query: str = "", layer: str = "Wiki", limit: int = 5) -> str:
        """Read entries from the vault."""
        try:
            results = self.vault.search(query, layer=layer, limit=limit)
            return json.dumps({"ok": True, "results": results, "count": len(results)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    
    def vault_write(self, title: str, body: str, layer: str = "Wiki", tags: str = "") -> str:
        """Write an entry to the vault."""
        error = self.safety_check(body)
        if error:
            return json.dumps({"ok": False, "error": error})
        
        try:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            entry = VaultEntry(layer=layer, title=title, body=body, tags=tag_list)
            path = self.vault.write(entry)
            
            # Also index in semantic search
            self.search.index_memory(
                memory_id=f"{layer}/{title}",
                title=title,
                content=body[:3000],
                source="vault",
                author="aeryn",
                metadata={"layer": layer, "tags": tag_list}
            )
            
            return json.dumps({"ok": True, "path": path}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    
    def social_memory_get(self, user_id: str) -> str:
        """Get social memory facts about a user."""
        try:
            facts = self.sm.get_facts(user_id)
            return json.dumps({"ok": True, "facts": facts, "count": len(facts)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    
    def social_memory_add(self, user_id: str, fact: str) -> str:
        """Add a fact to social memory."""
        try:
            added = self.sm.add_fact(user_id, fact)
            return json.dumps({"ok": True, "added": added}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    
    # ── Filesystem Tools ──────────────────────────────────────────
    
    def fs_read(self, path: str) -> str:
        """Read a file from the filesystem."""
        try:
            ok, reason = check_path(path, "read")
            if not ok:
                return json.dumps({"ok": False, "error": reason})
            
            with open(path, encoding="utf-8") as f:
                content = f.read()
            return json.dumps({"ok": True, "content": content[:10000], "path": path}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    
    def fs_write(self, path: str, content: str) -> str:
        """Write content to a file."""
        try:
            ok, reason = check_path(path, "write")
            if not ok:
                return json.dumps({"ok": False, "error": reason})
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return json.dumps({"ok": True, "path": path, "bytes_written": len(content)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    
    # ── Productivity Tools ────────────────────────────────────────
    
    def set_reminder(self, text: str, when: str) -> str:
        """Set a reminder for later."""
        try:
            rid = self.db.add_reminder(text, when, source="mcp")
            return json.dumps({"ok": True, "id": rid, "text": text, "when": when}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    
    def task_create(self, title: str, description: str = "", priority: int = 5) -> str:
        """Create a task."""
        try:
            tid = self.db.add_task(title, description, priority)
            return json.dumps({"ok": True, "id": tid, "title": title}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    
    def task_list(self) -> str:
        """List pending tasks."""
        try:
            tasks = self.db.get_pending_tasks()
            return json.dumps({"ok": True, "tasks": tasks, "count": len(tasks)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    
    # ── Cognitive Tools ───────────────────────────────────────────
    
    def context_compile(self, user_prompt: str, session_id: str = "default") -> str:
        """Compile cognitive context for a user message."""
        try:
            result = self.ctx_builder.compile_prompt(user_prompt, session_id)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})
    
    def safety_check_tool(self, text: str) -> str:
        """Check if text passes safety checks."""
        result = self.eng.check_input(text)
        return json.dumps(result.to_dict(), ensure_ascii=False)
    
    def report_generate(self, title: str, format: str = "markdown") -> str:
        """Generate a structured report."""
        try:
            if format == "markdown":
                report = StructuredOutput.generate_daily_summary()
            elif format == "vault":
                report = StructuredOutput.generate_vault_index()
            elif format == "tasks":
                report = StructuredOutput.generate_task_report()
            else:
                report = StructuredOutput.generate_report(title, [{"heading": "Content", "content": "Generated by Aeryn"}])
            return json.dumps({"ok": True, "report": report[:5000], "format": format}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})


# ── MCP Server Setup ────────────────────────────────────────────

def create_mcp_server() -> 'Server':
    """Create and configure the MCP server."""
    if not HAS_MCP:
        raise ImportError("MCP SDK not installed. Run: pip install mcp")
    
    server = Server("aeryn")
    handler = AerynToolHandler()
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List all available tools."""
        return [
            Tool(
                name="web_search",
                description="Search the web for information",
                inputSchema={
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "Search query"}},
                    "required": ["query"]
                }
            ),
            Tool(
                name="web_read",
                description="Read content from a URL",
                inputSchema={
                    "type": "object",
                    "properties": {"url": {"type": "string", "description": "URL to read"}},
                    "required": ["url"]
                }
            ),
            Tool(
                name="memory_search",
                description="Search memories using hybrid search (keyword + semantic)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Max results (default 5)"}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="vault_read",
                description="Read entries from the vault",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query (empty for all)"},
                        "layer": {"type": "string", "description": "Vault layer (Wiki/Projects/Daily/etc)"},
                        "limit": {"type": "integer", "description": "Max results"}
                    }
                }
            ),
            Tool(
                name="vault_write",
                description="Write an entry to the vault",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Entry title"},
                        "body": {"type": "string", "description": "Entry content"},
                        "layer": {"type": "string", "description": "Vault layer (default Wiki)"},
                        "tags": {"type": "string", "description": "Comma-separated tags"}
                    },
                    "required": ["title", "body"]
                }
            ),
            Tool(
                name="social_memory_get",
                description="Get social memory facts about a user",
                inputSchema={
                    "type": "object",
                    "properties": {"user_id": {"type": "string", "description": "User identifier"}},
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="social_memory_add",
                description="Add a fact to social memory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "fact": {"type": "string", "description": "Fact to store"}
                    },
                    "required": ["user_id", "fact"]
                }
            ),
            Tool(
                name="fs_read",
                description="Read a file from the filesystem",
                inputSchema={
                    "type": "object",
                    "properties": {"path": {"type": "string", "description": "File path"}},
                    "required": ["path"]
                }
            ),
            Tool(
                name="fs_write",
                description="Write content to a file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "Content to write"}
                    },
                    "required": ["path", "content"]
                }
            ),
            Tool(
                name="set_reminder",
                description="Set a reminder for later (+5m, +2h, +1d, or ISO timestamp)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Reminder text"},
                        "when": {"type": "string", "description": "When (+5m, +2h, +1d, or ISO)"},
                    },
                    "required": ["text", "when"]
                }
            ),
            Tool(
                name="task_create",
                description="Create a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Task title"},
                        "description": {"type": "string", "description": "Task description"},
                        "priority": {"type": "integer", "description": "Priority 1-10 (default 5)"}
                    },
                    "required": ["title"]
                }
            ),
            Tool(
                name="task_list",
                description="List pending tasks",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="context_compile",
                description="Compile cognitive context for a user message",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_prompt": {"type": "string", "description": "User message"},
                        "session_id": {"type": "string", "description": "Session identifier"}
                    },
                    "required": ["user_prompt"]
                }
            ),
            Tool(
                name="safety_check",
                description="Check if text passes safety checks",
                inputSchema={
                    "type": "object",
                    "properties": {"text": {"type": "string", "description": "Text to check"}},
                    "required": ["text"]
                }
            ),
            Tool(
                name="report_generate",
                description="Generate a structured report (daily/vault/tasks)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Report title"},
                        "format": {"type": "string", "description": "Format: markdown/vault/tasks"}
                    },
                    "required": ["title"]
                }
            ),
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> List[TextContent]:
        """Handle tool calls."""
        try:
            if name == "web_search":
                result = handler.web_search(arguments["query"])
            elif name == "web_read":
                result = handler.web_read(arguments["url"])
            elif name == "memory_search":
                result = handler.memory_search(arguments["query"], arguments.get("limit", 5))
            elif name == "vault_read":
                result = handler.vault_read(arguments.get("query", ""), arguments.get("layer", "Wiki"), arguments.get("limit", 5))
            elif name == "vault_write":
                result = handler.vault_write(arguments["title"], arguments["body"], arguments.get("layer", "Wiki"), arguments.get("tags", ""))
            elif name == "social_memory_get":
                result = handler.social_memory_get(arguments["user_id"])
            elif name == "social_memory_add":
                result = handler.social_memory_add(arguments["user_id"], arguments["fact"])
            elif name == "fs_read":
                result = handler.fs_read(arguments["path"])
            elif name == "fs_write":
                result = handler.fs_write(arguments["path"], arguments["content"])
            elif name == "set_reminder":
                result = handler.set_reminder(arguments["text"], arguments["when"])
            elif name == "task_create":
                result = handler.task_create(arguments["title"], arguments.get("description", ""), arguments.get("priority", 5))
            elif name == "task_list":
                result = handler.task_list()
            elif name == "context_compile":
                result = handler.context_compile(arguments["user_prompt"], arguments.get("session_id", "default"))
            elif name == "safety_check":
                result = handler.safety_check_tool(arguments["text"])
            elif name == "report_generate":
                result = handler.report_generate(arguments["title"], arguments.get("format", "markdown"))
            else:
                result = json.dumps({"ok": False, "error": f"Unknown tool: {name}"})
            
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"ok": False, "error": str(e)}))]
    
    return server


async def run_stdio():
    """Run MCP server in stdio mode (for CLI tools like Claude Code)."""
    server = create_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def run_http(port: int = 3011):
    """Run MCP server in HTTP mode (for web clients)."""
    from starlette.applications import Starlette
    from starlette.routing import Mount
    from starlette.responses import JSONResponse
    
    server = create_mcp_server()
    transport = SseServerTransport("/mcp/messages")
    
    async def handle_mcp(request):
        await transport.handle_post_message(request)
        return JSONResponse({"ok": True})
    
    app = Starlette(
        routes=[
            Mount("/mcp", app=handle_mcp),
        ]
    )
    
    import uvicorn
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info")
    server_uv = uvicorn.Server(config)
    await server_uv.serve()


if __name__ == "__main__":
    ensure_dirs()
    parser = argparse.ArgumentParser(description="Aeryn MCP Server")
    parser.add_argument("--http", type=int, help="Run in HTTP mode on specified port")
    args = parser.parse_args()
    
    if args.http:
        asyncio.run(run_http(args.http))
    else:
        asyncio.run(run_stdio())
