"""Tool Registry — dynamic tool registration and invocation."""

from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
import json


@dataclass
class Tool:
    """Represents a callable tool."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    handler: Callable
    is_async: bool = False
    
    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


class ToolRegistry:
    """Register and invoke tools dynamically."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, name: str, description: str, parameters: Dict[str, Any], handler: Callable, is_async: bool = False):
        """Register a tool."""
        self._tools[name] = Tool(name, description, parameters, handler, is_async)
    
    def unregister(self, name: str):
        """Unregister a tool."""
        self._tools.pop(name, None)
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[Tool]:
        """List all registered tools."""
        return list(self._tools.values())
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas in OpenAI format."""
        return [t.to_openai_schema() for t in self._tools.values()]
    
    async def call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name with arguments."""
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Tool '{name}' not found"}
        
        try:
            if tool.is_async:
                result = await tool.handler(**arguments)
            else:
                result = tool.handler(**arguments)
            return {"result": result, "tool": name, "status": "ok"}
        except Exception as e:
            return {"error": str(e), "tool": name, "status": "error"}
    
    def call_sync(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool synchronously."""
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Tool '{name}' not found"}
        
        try:
            result = tool.handler(**arguments)
            return {"result": result, "tool": name, "status": "ok"}
        except Exception as e:
            return {"error": str(e), "tool": name, "status": "error"}


# Global registry instance
_registry = None

def get_tool_registry() -> ToolRegistry:
    """Get global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _register_core_tools(_registry)
    return _registry


def _register_core_tools(registry: ToolRegistry):
    """Register 5 core tools."""
    from aeryn_core.tools.bash import bash_tool
    from aeryn_core.tools.file_read import file_read_tool
    from aeryn_core.tools.file_write import file_write_tool
    from aeryn_core.tools.file_search import file_search_tool
    from aeryn_core.tools.web_search import web_search_tool
    
    registry.register(
        "bash",
        "Execute a shell command and return stdout/stderr",
        {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"},
            },
            "required": ["command"],
        },
        bash_tool.execute
    )
    
    registry.register(
        "file_read",
        "Read the contents of a file",
        {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
            },
            "required": ["path"],
        },
        file_read_tool.execute
    )
    
    registry.register(
        "file_write",
        "Write content to a file (creates or overwrites)",
        {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
        file_write_tool.execute
    )
    
    registry.register(
        "file_search",
        "Search for files by name pattern",
        {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern (e.g., *.py)"},
                "directory": {"type": "string", "description": "Directory to search (default: current)"},
            },
            "required": ["pattern"],
        },
        file_search_tool.execute
    )
    
    registry.register(
        "web_search",
        "Search the web for information",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results (default 5)"},
            },
            "required": ["query"],
        },
        web_search_tool.execute
    )
