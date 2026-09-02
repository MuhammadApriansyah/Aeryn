"""Bash tool — execute shell commands."""

import subprocess
import shlex
import os


class BashTool:
    """Execute shell commands with timeout and safety."""
    
    def __init__(self, working_dir=None, timeout=30):
        self.working_dir = working_dir or os.getcwd()
        self.timeout = timeout
    
    def execute(self, command: str, timeout: int = 30) -> dict:
        """Execute a shell command and return result."""
        try:
            # Safety: block dangerous commands
            blocked = ['rm -rf /', 'mkfs.', 'dd if=', ':(){:|:&};:', '> /dev/sda']
            for b in blocked:
                if b in command:
                    return {"stdout": "", "stderr": f"Blocked: dangerous command '{b}'", "returncode": 1}
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                cwd=self.working_dir,
                env={**os.environ, "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")}
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": f"Command timed out after {timeout}s", "returncode": 124}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "returncode": 1}


bash_tool = BashTool()
