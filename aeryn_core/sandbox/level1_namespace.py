#!/usr/bin/env python3
"""Level 1: Namespace sandbox — unshare + resource limits."""
import os
import sys
import ctypes
import ctypes.util
import resource
import tempfile
import shutil
import subprocess
import logging

logger = logging.getLogger(__name__)

CLONE_NEWNS = 0x00020000
CLONE_NEWUTS = 0x04000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000
CLONE_NEWIPC = 0x08000000
CLONE_NEWUSER = 0x10000000

class NamespaceSandbox:
    def __init__(self, memory_limit_mb=256, cpu_limit_sec=30, fd_limit=64):
        self.memory_limit = memory_limit_mb * 1024 * 1024
        self.cpu_limit = cpu_limit_sec
        self.fd_limit = fd_limit
        self._libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
    
    def _preexec_fn(self):
        try:
            flags = CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWPID | CLONE_NEWIPC
            result = self._libc.unshare(flags)
            if result != 0:
                errno = ctypes.get_errno()
                logger.warning(f"unshare failed: {ctypes.get_errno()}")
        except Exception as e:
            logger.warning(f"unshare exception: {e}")
        
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
        
        tempdir = tempfile.mkdtemp(prefix="aeryn_sandbox_")
        try:
            result = subprocess.run(
                parts, capture_output=True, text=True,
                preexec_fn=self._preexec_fn, cwd=tempdir,
                timeout=timeout or self.cpu_limit
            )
            return {
                "stdout": result.stdout, "stderr": result.stderr,
                "returncode": result.returncode, "sandbox": "namespace"
            }
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            if tempdir and os.path.exists(tempdir):
                shutil.rmtree(tempdir, ignore_errors=True)

namespace_sandbox = NamespaceSandbox()
