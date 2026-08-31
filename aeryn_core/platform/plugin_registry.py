#!/usr/bin/env python3
"""V61.1 — Dynamic Tool Routing (voltagent-style) for Aeryn.

PluginRegistry: register/unregister tools at runtime.
discover_tools(query): find tools by intent.
callTool(name, args): dynamic dispatch.
"""
import os
import re
import json
import logging
import importlib
import importlib.util
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger(__name__)


class ToolDefinition:
    """Metadata for a registered tool."""

    def __init__(self, name: str, description: str, handler: Callable,
                 parameters: Dict = None, tags: List[str] = None, version: str = "1.0"):
        self.name = name
        self.description = description
        self.handler = handler
        self.parameters = parameters or {}
        self.tags = tags or []
        self.version = version

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "tags": self.tags,
            "version": self.version,
        }


class PluginRegistry:
    """Dynamic tool registry — register, discover, dispatch."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, name: str, description: str, handler: Callable,
                 parameters: Dict = None, tags: List[str] = None, category: str = "general"):
        tool = ToolDefinition(name, description, handler, parameters, tags)
        self._tools[name] = tool
        self._categories.setdefault(category, []).append(name)
        logger.info(f"Registered tool: {name} (category: {category})")
        return tool

    def unregister(self, name: str) -> bool:
        tool = self._tools.pop(name, None)
        if tool:
            for cat, tools in self._categories.items():
                if name in tools:
                    tools.remove(name)
            return True
        return False

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self, category: str = None) -> List[Dict]:
        if category:
            names = self._categories.get(category, [])
            return [self._tools[n].to_dict() for n in names if n in self._tools]
        return [t.to_dict() for t in self._tools.values()]

    def discover_tools(self, query: str, limit: int = 5) -> List[Dict]:
        """Find tools matching a query (keyword + tag match)."""
        query_lower = query.lower()
        words = set(re.findall(r'\w+', query_lower))
        scored = []
        for tool in self._tools.values():
            score = 0
            # Name match
            if query_lower in tool.name.lower():
                score += 10
            # Description match
            desc_words = set(re.findall(r'\w+', tool.description.lower()))
            overlap = words & desc_words
            score += len(overlap) * 3
            # Tag match
            for tag in tool.tags:
                if tag.lower() in query_lower:
                    score += 5
            if score > 0:
                scored.append((score, tool))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t.to_dict() for _, t in scored[:limit]]

    def call_tool(self, name: str, **kwargs) -> Any:
        """Dynamic dispatch to tool handler."""
        tool = self._tools.get(name)
        if not tool:
            return {"ok": False, "error": f"Tool not found: {name}"}
        try:
            result = tool.handler(**kwargs)
            return result
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return {"ok": False, "error": str(e)}

    def load_plugin_from_file(self, path: str, name: str = None) -> Optional[str]:
        """Load a tool from a Python file dynamically."""
        try:
            plugin_name = name or os.path.basename(path).replace(".py", "")
            spec = importlib.util.spec_from_file_location(plugin_name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register"):
                module.register(self)
                return plugin_name
            logger.warning(f"Plugin {path} has no register() function")
            return None
        except Exception as e:
            logger.error(f"Failed to load plugin {path}: {e}")
            return None

    def load_plugins_from_dir(self, directory: str) -> List[str]:
        """Load all plugins from a directory."""
        loaded = []
        if not os.path.isdir(directory):
            return loaded
        for fname in os.listdir(directory):
            if fname.endswith(".py") and not fname.startswith("_"):
                path = os.path.join(directory, fname)
                name = self.load_plugin_from_file(path)
                if name:
                    loaded.append(name)
        return loaded

    def get_stats(self) -> Dict:
        return {
            "total_tools": len(self._tools),
            "categories": {k: len(v) for k, v in self._categories.items()},
        }


# Singleton
_registry = None

def get_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _register_builtin_tools(_registry)
    return _registry


def _register_builtin_tools(registry: PluginRegistry):
    """Register Aeryn's built-in tools."""
    # Lazy import to avoid DB connection at startup
    try:
        from aeryn_core.platform.tool_runtime import get_tool_runtime
        runtime = get_tool_runtime()
    except Exception:
        runtime = None

    def _safe_exec(tool_name, **kwargs):
        if runtime is None:
            return {"ok": False, "error": "Tool runtime unavailable"}
        return runtime.execute(tool_name, kwargs)

    registry.register(
        "fs_read", "Read file content",
        handler=lambda path, **kw: _safe_exec("fs_read", path=path),
        parameters={"type": "object", "properties": {"path": {"type": "string"}}},
        tags=["file", "read", "io"],
        category="filesystem"
    )
    registry.register(
        "fs_write", "Write content to file",
        handler=lambda path, content, **kw: _safe_exec("fs_write", path=path, content=content),
        parameters={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}},
        tags=["file", "write", "io"],
        category="filesystem"
    )
    registry.register(
        "fs_list", "List directory contents",
        handler=lambda path=".", **kw: _safe_exec("fs_list", path=path),
        parameters={"type": "object", "properties": {"path": {"type": "string"}}},
        tags=["file", "list", "directory"],
        category="filesystem"
    )
    registry.register(
        "terminal", "Execute shell command (sandboxed)",
        handler=lambda command, timeout=30, **kw: _safe_exec("terminal", command=command, timeout=timeout),
        parameters={"type": "object", "properties": {"command": {"type": "string"}, "timeout": {"type": "integer"}}},
        tags=["shell", "exec", "command"],
        category="system"
    )
    registry.register(
        "web_search", "Search the web",
        handler=lambda query, **kw: _safe_exec("web_search", query=query),
        parameters={"type": "object", "properties": {"query": {"type": "string"}}},
        tags=["web", "search", "internet"],
        category="web"
    )
    registry.register(
        "web_fetch", "Fetch URL content",
        handler=lambda url, **kw: _safe_exec("web_fetch", url=url),
        parameters={"type": "object", "properties": {"url": {"type": "string"}}},
        tags=["web", "fetch", "http"],
        category="web"
    )
    registry.register(
        "memory_search", "Search memory/vault",
        handler=lambda query, limit=5, **kw: _safe_exec("memory_search", query=query, limit=limit),
        parameters={"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}},
        tags=["memory", "search", "vault"],
        category="memory"
    )
