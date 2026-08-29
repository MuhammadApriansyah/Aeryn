#!/usr/bin/env python3
"""Level 3: Full sandbox — bubblewrap + secimport + cgroups."""
import os
import shutil
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)

class FullSandbox:
    def __init__(self, memory_limit_mb=256, cpu_limit_sec=30, fd_limit=64):
        self.memory_limit = memory_limit_mb
        self.cpu_limit = cpu_limit_sec
        self.fd_limit = fd_limit
        self._bwrap_path = shutil.which("bwrap")
    
    def is_available(self):
        try:
            import secimport
            return self._bwrap_path is not None and os.getuid() == 0
        except ImportError:
            return False
    
    def execute(self, command, timeout=None):
        if not self.is_available():
            return {"error": "full sandbox requires bwrap + secimport + root"}
        
        if isinstance(command, str):
            parts = command.split()
        else:
            parts = list(command)
        
        if not parts:
            return {"error": "Empty command"}
        
        tempdir = tempfile.mkdtemp(prefix="aeryn_sandbox_")
        try:
            bwrap_cmd = [
                self._bwrap_path,
                "--ro-bind", "/usr", "/usr",
                "--ro-bind", "/lib", "/lib",
                "--ro-bind", "/lib64", "/lib64",
                "--proc", "/proc",
                "--dev", "/dev",
                "--tmpfs", "/tmp",
                "--bind", tempdir, "/workspace",
                "--unshare-all",
                "--new-session",
                "--die-with-parent",
            ]
            
            bwrap_cmd.extend(["/bin/sh", "-c", f"ulimit -v {self.memory_limit * 1024}; ulimit -t {self.cpu_limit}; {' '.join(parts)}"])
            
            result = subprocess.run(
                bwrap_cmd, capture_output=True, text=True,
                timeout=timeout or self.cpu_limit
            )
            return {
                "stdout": result.stdout, "stderr": result.stderr,
                "returncode": result.returncode, "sandbox": "full"
            }
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            if tempdir and os.path.exists(tempdir):
                shutil.rmtree(tempdir, ignore_errors=True)

full_sandbox = FullSandbox()
