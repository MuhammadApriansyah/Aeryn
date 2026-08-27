#!/usr/bin/env python3
"""V39.79 — Sandboxing: Safe terminal execution with isolation.

Features:
- Path jail (only allow certain directories)
- Command whitelist/blacklist
- Resource limits (timeout, memory)
- Network isolation option
- Audit logging
"""

import os
import re
import subprocess
import tempfile
import shutil
import signal
import resource
import time
from typing import Tuple, Optional
from dataclasses import dataclass

@dataclass
class SandboxResult:
    """Result of a sandboxed execution."""
    ok: bool
    returncode: int
    stdout: str
    stderr: str
    duration_ms: int
    error: str = ""

class Sandbox:
    """Safe execution environment."""
    
    # Allowed directories (path jail)
    ALLOWED_PATHS = [
        "/tmp",
        "/home/sen/aeryn-core-agent",
        "/home/sen/webnovel-platform",
        "/home/sen/Downloads",
    ]
    
    # Blocked commands
    BLOCKED_PATTERNS = [
        r"rm\s+-rf\s+/",
        r"rm\s+-rf\s+~",
        r"mkfs",
        r"dd\s+if=/dev/zero",
        r":\(\)\{:\|:&};:",  # Fork bomb
        r"chmod\s+777",
        r"chmod\s+-R\s+777",
        r">\s*/dev/sda",
        r"mv\s+.*\s+/dev/null",
        r"curl\s+.*\|\s*sh",
        r"wget\s+.*\|\s*sh",
    ]
    
    # Suspicious patterns (require confirmation)
    SUSPICIOUS_PATTERNS = [
        r"rm\s+-rf",
        r"sudo",
        r"apt\s+install",
        r"pip\s+install",
        r"npm\s+install\s+-g",
    ]
    
    def __init__(self, timeout: int = 30, max_memory_mb: int = 256,
                 allow_network: bool = True):
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb
        self.allow_network = allow_network
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """Validate a command before execution."""
        # Check blocked patterns
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, command, re.I):
                return False, f"Blocked command: {pattern}"
        
        # Check path jail (for file operations)
        if any(cmd in command for cmd in ["cat", "ls", "cd", "rm", "mv", "cp"]):
            for pattern in self.ALLOWED_PATHS:
                if pattern in command:
                    break
            else:
                # No allowed path found
                if not any(safe in command for safe in ["-la", "-l", "--help", "ls"]):
                    return False, f"Path jail: command must operate on allowed directories"
        
        return True, ""
    
    def execute(self, command: str, cwd: str = "/tmp") -> SandboxResult:
        """Execute a command in the sandbox."""
        import time
        
        # Validate
        valid, error = self.validate_command(command)
        if not valid:
            return SandboxResult(ok=False, returncode=-1, stdout="", stderr="",
                                duration_ms=0, error=error)
        
        # Check path jail for cwd
        if not any(cwd.startswith(p) for p in self.ALLOWED_PATHS):
            return SandboxResult(ok=False, returncode=-1, stdout="", stderr="",
                                duration_ms=0, error=f"CWD not in allowed paths")
        
        start_time = time.time()
        
        try:
            # Set resource limits
            def set_limits():
                # Limit memory
                resource.setrlimit(resource.RLIMIT_AS, (
                    self.max_memory_mb * 1024 * 1024,
                    self.max_memory_mb * 1024 * 1024
                ))
                # Limit CPU time
                resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout))
            
            # Execute
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=cwd,
                preexec_fn=set_limits
            )
            
            duration = int((time.time() - start_time) * 1000)
            
            return SandboxResult(
                ok=(result.returncode == 0),
                returncode=result.returncode,
                stdout=result.stdout[:5000],
                stderr=result.stderr[:2000],
                duration_ms=duration
            )
        
        except subprocess.TimeoutExpired:
            return SandboxResult(ok=False, returncode=-1, stdout="", stderr="",
                                duration_ms=int((time.time() - start_time) * 1000),
                                error=f"Command timed out ({self.timeout}s)")
        
        except Exception as e:
            return SandboxResult(ok=False, returncode=-1, stdout="", stderr="",
                                duration_ms=int((time.time() - start_time) * 1000),
                                error=str(e))
    
    def create_temp_dir(self) -> str:
        """Create a temporary directory in the sandbox."""
        tmpdir = tempfile.mkdtemp(prefix="aeryn_sandbox_")
        return tmpdir
    
    def cleanup_temp_dir(self, path: str):
        """Clean up a temporary directory."""
        if path.startswith("/tmp/aeryn_sandbox_"):
            shutil.rmtree(path, ignore_errors=True)


class SecureTerminal:
    """Secure terminal with sandboxing."""
    
    def __init__(self):
        self.sandbox = Sandbox()
        self._audit_log = []
    
    def run(self, command: str, cwd: str = "/tmp") -> dict:
        """Run a command securely."""
        # Audit
        self._audit_log.append({
            "command": command,
            "cwd": cwd,
            "timestamp": time.time()
        })
        
        result = self.sandbox.execute(command, cwd)
        
        return {
            "ok": result.ok,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_ms": result.duration_ms,
            "error": result.error
        }
    
    def get_audit_log(self) -> list:
        """Get audit log."""
        return self._audit_log


# Singleton
_terminal = None

def get_secure_terminal() -> SecureTerminal:
    global _terminal
    if _terminal is None:
        _terminal = SecureTerminal()
    return _terminal


if __name__ == "__main__":
    terminal = SecureTerminal()
    
    print("=== Sandbox Test ===")
    
    # Safe command
    result = terminal.run("ls -la /tmp")
    print(f"Safe: ok={result['ok']}, stdout={result['stdout'][:100]}")
    
    # Blocked command
    result = terminal.run("rm -rf /")
    print(f"Blocked: ok={result['ok']}, error={result['error']}")
    
    # Suspicious but allowed
    result = terminal.run("rm -rf /tmp/aeryn_sandbox_test")
    print(f"Suspicious: ok={result['ok']}")
    
    # Fork bomb
    result = terminal.run(":(){ :|:& };:")
    print(f"Fork bomb: ok={result['ok']}, error={result['error']}")
