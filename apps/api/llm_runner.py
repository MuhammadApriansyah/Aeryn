#!/usr/bin/env python3
"""V39.65 — Feature: Real LLM Integration + Tool Execution Bridge.

Connects actual LLM to /run endpoint and enables tool execution:
- web_search: search the web
- web_read: read web pages
- fs_read: read files
- fs_write: write files
- terminal: run commands
- set_reminder: schedule reminders
"""

import os
import sys
import json
import uuid
import time
import subprocess
import urllib.parse
import urllib.request
import urllib.error
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aeryn_core.safety_engine import get_safety_engine, sanitize_output
from aeryn_core.adapters import get_active_adapter, render_adapter_context
from aeryn_core.reasoning_style import needs_research
from aeryn_core.vault import AerynVault, VaultEntry, LAYER_WIKI
from aeryn_core.social_memory import SocialMemory
from aeryn_core.hybrid_search import get_search_engine
from aeryn_core.persona_engine import load_persona
from aeryn_core.config import ensure_dirs, DATABASE_DIR
from aeryn_core.model_client import ModelClient

# ── Tool Execution Engine ────────────────────────────────────────

class ToolExecutor:
    """Execute tools requested by the LLM."""
    
    def __init__(self, sandbox_roots: list = None):
        self.sandbox_roots = sandbox_roots if sandbox_roots is not None else ["/tmp", os.path.expanduser("~/aeryn-core-agent")]
        self._reminder_file = os.path.join(DATABASE_DIR, "reminders.jsonl")
    
    def execute(self, tool_name: str, params: dict) -> dict:
        """Execute a tool and return result."""
        try:
            if tool_name == "web_search":
                return self.web_search(params.get("query", ""))
            elif tool_name == "web_read":
                return self.web_read(params.get("url", ""))
            elif tool_name == "fs_read":
                return self.fs_read(params.get("path", ""))
            elif tool_name == "fs_write":
                return self.fs_write(params.get("path", ""), params.get("content", ""))
            elif tool_name == "terminal":
                return self.terminal(params.get("command", ""))
            elif tool_name == "set_reminder":
                return self.set_reminder(
                    params.get("text", ""),
                    params.get("when", "")
                )
            elif tool_name == "memory_search":
                return self.memory_search(params.get("query", ""))
            elif tool_name == "vault_read":
                return self.vault_read(params.get("query", ""))
            else:
                return {"ok": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def web_search(self, query: str) -> dict:
        """Search the web using available search backend."""
        if not query:
            return {"ok": False, "error": "No query provided"}
        
        # Use Hermes web_search tool if available
        try:
            import urllib.parse
            import urllib.request
            # Simple search via DuckDuckGo or similar
            search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="replace")
                # Extract titles and snippets (simple parsing)
                results = []
                import re
                for match in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html):
                    url, title = match.groups()
                    title = re.sub(r'<[^>]+>', '', title)
                    results.append({"title": title[:100], "url": url[:200]})
                    if len(results) >= 5:
                        break
                return {"ok": True, "results": results, "query": query}
        except Exception as e:
            return {"ok": False, "error": f"Search failed: {e}"}
    
    def web_read(self, url: str) -> dict:
        """Read content from a URL."""
        if not url:
            return {"ok": False, "error": "No URL provided"}
        
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                # Strip HTML tags for readability
                import re
                text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.I)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.I)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                return {"ok": True, "content": text[:5000], "url": url}
        except Exception as e:
            return {"ok": False, "error": f"Read failed: {e}"}
    
    def fs_read(self, path: str) -> dict:
        """Read a file from filesystem."""
        if not path:
            return {"ok": False, "error": "No path provided"}
        
        # Safety check
        from aeryn_core.safety_engine import check_path
        ok, reason = check_path(path, "read")
        if not ok:
            return {"ok": False, "error": reason}
        
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            return {"ok": True, "content": content[:10000], "path": path}
        except Exception as e:
            return {"ok": False, "error": f"Read failed: {e}"}
    
    def fs_write(self, path: str, content: str) -> dict:
        """Write content to a file."""
        if not path:
            return {"ok": False, "error": "No path provided"}
        
        from aeryn_core.safety_engine import check_path
        ok, reason = check_path(path, "write")
        if not ok:
            return {"ok": False, "error": reason}
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"ok": True, "path": path, "bytes_written": len(content)}
        except Exception as e:
            return {"ok": False, "error": f"Write failed: {e}"}
    
    def terminal(self, command: str) -> dict:
        """Run a terminal command (sandboxed)."""
        if not command:
            return {"ok": False, "error": "No command provided"}
        
        # Block dangerous commands
        dangerous = ["rm -rf /", "mkfs", "dd if=/dev/zero", ":(){ :|:& };:", "chmod 777"]
        for d in dangerous:
            if d in command:
                return {"ok": False, "error": f"Dangerous command blocked: {d}"}
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd="/tmp",
            )
            return {
                "ok": result.returncode == 0,
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:2000],
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Command timed out (30s)"}
        except Exception as e:
            return {"ok": False, "error": f"Command failed: {e}"}
    
    def set_reminder(self, text: str, when: str) -> dict:
        """Set a reminder for later."""
        if not text:
            return {"ok": False, "error": "No reminder text"}
        
        # Parse "when" (simple: +5m, +2h, +1d, or ISO timestamp)
        now = datetime.now()
        try:
            if when.startswith("+"):
                num = int(when[1:-1])
                unit = when[-1]
                if unit == "m":
                    dt = now + timedelta(minutes=num)
                elif unit == "h":
                    dt = now + timedelta(hours=num)
                elif unit == "d":
                    dt = now + timedelta(days=num)
                else:
                    dt = now + timedelta(hours=1)
            else:
                dt = datetime.fromisoformat(when)
        except Exception:
            dt = now + timedelta(hours=1)
        
        reminder = {
            "id": str(uuid.uuid4())[:8],
            "text": text,
            "due": dt.isoformat(),
            "created": now.isoformat(),
            "status": "pending",
        }
        
        try:
            os.makedirs(os.path.dirname(self._reminder_file), exist_ok=True)
            with open(self._reminder_file, "a") as f:
                f.write(json.dumps(reminder) + "\n")
            return {"ok": True, "reminder": reminder}
        except Exception as e:
            return {"ok": False, "error": f"Failed to save reminder: {e}"}
    
    def memory_search(self, query: str) -> dict:
        """Search memories."""
        hse = get_search_engine()
        results = hse.search(query, limit=5)
        return {"ok": True, "results": results, "query": query}
    
    def vault_read(self, query: str) -> dict:
        """Read from vault."""
        vault = AerynVault()
        results = vault.search(query, limit=5)
        return {"ok": True, "results": results, "query": query}


# ── LLM Runner ───────────────────────────────────────────────────

class LLMRunner:
    """Run goals through actual LLM with tool execution."""
    
    def __init__(self):
        self.client = ModelClient()
        self.tool_executor = ToolExecutor()
        self.eng = get_safety_engine()
    
    def run(self, goal: str, session_id: str, max_tool_calls: int = 5) -> dict:
        """Run goal through LLM with tool execution loop."""
        persona = load_persona()
        
        # Build system prompt
        system_prompt = persona + "\n\n"
        system_prompt += "You are Aeryn, an AI assistant. You have access to tools. "
        system_prompt += "When you need to use a tool, respond with JSON: "
        system_prompt += '{"tool": "tool_name", "params": {key: value}}\n'
        system_prompt += "When you have a final response, just respond normally."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": goal},
        ]
        
        tool_calls = 0
        trace = []
        
        while tool_calls < max_tool_calls:
            # Call LLM
            try:
                response = self.client.chat(
                    messages,
                    max_tokens=2048,
                    temperature=0.4,
                )
            except Exception as e:
                return {
                    "ok": False,
                    "error": f"LLM call failed: {e}",
                    "trace": trace,
                }
            
            # Handle dict response (ModelClient returns OpenAI-compatible dict)
            response_text = ""
            if isinstance(response, dict):
                # Extract actual content from OpenAI-compatible response
                choices = response.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    response_text = message.get("content", "")
                if not response_text:
                    response_text = str(response)
            else:
                response_text = str(response)
            
            # Check if response is a tool call
            try:
                tool_call = json.loads(response_text.strip())
                if isinstance(tool_call, dict) and "tool" in tool_call:
                    tool_name = tool_call["tool"]
                    params = tool_call.get("params", {})
                    
                    # Execute tool
                    result = self.tool_executor.execute(tool_name, params)
                    trace.append({
                        "tool": tool_name,
                        "params": params,
                        "result": result,
                    })
                    
                    # Add tool result to messages
                    messages.append({"role": "assistant", "content": response_text})
                    messages.append({
                        "role": "user",
                        "content": f"Tool result: {json.dumps(result, ensure_ascii=False)}",
                    })
                    
                    tool_calls += 1
                    continue
            except json.JSONDecodeError:
                pass  # Not a tool call, it's a final response
            
            # Final response
            clean = sanitize_output(response_text)
            return {
                "ok": True,
                "response": clean,
                "tool_calls": tool_calls,
                "trace": trace,
            }
        
        return {
            "ok": True,
            "response": "Max tool calls reached. Partial result.",
            "tool_calls": tool_calls,
            "trace": trace,
        }


# ── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    ensure_dirs()
    runner = LLMRunner()
    
    # Test
    result = runner.run("What is 2+2?", "test_session")
    print(json.dumps(result, indent=2, ensure_ascii=False))
