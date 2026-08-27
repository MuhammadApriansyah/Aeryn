#!/usr/bin/env python3
"""V39.73 — Tool Schema Docs: Structured documentation for all tools.

Provides:
- Tool manifest (JSON schema for all available tools)
- Tool descriptions with parameters
- Usage examples
- Category grouping
"""

import os
import sys
import json
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TOOL_MANIFEST = {
    "version": "39.73",
    "tools": [
        {
            "name": "web_search",
            "category": "information",
            "description": "Search the web for information",
            "parameters": {
                "query": {"type": "string", "required": True, "description": "Search query"}
            },
            "example": {"tool": "web_search", "params": {"query": "latest AI frameworks 2024"}}
        },
        {
            "name": "web_read",
            "category": "information",
            "description": "Read content from a URL",
            "parameters": {
                "url": {"type": "string", "required": True, "description": "URL to read"}
            },
            "example": {"tool": "web_read", "params": {"url": "https://example.com"}}
        },
        {
            "name": "fs_read",
            "category": "filesystem",
            "description": "Read a file from filesystem",
            "parameters": {
                "path": {"type": "string", "required": True, "description": "File path"}
            },
            "example": {"tool": "fs_read", "params": {"path": "/home/sen/notes.txt"}}
        },
        {
            "name": "fs_write",
            "category": "filesystem",
            "description": "Write content to a file",
            "parameters": {
                "path": {"type": "string", "required": True, "description": "File path"},
                "content": {"type": "string", "required": True, "description": "Content to write"}
            },
            "example": {"tool": "fs_write", "params": {"path": "/tmp/test.txt", "content": "Hello"}}
        },
        {
            "name": "terminal",
            "category": "system",
            "description": "Run a terminal command (sandboxed)",
            "parameters": {
                "command": {"type": "string", "required": True, "description": "Command to execute"}
            },
            "example": {"tool": "terminal", "params": {"command": "ls -la /tmp"}}
        },
        {
            "name": "memory_search",
            "category": "memory",
            "description": "Search memories and vault entries",
            "parameters": {
                "query": {"type": "string", "required": True, "description": "Search query"}
            },
            "example": {"tool": "memory_search", "params": {"query": "docker setup"}}
        },
        {
            "name": "set_reminder",
            "category": "productivity",
            "description": "Set a reminder for later",
            "parameters": {
                "text": {"type": "string", "required": True, "description": "Reminder text"},
                "when": {"type": "string", "required": True, "description": "When (+5m, +2h, +1d, or ISO)"}
            },
            "example": {"tool": "set_reminder", "params": {"text": "Check server", "when": "+1h"}}
        },
        {
            "name": "context_compile",
            "category": "cognitive",
            "description": "Compile cognitive context for a user message",
            "parameters": {
                "user_prompt": {"type": "string", "required": True},
                "session_id": {"type": "string", "required": False}
            },
            "example": {"tool": "context_compile", "params": {"user_prompt": "hello"}}
        },
        {
            "name": "task_create",
            "category": "productivity",
            "description": "Create a long-horizon task",
            "parameters": {
                "title": {"type": "string", "required": True},
                "description": {"type": "string", "required": False},
                "priority": {"type": "integer", "required": False}
            },
            "example": {"tool": "task_create", "params": {"title": "Research AI", "priority": 8}}
        },
        {
            "name": "report_generate",
            "category": "output",
            "description": "Generate structured reports",
            "parameters": {
                "title": {"type": "string", "required": True},
                "format": {"type": "string", "required": False}
            },
            "example": {"tool": "report_generate", "params": {"title": "Daily Summary"}}
        }
    ]
}


def get_tool_manifest() -> dict:
    """Get the full tool manifest."""
    return TOOL_MANIFEST


def get_tool_schema(tool_name: str) -> Optional[dict]:
    """Get schema for a specific tool."""
    for tool in TOOL_MANIFEST["tools"]:
        if tool["name"] == tool_name:
            return tool
    return None


def get_tools_by_category(category: str) -> List[dict]:
    """Get all tools in a category."""
    return [t for t in TOOL_MANIFEST["tools"] if t["category"] == category]


def search_tools(query: str) -> List[dict]:
    """Search tools by name or description."""
    query_lower = query.lower()
    return [
        t for t in TOOL_MANIFEST["tools"]
        if query_lower in t["name"].lower() or query_lower in t["description"].lower()
    ]


def get_tool_doc(tool_name: str) -> str:
    """Get formatted documentation for a tool."""
    tool = get_tool_schema(tool_name)
    if not tool:
        return f"Tool '{tool_name}' not found"
    
    lines = [
        f"# {tool['name']}",
        f"",
        f"**Category:** {tool['category']}",
        f"",
        f"## Description",
        f"{tool['description']}",
        f"",
        f"## Parameters",
    ]
    
    for param_name, param_info in tool.get("parameters", {}).items():
        req = "required" if param_info.get("required") else "optional"
        lines.append(f"- `{param_name}` ({req}): {param_info.get('description', '')}")
    
    lines.extend([
        f"",
        f"## Example",
        f"```json",
        f"{json.dumps(tool.get('example', {}), indent=2)}",
        f"```"
    ])
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("=== Tool Schema Docs ===")
    manifest = get_tool_manifest()
    print(f"Total tools: {len(manifest['tools'])}")
    print(f"Categories: {set(t['category'] for t in manifest['tools'])}")
    
    print("\n--- web_search schema ---")
    print(json.dumps(get_tool_schema("web_search"), indent=2))
    
    print("\n--- Search 'memory' ---")
    for t in search_tools("memory"):
        print(f"  {t['name']}: {t['description']}")
    
    print("\n--- Tool doc ---")
    print(get_tool_doc("web_search"))
