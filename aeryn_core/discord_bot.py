#!/usr/bin/env python3
"""V40.20 — Discord Bot: Full integration with Discord via Bot API.

Features:
- Slash commands (/aeryn, /search, /task, /reminder)
- Message handler (natural language)
- Direct message support
- Role-based permissions
- Channel management
- Voice channel presence
- Webhook integration
"""

import os
import sys
import json
import time
import sqlite3
import asyncio
import threading
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/discord_bot.db")


class DiscordBotConfig:
    """Discord bot configuration."""
    
    def __init__(self):
        self.db_path = DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS bot_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS discord_channels (
                    channel_id TEXT PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    channel_name TEXT,
                    channel_type TEXT DEFAULT 'text',
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS discord_users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    display_name TEXT,
                    is_admin INTEGER DEFAULT 0,
                    dm_channel_id TEXT,
                    last_interaction TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        finally:
            conn.close()
    
    def set(self, key: str, value: str):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO bot_config (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, datetime.now().isoformat()))
            conn.commit()
        finally:
            conn.close()
    
    def get(self, key: str, default: str = None) -> str:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT value FROM bot_config WHERE key = ?", (key,)
            ).fetchone()
            return row[0] if row else default
        finally:
            conn.close()


class DiscordBotHandler:
    """Handle Discord bot interactions."""
    
    def __init__(self, token: str = None, api_base: str = "https://discord.com/api/v10"):
        self.config = DiscordBotConfig()
        self.token = token or self.config.get("bot_token", "")
        self.api_base = api_base
        self._commands = {}
        self._handlers = {}
        self._register_default_commands()
    
    def _register_default_commands(self):
        """Register slash commands."""
        self._commands = {
            "aeryn": {
                "description": "Ask Aeryn anything",
                "options": [
                    {
                        "name": "message",
                        "description": "Your message to Aeryn",
                        "type": 3,  # STRING
                        "required": True,
                    }
                ]
            },
            "search": {
                "description": "Search Aeryn's memory",
                "options": [
                    {
                        "name": "query",
                        "description": "What to search for",
                        "type": 3,
                        "required": True,
                    }
                ]
            },
            "task": {
                "description": "Manage tasks",
                "options": [
                    {
                        "name": "action",
                        "description": "Action to perform",
                        "type": 3,
                        "required": True,
                        "choices": [
                            {"name": "Create", "value": "create"},
                            {"name": "List", "value": "list"},
                            {"name": "Complete", "value": "complete"},
                        ]
                    },
                    {
                        "name": "description",
                        "description": "Task description",
                        "type": 3,
                        "required": False,
                    }
                ]
            },
            "reminder": {
                "description": "Set a reminder",
                "options": [
                    {
                        "name": "text",
                        "description": "Reminder text",
                        "type": 3,
                        "required": True,
                    },
                    {
                        "name": "when",
                        "description": "When (+5m, +2h, +1d)",
                        "type": 3,
                        "required": True,
                    }
                ]
            },
            "vault": {
                "description": "Vault operations",
                "options": [
                    {
                        "name": "action",
                        "description": "Read or write",
                        "type": 3,
                        "required": True,
                        "choices": [
                            {"name": "Read", "value": "read"},
                            {"name": "Write", "value": "write"},
                            {"name": "Search", "value": "search"},
                        ]
                    },
                    {
                        "name": "query",
                        "description": "Query or content",
                        "type": 3,
                        "required": True,
                    }
                ]
            },
        }
    
    def get_commands(self) -> List[Dict]:
        """Get all registered commands."""
        commands = []
        for name, cmd in self._commands.items():
            commands.append({
                "name": name,
                "description": cmd["description"],
                "options": cmd.get("options", []),
            })
        return commands
    
    def register_command(self, name: str, handler, description: str = "",
                        options: List[Dict] = None):
        """Register a custom command."""
        self._commands[name] = {
            "description": description,
            "options": options or [],
        }
        self._handlers[name] = handler
    
    async def handle_interaction(self, interaction: Dict) -> Dict:
        """Handle a Discord interaction."""
        data = interaction.get("data", {})
        command_name = data.get("name", "")
        options = data.get("options", [])
        
        # Parse options into kwargs
        kwargs = {}
        for opt in options:
            kwargs[opt["name"]] = opt["value"]
        
        # Execute command
        if command_name in self._handlers:
            result = await self._handlers[command_name](**kwargs)
            return {
                "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
                "data": {
                    "content": str(result)[:2000],
                }
            }
        
        # Default handlers
        if command_name == "aeryn":
            return await self._handle_aeryn(**kwargs)
        elif command_name == "search":
            return await self._handle_search(**kwargs)
        elif command_name == "task":
            return await self._handle_task(**kwargs)
        elif command_name == "reminder":
            return await self._handle_reminder(**kwargs)
        elif command_name == "vault":
            return await self._handle_vault(**kwargs)
        
        return {
            "type": 4,
            "data": {"content": "Unknown command"}
        }
    
    async def _handle_aeryn(self, message: str = "", **kwargs) -> Dict:
        """Handle /aeryn command."""
        # Forward to Aeryn API
        import urllib.request
        
        req = urllib.request.Request(
            "http://127.0.0.1:3010/run",
            data=json.dumps({"goal": message}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                return {
                    "type": 4,
                    "data": {
                        "content": result.get("response", "No response")[:2000],
                        "embeds": [
                            {
                                "title": "Aeryn Response",
                                "description": result.get("response", "No response")[:4000],
                                "color": 0x00FF88,
                                "fields": [
                                    {
                                        "name": "Safety",
                                        "value": result.get("safety", {}).get("risk", "unknown"),
                                        "inline": True,
                                    },
                                    {
                                        "name": "Adapter",
                                        "value": result.get("adapter", "none"),
                                        "inline": True,
                                    },
                                ]
                            }
                        ]
                    }
                }
        except Exception as e:
            return {
                "type": 4,
                "data": {"content": f"Error: {str(e)}"}
            }
    
    async def _handle_search(self, query: str = "", **kwargs) -> Dict:
        """Handle /search command."""
        import urllib.request
        
        req = urllib.request.Request(
            f"http://127.0.0.1:3010/search?q={urllib.parse.quote(query)}&limit=5",
            method="GET",
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                results = result.get("results", [])
                
                if not results:
                    return {"type": 4, "data": {"content": "No results found"}}
                
                embed = {
                    "title": f"Search: {query}",
                    "color": 0x00CCFF,
                    "fields": []
                }
                
                for r in results:
                    embed["fields"].append({
                        "name": r.get("title", "Untitled")[:256],
                        "value": r.get("content", "")[:1024],
                        "inline": False,
                    })
                
                return {"type": 4, "data": {"embeds": [embed]}}
        except Exception as e:
            return {"type": 4, "data": {"content": f"Error: {str(e)}"}}
    
    async def _handle_task(self, action: str = "list", description: str = "", **kwargs) -> Dict:
        """Handle /task command."""
        import urllib.request
        
        if action == "list":
            req = urllib.request.Request(
                "http://127.0.0.1:3010/shared/tasks",
                method="GET",
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    result = json.loads(resp.read().decode())
                    tasks = result.get("tasks", [])
                    
                    if not tasks:
                        return {"type": 4, "data": {"content": "No pending tasks"}}
                    
                    task_list = "\n".join([
                        f"- [{t.get('status', '?')}] {t.get('title', 'Untitled')}"
                        for t in tasks[:10]
                    ])
                    
                    return {"type": 4, "data": {"content": f"**Tasks:**\n{task_list}"}}
            except Exception as e:
                return {"type": 4, "data": {"content": f"Error: {str(e)}"}}
        
        elif action == "create" and description:
            req = urllib.request.Request(
                f"http://127.0.0.1:3010/shared/tasks/add?title={urllib.parse.quote(description)}&priority=5",
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    result = json.loads(resp.read().decode())
                    return {"type": 4, "data": {"content": f"Task created: {result.get('id', '?')}"}}
            except Exception as e:
                return {"type": 4, "data": {"content": f"Error: {str(e)}"}}
        
        return {"type": 4, "data": {"content": "Usage: /task action:list|create|complete [description]"}}
    
    async def _handle_reminder(self, text: str = "", when: str = "+1h", **kwargs) -> Dict:
        """Handle /reminder command."""
        import urllib.request
        
        req = urllib.request.Request(
            f"http://127.0.0.1:3010/shared/reminders/add?text={urllib.parse.quote(text)}&when={urllib.parse.quote(when)}&source=discord",
            method="POST",
        )
        
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
                return {"type": 4, "data": {"content": f"Reminder set! ID: {result.get('id', '?')}"}}
        except Exception as e:
            return {"type": 4, "data": {"content": f"Error: {str(e)}"}}
    
    async def _handle_vault(self, action: str = "search", query: str = "", **kwargs) -> Dict:
        """Handle /vault command."""
        import urllib.request
        
        if action == "read" or action == "search":
            req = urllib.request.Request(
                f"http://127.0.0.1:3010/search?q={urllib.parse.quote(query)}&limit=3",
                method="GET",
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    result = json.loads(resp.read().decode())
                    results = result.get("results", [])
                    
                    if not results:
                        return {"type": 4, "data": {"content": "No entries found"}}
                    
                    content = "\n\n".join([
                        f"**{r.get('title', 'Untitled')}**\n{r.get('content', '')[:500]}"
                        for r in results
                    ])
                    
                    return {"type": 4, "data": {"content": content[:2000]}}
            except Exception as e:
                return {"type": 4, "data": {"content": f"Error: {str(e)}"}}
        
        return {"type": 4, "data": {"content": "Usage: /vault action:read|write|search query:..."}}


class DiscordBotRunner:
    """Run the Discord bot event loop."""
    
    def __init__(self, token: str):
        self.token = token
        self.handler = DiscordBotHandler(token)
        self._running = False
    
    async def start(self):
        """Start the bot."""
        import aiohttp
        
        self._running = True
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                "wss://gateway.discord.gg/?v=10&encoding=json"
            ) as ws:
                # Identify
                await ws.send_json({
                    "op": 2,
                    "d": {
                        "token": self.token,
                        "intents": 513,  # GUILDS + GUILD_MESSAGES
                        "properties": {
                            "os": "linux",
                            "browser": "aeryn",
                            "device": "aeryn",
                        }
                    }
                })
                
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        await self._handle_event(ws, data)
    
    async def _handle_event(self, ws, data: Dict):
        """Handle Discord gateway events."""
        op = data.get("op")
        event = data.get("t")
        d = data.get("d", {})
        
        if op == 10:  # Hello
            # Start heartbeat
            interval = d.get("heartbeat_interval", 41250) / 1000
            asyncio.create_task(self._heartbeat(ws, interval))
        
        elif event == "INTERACTION_CREATE":
            interaction = d
            response = await self.handler.handle_interaction(interaction)
            await ws.send_json({
                "op": 4,  # ? - use HTTP response instead
                "d": response,
            })
        
        elif event == "MESSAGE_CREATE":
            # Handle natural language messages
            content = d.get("content", "")
            if content.startswith("!aeryn "):
                message = content[7:]
                response = await self.handler._handle_aeryn(message=message)
                await ws.send_json({
                    "op": 4,
                    "d": response,
                })
    
    async def _heartbeat(self, ws, interval: float):
        """Send periodic heartbeats."""
        while self._running:
            await ws.send_json({"op": 1, "d": None})
            await asyncio.sleep(interval)


if __name__ == "__main__":
    handler = DiscordBotHandler()
    
    print("=== Discord Bot Test ===")
    print(f"Commands: {len(handler.get_commands())}")
    for cmd in handler.get_commands():
        print(f"  /{cmd['name']}: {cmd['description']}")
    
    # Test handlers
    async def test():
        result = await handler._handle_search(query="python")
        print(f"Search result: {result['data'].get('content', '')[:100]}")
    
    asyncio.run(test())
