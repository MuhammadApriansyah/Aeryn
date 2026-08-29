#!/usr/bin/env python3
"""Level 0: Basic sandbox — resource limits + whitelist + tempdir."""
import os
import sys
import resource
import shutil
import tempfile
import subprocess
import threading
import logging

logger = logging.getLogger(__name__)

ALLOWED_COMMANDS = {
    "python3", "python", "pip", "pip3", "git", "ls", "cat", "head", "tail",
    "grep", "awk", "sed", "wc", "sort", "uniq", "find", "echo", "mkdir",
    "cp", "mv", "touch", "chmod", "curl", "wget", "jq",
}

class BasicSandbox:
    def __init__(self, memory_limit_mb=256, cpu_limit_sec=30, fd_limit=64):
        self.memory_limit = memory_limit_mb * 1024 * 1024
        self.cpu_limit = cpu_limit_sec
        self.fd_limit = fd_limit
        self._tempdir = None
    
    def _preexec_fn(self):
        resource.setrlimit(resource.RLIMIT_AS, (self.memory_limit, self.memory_limit))
        resource.setrlimit(resource.RLIMIT_CPU, (self.cpu_limit, self.cpu_limit))
        resource.setrlimit(resource.RLIMIT_NOFILE, (self.fd_limit, self.fd_limit))
        resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))
    
    def execute(self, command, timeout=None):
        if isinstance(command, str):
            parts = command.split()
        else:
            parts = list(command)
        
        if not parts:
            return {"error": "Empty command"}
        
        cmd = parts[0]
        if cmd not in ALLOWED_COMMANDS and not cmd.startswith("./"):
            return {"error": f"Command '{cmd}' not in whitelist"}
        
        self._tempdir = tempfile.mkdtemp(prefix="aeryn_sandbox_")
        try:
            result = subprocess.run(
                parts, capture_output=True, text=True,
                preexec_fn=self._preexec_fn, cwd=self._tempdir,
                timeout=timeout or self.cpu_limit
            )
            return {
                "stdout": result.stdout, "stderr": result.stderr,
                "returncode": result.returncode, "sandbox": "basic"
            }
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            if self._tempdir and os.path.exists(self._tempdir):
                shutil.rmtree(self._tempdir, ignore_errors=True)

basic_sandbox = BasicSandbox()
