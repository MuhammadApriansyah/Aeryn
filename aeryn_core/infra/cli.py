#!/usr/bin/env python3
"""
V44.0 — Agent CLI.
Command-line interface for creating and managing agents.
"""

import sys
import json
from typing import Dict, List, Optional

from .templates import template_registry, AgentTemplate
from ..mcp import mcp_server
from ..multi_agent import orchestrator


class AgentCLI:
    """Command-line interface for agent management."""
    
    def __init__(self):
        self.commands = {
            "create": self.cmd_create,
            "list": self.cmd_list,
            "run": self.cmd_run,
            "status": self.cmd_status,
            "templates": self.cmd_templates,
            "tools": self.cmd_tools,
            "help": self.cmd_help,
        }
    
    def run(self, args: List[str]):
        """Run CLI command."""
        if not args:
            self.cmd_help()
            return
        
        cmd = args[0]
        handler = self.commands.get(cmd, self.cmd_help)
        handler(args[1:])
    
    def cmd_create(self, args: List[str]):
        """Create a new agent: create <name> [--template <name>]"""
        if not args:
            print("Usage: aeryn create <agent_name> [--template <template_name>]")
            return
        
        name = args[0]
        template_name = None
        
        if "--template" in args:
            idx = args.index("--template")
            if idx + 1 < len(args):
                template_name = args[idx + 1]
        
        template = None
        if template_name:
            template = template_registry.get(template_name)
            if template:
                print(f"Using template: {template_name}")
                print(f"  System prompt: {template.system_prompt[:50]}...")
                print(f"  Tools: {', '.join(template.tools)}")
            else:
                print(f"Template '{template_name}' not found")
                return
        
        # Register as tool in MCP server
        mcp_server.register_tool(
            name=f"agent_{name}",
            description=f"Custom agent: {name}",
            input_schema={"type": "object", "properties": {"input": {"type": "string"}}},
            handler=f"agent_{name}_handler"
        )
        
        print(f"Agent '{name}' created successfully!")
    
    def cmd_list(self, args: List[str]):
        """List agents"""
        tools = mcp_server.list_tools()
        agent_tools = [t for t in tools if t["name"].startswith("agent_")]
        
        if not agent_tools:
            print("No agents found.")
            return
        
        print(f"\nAgents ({len(agent_tools)}):")
        for tool in agent_tools:
            print(f"  - {tool['name']}: {tool['description']}")
    
    def cmd_run(self, args: List[str]):
        """Run an agent: run <name> <input>"""
        if len(args) < 2:
            print("Usage: aeryn run <agent_name> <input>")
            return
        
        name = args[0]
        user_input = " ".join(args[1:])
        
        # Execute via MCP
        result = mcp_server.call_tool(f"agent_{name}", {"input": user_input})
        print(f"Result: {result.get('result', 'No result')}")
    
    def cmd_status(self, args: List[str]):
        """Show system status"""
        tools = mcp_server.list_tools()
        resources = mcp_server.list_resources()
        prompts = mcp_server.list_prompts()
        templates = template_registry.list_templates()
        
        print("\n=== Aeryn Agent Infrastructure ===")
        print(f"Tools: {len(tools)}")
        print(f"Resources: {len(resources)}")
        print(f"Prompts: {len(prompts)}")
        print(f"Templates: {len(templates)}")
    
    def cmd_templates(self, args: List[str]):
        """List available templates"""
        templates = template_registry.list_templates()
        
        print(f"\nAvailable Templates ({len(templates)}):")
        for t in templates:
            print(f"\n  [{t['category']}] {t['name']}")
            print(f"    {t['description']}")
            print(f"    Tools: {', '.join(t['tools'])}")
    
    def cmd_tools(self, args: List[str]):
        """List all registered tools"""
        tools = mcp_server.list_tools()
        
        print(f"\nRegistered Tools ({len(tools)}):")
        for t in tools:
            print(f"  - {t['name']}: {t['description']}")
    
    def cmd_help(self, args: List[str] = None):
        """Show help"""
        print("""
Aeryn Agent CLI
===============

Usage: aeryn <command> [options]

Commands:
  create <name> [--template <name>]  Create a new agent
  list                               List all agents
  run <name> <input>                 Run an agent
  status                             Show system status
  templates                          List available templates
  tools                              List registered tools
  help                               Show this help

Examples:
  aeryn create my_agent --template researcher
  aeryn run my_agent "Research AI safety"
  aeryn templates
        """)


agent_cli = AgentCLI()
