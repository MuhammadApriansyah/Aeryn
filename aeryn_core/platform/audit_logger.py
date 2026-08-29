#!/usr/bin/env python3
"""
V41.0 — Audit Logging.
Mencatat semua aksi user ke PostgreSQL.
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from aeryn_core.database.neon_db import get_neon
from aeryn_core.utils.logger import info, warn


class AuditLogger:
    """Mencatat semua aksi user."""
    
    def __init__(self):
        self.db = get_neon()
        self._init_table()
    
    def _init_table(self):
        """Inisialisasi tabel audit_log."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT,
                resource_id TEXT,
                ip_address TEXT,
                user_agent TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id, created_at DESC);
        """)
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action, created_at DESC);
        """)
    
    def log(self, user_id: str, action: str, resource: str = None,
            resource_id: str = None, ip_address: str = None,
            user_agent: str = None, metadata: Dict = None):
        """Catat aksi user."""
        self.db.insert('audit_log', {
            'id': uuid.uuid4().hex,
            'user_id': user_id,
            'action': action,
            'resource': resource or '',
            'resource_id': resource_id or '',
            'ip_address': ip_address or '',
            'user_agent': user_agent or '',
            'metadata': metadata or {},
        })
    
    def get_user_actions(self, user_id: str, limit: int = 100) -> list:
        """Dapatkan riwayat aksi user."""
        return self.db.fetchall("""
            SELECT action, resource, resource_id, ip_address, metadata, created_at
            FROM audit_log
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user_id, limit))
    
    def get_recent_actions(self, limit: int = 100) -> list:
        """Dapatkan aksi terbaru (semua user)."""
        return self.db.fetchall("""
            SELECT user_id, action, resource, resource_id, created_at
            FROM audit_log
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))


# Singleton
_audit_logger = None

def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
