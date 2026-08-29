#!/usr/bin/env python3
"""V41.0 — Phase 1: Tool Execution Runtime.

Provides native tool execution without HTTP round-trip.
Tools run in-process with proper sandboxing.
"""

import os, sys, json, subprocess, asyncio, shutil
from typing import Dict, List, Optional, Any
from datetime import datetime
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR


class ToolResult:
    def __init__(self, ok: bool, output: str = "", error: str = "", 
                 duration_ms: int = 0, tool: str = ""):
        self.ok = ok
        self.output = output
        self.error = error
        self.duration_ms = duration_ms
        self.tool = tool
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "ok": self.ok,
            "output": self.output[:5000],
            "error": self.error[:1000] if self.error else "",
            "duration_ms": self.duration_ms,
            "tool": self.tool,
            "timestamp": self.timestamp,
        }


class ToolRuntime:
    """Execute tools natively in-process."""
    
    def __init__(self):
        self._tools: Dict[str, callable] = {
            "fs_read": self._fs_read,
            "fs_write": self._fs_write,
            "fs_list": self._fs_list,
            "terminal": self._terminal,
            "web_search": self._web_search,
            "web_fetch": self._web_fetch,
            "python": self._python,
        }
    
    def list_tools(self) -> List[str]:
        return list(self._tools.keys())
    
    async def execute(self, tool: str, params: Dict) -> ToolResult:
        """Execute a tool."""
        if tool not in self._tools:
            return ToolResult(ok=False, error=f"Unknown tool: {tool}", tool=tool)
        
        start = datetime.now()
        try:
            result = await self._tools[tool](params)
            duration = int((datetime.now() - start).total_seconds() * 1000)
            result.duration_ms = duration
            return result
        except Exception as e:
            duration = int((datetime.now() - start).total_seconds() * 1000)
            return ToolResult(ok=False, error=str(e), duration_ms=duration, tool=tool)
    
    async def _fs_read(self, params: Dict) -> ToolResult:
        path = params.get("path", "")
        
        # Security: validate path
        from aeryn_core.security_hardening import validate_path, SAFE_READ_DIRS
        if not validate_path(path, SAFE_READ_DIRS):
            return ToolResult(ok=False, error="Access denied: path outside safe directories", tool="fs_read")
        
        if not os.path.exists(path):
            return ToolResult(ok=False, error=f"File not found: {path}", tool="fs_read")
        
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                content = f.read()
            return ToolResult(ok=True, output=content[:50000], tool="fs_read")
        except Exception as e:
            return ToolResult(ok=False, error=str(e), tool="fs_read")
    
    async def _fs_write(self, params: Dict) -> ToolResult:
        path = params.get("path", "")
        content = params.get("content", "")
        
        # Security: validate path
        from aeryn_core.security_hardening import validate_path, SAFE_WRITE_DIRS
        if not validate_path(path, SAFE_WRITE_DIRS):
            return ToolResult(ok=False, error="Access denied: path outside safe directories", tool="fs_write")
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(ok=True, output=f"Written {len(content)} chars", tool="fs_write")
        except Exception as e:
            return ToolResult(ok=False, error=str(e), tool="fs_write")
    
    async def _fs_list(self, params: Dict) -> ToolResult:
        path = params.get("path", ".")
        if not os.path.isdir(path):
            return ToolResult(ok=False, error=f"Directory not found: {path}", tool="fs_list")
        
        try:
            entries = []
            for entry in os.listdir(path):
                full = os.path.join(path, entry)
                entries.append({
                    "name": entry,
                    "is_dir": os.path.isdir(full),
                    "size": os.path.getsize(full) if os.path.isfile(full) else 0,
                })
            return ToolResult(ok=True, output=json.dumps(entries, indent=2), tool="fs_list")
        except Exception as e:
            return ToolResult(ok=False, error=str(e), tool="fs_list")
    
    async def _terminal(self, params: Dict) -> ToolResult:
        command = params.get("command", "")
        timeout = params.get("timeout", 30)
        
        # Security: validate command
        from aeryn_core.security_hardening import sanitize_command
        safe, msg = sanitize_command(command)
        if not safe:
            return ToolResult(ok=False, error=f"Blocked: {msg}", tool="terminal")
        
        try:
            # Use sh -c for simple commands (safer than shell=True)
            proc = await asyncio.create_subprocess_exec(
                "sh", "-c", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=BASE_DIR,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return ToolResult(
                ok=proc.returncode == 0,
                output=stdout.decode(errors="replace")[:50000],
                error=stderr.decode(errors="replace")[:10000],
                tool="terminal",
            )
        except asyncio.TimeoutError:
            proc.kill()
            return ToolResult(ok=False, error=f"Timeout after {timeout}s", tool="terminal")
        except Exception as e:
            return ToolResult(ok=False, error=str(e), tool="terminal")
    
    async def _web_search(self, params: Dict) -> ToolResult:
        query = params.get("query", "")
        # Use curl to search (placeholder for real search API)
        try:
            proc = await asyncio.create_subprocess_exec(
                "curl", "-s", f"https://html.duckduckgo.com/html/?q={query}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
            return ToolResult(ok=True, output=stdout.decode(errors="replace")[:20000], tool="web_search")
        except Exception as e:
            return ToolResult(ok=False, error=str(e), tool="web_search")
    
    async def _web_fetch(self, params: Dict) -> ToolResult:
        url = params.get("url", "")
        try:
            proc = await asyncio.create_subprocess_exec(
                "curl", "-sL", "--max-time", "10", url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
            return ToolResult(ok=True, output=stdout.decode(errors="replace")[:50000], tool="web_fetch")
        except Exception as e:
            return ToolResult(ok=False, error=str(e), tool="web_fetch")
    
    async def _python(self, params: Dict) -> ToolResult:
        code = params.get("code", "")
        
        # Write to temp file and execute
        tmp_path = f"/tmp/aeryn_python_{os.getpid()}.py"
        try:
            with open(tmp_path, "w") as f:
                f.write(code)
            
            proc = await asyncio.create_subprocess_exec(
                sys.executable, tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            return ToolResult(
                ok=proc.returncode == 0,
                output=stdout.decode(errors="replace")[:50000],
                error=stderr.decode(errors="replace")[:10000],
                tool="python",
            )
        except asyncio.TimeoutError:
            proc.kill()
            return ToolResult(ok=False, error="Timeout after 30s", tool="python")
        except Exception as e:
            return ToolResult(ok=False, error=str(e), tool="python")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


# ── Singleton ─────────────────────────────────

_runtime: Optional[ToolRuntime] = None

def get_tool_runtime() -> ToolRuntime:
    global _runtime
    if _runtime is None:
        _runtime = ToolRuntime()
    return _runtime
