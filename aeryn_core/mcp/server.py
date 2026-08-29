#!/usr/bin/env python3
"""
V42.0 — MCP Protocol Server.
Provides tools, resources, and prompts to external MCP clients.
"""

import json
import sqlite3
import threading
import time
from typing import Dict, List, Any
from pathlib import Path

DATABASE_DIR = Path.home() / "aeryn-core-agent" / "Personalisasi" / "Database"
DB_PATH = DATABASE_DIR / "mcp_server.db"

class MCPServer:
    """MCP Server — serves tools, resources, prompts to external clients."""
    
    def __init__(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_tools (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    input_schema TEXT,
                    handler TEXT,
                    created_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_resources (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    resource_type TEXT,
                    config TEXT,
                    created_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mcp_prompts (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    template TEXT,
                    parameters TEXT,
                    created_at REAL
                )
            """)
            conn.commit()
            conn.close()
    
    def register_tool(self, name: str, description: str, input_schema: Dict, handler: str):
        """Register a tool for MCP clients."""
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("""
                INSERT OR REPLACE INTO mcp_tools (id, name, description, input_schema, handler, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, name, description, json.dumps(input_schema), handler, time.time()))
            conn.commit()
            conn.close()
    
    def list_tools(self) -> List[Dict]:
        """List all registered tools."""
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.execute("SELECT name, description, input_schema, handler FROM mcp_tools")
            tools = [
                {"name": r[0], "description": r[1], "input_schema": json.loads(r[2]), "handler": r[3]}
                for r in cursor.fetchall()
            ]
            conn.close()
        return tools
    
    def call_tool(self, name: str, args: Dict) -> Dict:
        """Call a registered tool."""
        tools = {t["name"]: t for t in self.list_tools()}
        if name not in tools:
            return {"error": f"Tool '{name}' not found"}
        
        tool = tools[name]
        return {
            "tool": name,
            "args": args,
            "result": f"Executed {tool['handler']} with {args}",
            "timestamp": time.time()
        }
    
    def register_resource(self, name: str, description: str, resource_type: str, config: Dict):
        """Register a resource for MCP clients."""
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("""
                INSERT OR REPLACE INTO mcp_resources (id, name, description, resource_type, config, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, name, description, resource_type, json.dumps(config), time.time()))
            conn.commit()
            conn.close()
    
    def list_resources(self) -> List[Dict]:
        """List all registered resources."""
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.execute("SELECT name, description, resource_type, config FROM mcp_resources")
            resources = [
                {"name": r[0], "description": r[1], "type": r[2], "config": json.loads(r[3])}
                for r in cursor.fetchall()
            ]
            conn.close()
        return resources
    
    def register_prompt(self, name: str, description: str, template: str, parameters: List[str]):
        """Register a prompt for MCP clients."""
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("""
                INSERT OR REPLACE INTO mcp_prompts (id, name, description, template, parameters, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, name, description, template, json.dumps(parameters), time.time()))
            conn.commit()
            conn.close()
    
    def list_prompts(self) -> List[Dict]:
        """List all registered prompts."""
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.execute("SELECT name, description, template, parameters FROM mcp_prompts")
            prompts = [
                {"name": r[0], "description": r[1], "template": r[2], "parameters": json.loads(r[3])}
                for r in cursor.fetchall()
            ]
            conn.close()
        return prompts


mcp_server = MCPServer()
