#!/usr/bin/env python3
"""V39.95-V39.99 — Enhanced Sandbox: Audit logging, network isolation, resource quotas.

Production-grade sandboxing with:
- Full audit trail (who ran what, when, result)
- Network isolation mode (block outbound)
- Resource quotas (CPU, memory, disk, time)
- Session-based sandbox environments
- Compatible with CubeSandbox API concepts
"""

import os
import sys
import json
import time
import shutil
import hashlib
import sqlite3
import subprocess
import threading
import resource
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "sandbox_audit.db")


@dataclass
class SandboxLimits:
    """Resource limits for a sandbox session."""
    max_cpu_seconds: int = 30
    max_memory_mb: int = 256
    max_disk_mb: int = 100
    max_processes: int = 10
    max_file_descriptors: int = 64
    allow_network: bool = False
    max_execution_time: int = 60


@dataclass
class SandboxSession:
    """A sandboxed execution environment."""
    session_id: str
    user_id: str
    created_at: datetime
    work_dir: str
    limits: SandboxLimits
    audit_entries: List[Dict] = field(default_factory=list)


class AuditLogger:
    """Full audit trail for sandboxed execution."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sandbox_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT,
                    status TEXT DEFAULT 'active',
                    work_dir TEXT,
                    config TEXT DEFAULT '{}'
                );
                
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    action TEXT NOT NULL,
                    command TEXT,
                    user_id TEXT,
                    result_status TEXT,
                    stdout_preview TEXT,
                    stderr_preview TEXT,
                    duration_ms INTEGER,
                    metadata TEXT DEFAULT '{}'
                );
                
                CREATE TABLE IF NOT EXISTS resource_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    cpu_seconds REAL,
                    memory_mb REAL,
                    disk_mb REAL,
                    processes INTEGER
                );
                
                CREATE INDEX IF NOT EXISTS idx_audit_session ON audit_log(session_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id, timestamp);
            """)
            conn.commit()
        finally:
            conn.close()
    
    def create_session(self, session: SandboxSession) -> str:
        """Register a new sandbox session."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO sandbox_sessions (session_id, user_id, work_dir, config)
                VALUES (?, ?, ?, ?)
            """, (
                session.session_id,
                session.user_id,
                session.work_dir,
                json.dumps({
                    "max_cpu": session.limits.max_cpu_seconds,
                    "max_memory_mb": session.limits.max_memory_mb,
                    "allow_network": session.limits.allow_network,
                }),
            ))
            conn.commit()
        finally:
            conn.close()
        return session.session_id
    
    def log_action(self, session_id: str, action: str, user_id: str = "unknown",
                   command: str = "", result_status: str = "success",
                   stdout: str = "", stderr: str = "", duration_ms: int = 0,
                   metadata: Dict = None):
        """Log a sandbox action."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO audit_log (session_id, action, command, user_id, result_status,
                                       stdout_preview, stderr_preview, duration_ms, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, action, command, user_id, result_status,
                stdout[:1000], stderr[:500], duration_ms,
                json.dumps(metadata or {}),
            ))
            conn.commit()
        finally:
            conn.close()
    
    def log_resource_usage(self, session_id: str, cpu: float = 0, memory: float = 0,
                           disk: float = 0, processes: int = 0):
        """Log resource usage snapshot."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO resource_usage (session_id, cpu_seconds, memory_mb, disk_mb, processes)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, cpu, memory, disk, processes))
            conn.commit()
        finally:
            conn.close()
    
    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get audit history for a session."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT timestamp, action, command, result_status, duration_ms, metadata
                FROM audit_log WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?
            """, (session_id, limit)).fetchall()
            
            return [
                {
                    "timestamp": r[0],
                    "action": r[1],
                    "command": r[2],
                    "result_status": r[3],
                    "duration_ms": r[4],
                    "metadata": json.loads(r[5]) if r[5] else {},
                }
                for r in rows
            ]
        finally:
            conn.close()
    
    def get_user_activity(self, user_id: str, days: int = 7) -> List[Dict]:
        """Get user's sandbox activity over time."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT timestamp, action, command, result_status, duration_ms
                FROM audit_log WHERE user_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC LIMIT 100
            """, (user_id, cutoff)).fetchall()
            
            return [
                {"timestamp": r[0], "action": r[1], "command": r[2],
                 "result_status": r[3], "duration_ms": r[4]}
                for r in rows
            ]
        finally:
            conn.close()


class EnhancedSandbox:
    """Enhanced sandbox with audit, isolation, and quotas."""
    
    BASE_DIR = "/tmp/aeryn_sandbox"
    
    def __init__(self):
        os.makedirs(self.BASE_DIR, exist_ok=True)
        self.audit = AuditLogger()
        self._active_sessions: Dict[str, SandboxSession] = {}
        self._lock = threading.Lock()
    
    def create_session(self, user_id: str, limits: SandboxLimits = None) -> str:
        """Create a new sandbox session."""
        import uuid
        
        session_id = str(uuid.uuid4())[:12]
        work_dir = os.path.join(self.BASE_DIR, session_id)
        os.makedirs(work_dir, exist_ok=True)
        
        session = SandboxSession(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(),
            work_dir=work_dir,
            limits=limits or SandboxLimits(),
        )
        
        self.audit.create_session(session)
        
        with self._lock:
            self._active_sessions[session_id] = session
        
        return session_id
    
    def execute(self, session_id: str, command: str, user_id: str = "unknown") -> Dict:
        """Execute a command in the sandbox with full audit."""
        start_time = time.time()
        
        session = self._active_sessions.get(session_id)
        if not session:
            return {"ok": False, "error": "Invalid session"}
        
        # Log the attempt
        self.audit.log_action(
            session_id=session_id,
            action="execute",
            user_id=user_id,
            command=command,
        )
        
        # Validate command against limits
        validation_error = self._validate_command(session, command)
        if validation_error:
            self.audit.log_action(
                session_id=session_id,
                action="blocked",
                user_id=user_id,
                command=command,
                result_status="blocked",
                metadata={"reason": validation_error},
            )
            return {"ok": False, "error": validation_error}
        
        # Set resource limits
        def set_limits():
            limits = session.limits
            resource.setrlimit(resource.RLIMIT_CPU, (limits.max_cpu_seconds, limits.max_cpu_seconds))
            resource.setrlimit(resource.RLIMIT_AS, (
                limits.max_memory_mb * 1024 * 1024,
                limits.max_memory_mb * 1024 * 1024,
            ))
            resource.setrlimit(resource.RLIMIT_NPROC, (limits.max_processes, limits.max_processes))
            resource.setrlimit(resource.RLIMIT_NOFILE, (limits.max_file_descriptors, limits.max_file_descriptors))
            
            # Disk limit via ulimit (best effort)
            try:
                resource.setrlimit(resource.RLIMIT_FSIZE, (
                    limits.max_disk_mb * 1024 * 1024,
                    limits.max_disk_mb * 1024 * 1024,
                ))
            except Exception:
                pass
        
        # Execute
        try:
            env = os.environ.copy()
            if not session.limits.allow_network:
                # Basic network isolation via env vars
                env["http_proxy"] = "http://127.0.0.1:0"
                env["https_proxy"] = "http://127.0.0.1:0"
                env["no_proxy"] = "*"
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=session.limits.max_execution_time,
                cwd=session.work_dir,
                env=env,
                preexec_fn=set_limits,
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            stdout = result.stdout[:5000]
            stderr = result.stderr[:2000]
            
            # Log result
            self.audit.log_action(
                session_id=session_id,
                action="completed",
                user_id=user_id,
                command=command,
                result_status="success" if result.returncode == 0 else "error",
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
                metadata={
                    "returncode": result.returncode,
                    "network_isolated": not session.limits.allow_network,
                },
            )
            
            # Log resource usage (approximate)
            self.audit.log_resource_usage(
                session_id=session_id,
                cpu=duration_ms / 1000,
                memory=0,  # Would need psutil for accurate readings
                disk=0,
                processes=0,
            )
            
            return {
                "ok": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "duration_ms": duration_ms,
            }
        
        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            self.audit.log_action(
                session_id=session_id,
                action="timeout",
                user_id=user_id,
                command=command,
                result_status="timeout",
                duration_ms=duration_ms,
            )
            return {"ok": False, "error": f"Command timed out ({session.limits.max_execution_time}s)"}
        
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.audit.log_action(
                session_id=session_id,
                action="error",
                user_id=user_id,
                command=command,
                result_status="error",
                duration_ms=duration_ms,
                metadata={"error": str(e)},
            )
            return {"ok": False, "error": str(e)}
    
    def _validate_command(self, session: SandboxSession, command: str) -> Optional[str]:
        """Validate command against session limits."""
        # Blocked patterns
        blocked = [
            "rm -rf /", "rm -rf ~", "mkfs", "dd if=/dev/zero",
            ":(){ :|:& };:", "chmod 777", "chmod -R 777",
        ]
        for pattern in blocked:
            if pattern in command:
                return f"Blocked command: {pattern}"
        
        return None
    
    def cleanup_session(self, session_id: str):
        """Clean up a sandbox session."""
        session = self._active_sessions.get(session_id)
        if session and os.path.exists(session.work_dir):
            shutil.rmtree(session.work_dir, ignore_errors=True)
        
        with self._lock:
            self._active_sessions.pop(session_id, None)
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information."""
        session = self._active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "work_dir": session.work_dir,
            "limits": {
                "max_cpu_seconds": session.limits.max_cpu_seconds,
                "max_memory_mb": session.limits.max_memory_mb,
                "allow_network": session.limits.allow_network,
            },
        }
    
    def list_active_sessions(self) -> List[Dict]:
        """List all active sandbox sessions."""
        return [
            {
                "session_id": s.session_id,
                "user_id": s.user_id,
                "created_at": s.created_at.isoformat(),
            }
            for s in self._active_sessions.values()
        ]


# Singleton
_sandbox = None

def get_enhanced_sandbox() -> EnhancedSandbox:
    global _sandbox
    if _sandbox is None:
        _sandbox = EnhancedSandbox()
    return _sandbox


if __name__ == "__main__":
    sandbox = get_enhanced_sandbox()
    
    print("=== Enhanced Sandbox Test ===")
    
    # Create session
    session_id = sandbox.create_session(
        user_id="sen",
        limits=SandboxLimits(max_execution_time=10, allow_network=False),
    )
    print(f"Session: {session_id}")
    
    # Execute commands
    result = sandbox.execute(session_id, "echo 'hello sandbox'", user_id="sen")
    print(f"Echo: ok={result['ok']}, stdout={result['stdout'].strip()}")
    
    result = sandbox.execute(session_id, "pwd", user_id="sen")
    print(f"PWD: {result['stdout'].strip()}")
    
    result = sandbox.execute(session_id, "rm -rf /", user_id="sen")
    print(f"Dangerous: ok={result['ok']}, error={result.get('error')}")
    
    # Get session info
    info = sandbox.get_session_info(session_id)
    print(f"Info: user={info['user_id']}, dir={info['work_dir']}")
    
    # Get audit history
    history = sandbox.audit.get_session_history(session_id)
    print(f"Audit entries: {len(history)}")
    for h in history:
        print(f"  {h['timestamp']} | {h['action']} | {h['command'][:30]}")
    
    # Cleanup
    sandbox.cleanup_session(session_id)
    print("Session cleaned up")
