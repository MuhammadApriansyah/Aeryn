#!/usr/bin/env python3
"""
V42.0 — MCP Protocol Client.
Connect to external MCP servers and invoke tools.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any


class MCPClient:
    """MCP Client — connect to external MCP servers."""
    
    def __init__(self, server_url: str, name: str = "external"):
        self.server_url = server_url
        self.name = name
        self._tools: List[Dict] = []
        self._resources: List[Dict] = []
        self._prompts: List[Dict] = []
    
    def discover(self) -> Dict:
        """Discover tools, resources, prompts from MCP server."""
        try:
            tools = self._get("/tools")
            resources = self._get("/resources")
            prompts = self._get("/prompts")
            
            self._tools = tools.get("tools", [])
            self._resources = resources.get("resources", [])
            self._prompts = prompts.get("prompts", [])
            
            return {
                "tools": len(self._tools),
                "resources": len(self._resources),
                "prompts": len(self._prompts),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get(self, path: str) -> Dict:
        """GET request to MCP server."""
        try:
            req = urllib.request.Request(f"{self.server_url}{path}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, OSError):
            return {}
    
    def call_tool(self, tool_name: str, args: Dict) -> Dict:
        """Call a tool on the MCP server."""
        try:
            data = json.dumps({"name": tool_name, "arguments": args}).encode()
            req = urllib.request.Request(
                f"{self.server_url}/tools/call",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}
    
    def list_tools(self) -> List[Dict]:
        return self._tools
    
    def list_resources(self) -> List[Dict]:
        return self._resources
    
    def list_prompts(self) -> List[Dict]:
        return self._prompts


class MCPRegistry:
    """Registry of MCP server connections."""
    
    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}
    
    def register(self, name: str, url: str) -> MCPClient:
        client = MCPClient(url, name)
        self._clients[name] = client
        return client
    
    def get(self, name: str) -> Optional[MCPClient]:
        return self._clients.get(name)
    
    def list_servers(self) -> List[str]:
        return list(self._clients.keys())
    
    def discover_all(self) -> Dict:
        results = {}
        for name, client in self._clients.items():
            results[name] = client.discover()
        return results


mcp_registry = MCPRegistry()
