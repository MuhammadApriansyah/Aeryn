#!/usr/bin/env python3
"""
V42.0 — Memory Injection Defense.
Memory integrity verification and access audit.
"""

import time
import hashlib
import sqlite3
import threading
from typing import Dict, List, Optional
from pathlib import Path

DATABASE_DIR = Path.home() / "aeryn-core-agent" / "Personalisasi" / "Database"
DB_PATH = DATABASE_DIR / "memory_audit.db"


class MemoryGuard:
    """Memory integrity and audit."""
    
    def __init__(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    session_id TEXT,
                    action TEXT,
                    key TEXT,
                    value_hash TEXT,
                    source TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_session ON memory_audit(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON memory_audit(timestamp)")
            conn.commit()
            conn.close()
    
    def log_access(self, session_id: str, action: str, key: str, value: str, source: str = "system"):
        """Log memory access."""
        value_hash = hashlib.sha256(value.encode()).hexdigest()[:16]
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute(
                "INSERT INTO memory_audit (timestamp, session_id, action, key, value_hash, source) VALUES (?, ?, ?, ?, ?, ?)",
                (time.time(), session_id, action, key, value_hash, source)
            )
            conn.commit()
            conn.close()
    
    def verify_integrity(self, key: str, expected_hash: str) -> bool:
        """Verify memory value hasn't been tampered with."""
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.execute(
                "SELECT value_hash FROM memory_audit WHERE key = ? ORDER BY timestamp DESC LIMIT 1",
                (key,)
            )
            row = cursor.fetchone()
            conn.close()
        
        if not row:
            return False
        return row[0] == expected_hash
    
    def get_audit_trail(self, session_id: str, limit: int = 100) -> List[Dict]:
        """Get audit trail for a session."""
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.execute(
                "SELECT timestamp, action, key, value_hash, source FROM memory_audit WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
                (session_id, limit)
            )
            results = [
                {"timestamp": r[0], "action": r[1], "key": r[2], "hash": r[3], "source": r[4]}
                for r in cursor.fetchall()
            ]
            conn.close()
        return results
    
    def cleanup(self, days: int = 30):
        """Clean up old audit records."""
        cutoff = time.time() - (days * 86400)
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("DELETE FROM memory_audit WHERE timestamp < ?", (cutoff,))
            conn.commit()
            conn.close()


guard = MemoryGuard()
