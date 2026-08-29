#!/usr/bin/env python3
"""V41.0 — Security Hardening & Mitigation.

Fixes identified vulnerabilities:
1. Path Traversal - stricter validation
2. Command Injection - replace shell=True with exec
3. SQL Injection - validate table names
4. Resource leaks - proper cleanup
"""

import os, sys, json, asyncio, re
from typing import Dict, Optional
from aeryn_core.utils.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── 1. Path Traversal Mitigation ──────────────

SAFE_READ_DIRS = [
    BASE_DIR,
    "/tmp/aeryn-safe",
]

SAFE_WRITE_DIRS = [
    os.path.join(BASE_DIR, "Personalisasi"),
    os.path.join(BASE_DIR, "logs"),
    "/tmp/aeryn-safe",
]

def validate_path(path: str, safe_dirs: list) -> bool:
    """Validate path is within safe directories."""
    try:
        real_path = os.path.realpath(path)
        real_safe = [os.path.realpath(d) for d in safe_dirs if os.path.isdir(d)]
        return any(real_path.startswith(rs + os.sep) or real_path == rs for rs in real_safe)
    except Exception:
        return False


# ── 2. Command Injection Mitigation ───────────

DANGEROUS_PATTERNS = [
    # Dangerous standalone commands
    r'^rm\s+-rf', r'^rm\s+-fr', r'^rm\s+/',
    r'^mkfs', r'^dd\s+if=', r':\(\)\{',
    r'^chmod\s+\+s', r'^chmod\s+4755',
    # Injection patterns
    r';\s*rm\s', r'\|\s*rm\s', r'&&\s*rm\s',
    r';\s*mkfs', r'\|\s*mkfs',
    r';\s*dd\s', r'\|\s*dd\s',
    r'`[^`]+`', r'\$\([^)]+\)',
    r'>\s*/dev/', r'<\s*/etc/',
    r'curl\s+.*\|.*sh', r'wget\s+.*\|.*sh',
    r';\s*bash\s', r'\|\s*bash\s',
    r';\s*sh\s', r'\|\s*sh\s',
    r'python\s+-c\s+.*import\s+os',
    r'python\s+-c\s+.*subprocess',
]

def sanitize_command(command: str) -> tuple[bool, str]:
    """Sanitize command string. Returns (safe, error_message)."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Dangerous pattern detected: {pattern}"
    return True, ""


# ── 3. SQL Injection Mitigation ───────────────

VALID_TABLE_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

def validate_table_name(name: str) -> bool:
    """Validate SQL table name."""
    return bool(VALID_TABLE_PATTERN.match(name))


# ── 4. Resource Management ────────────────────

class SafeFileHandle:
    """Context manager for safe file operations."""
    
    def __init__(self, path: str, mode: str = 'r', max_size: int = 10*1024*1024):
        self.path = path
        self.mode = mode
        self.max_size = max_size
        self._handle = None
    
    def __enter__(self):
        if 'r' in self.mode:
            size = os.path.getsize(self.path)
            if size > self.max_size:
                raise IOError(f"File too large: {size} bytes (max {self.max_size})")
        self._handle = open(self.path, self.mode, encoding='utf-8', errors='replace')
        return self._handle
    
    def __exit__(self, *args):
        if self._handle:
            self._handle.close()


class SafeProcess:
    """Context manager for safe subprocess execution."""
    
    def __init__(self, command: list, timeout: int = 30, cwd: str = None):
        self.command = command
        self.timeout = timeout
        self.cwd = cwd or BASE_DIR
        self.proc = None
    
    async def __aenter__(self):
        self.proc = await asyncio.create_subprocess_exec(
            *self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.cwd,
        )
        return self.proc
    
    async def __aexit__(self, *args):
        if self.proc and self.proc.returncode is None:
            try:
                self.proc.kill()
                await asyncio.wait_for(self.proc.communicate(), timeout=5)
            except Exception:
                from aeryn_core.utils.logger import log_exception
                log_exception(e, context=f"{__name__}")
                pass


def apply_hardening():
    """Apply all hardening measures."""
    # Create safe directories
    for d in SAFE_WRITE_DIRS:
        os.makedirs(d, exist_ok=True)
    
    print("Security hardening applied:")
    print(f"  Safe read dirs: {len(SAFE_READ_DIRS)}")
    print(f"  Safe write dirs: {len(SAFE_WRITE_DIRS)}")
    print(f"  Dangerous patterns: {len(DANGEROUS_PATTERNS)}")


if __name__ == "__main__":
    apply_hardening()
    print("\nHardening test:")
    
    # Test path validation
    assert validate_path("/tmp/aeryn-safe/test.txt", SAFE_WRITE_DIRS)
    assert not validate_path("/etc/passwd", SAFE_READ_DIRS)
    assert not validate_path("../../../etc/passwd", SAFE_READ_DIRS)
    print("  Path validation: OK")
    
    # Test command sanitization
    safe, msg = sanitize_command("ls -la")
    assert safe, f"Expected safe, got: {msg}"
    safe, msg = sanitize_command("rm -rf /")
    assert not safe, f"Expected unsafe, got safe"
    safe, msg = sanitize_command("cat /etc/passwd")
    assert safe, f"cat /etc/passwd should be safe: {msg}"
    print("  Command sanitization: OK")
    
    # Test table name validation
    assert validate_table_name("valid_table_123")
    assert not validate_table_name("table; DROP TABLE users")
    print("  SQL table validation: OK")
    
    print("\nAll hardening measures working!")
