#!/usr/bin/env python3
"""V40.34 — Multi-Tenant: Per-user data isolation and resource quotas."""

import os, sys, json, sqlite3, hashlib
from typing import Dict, List, Optional
from datetime import datetime
from aeryn_core.utils.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "multi_tenant.db")

class MultiTenant:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tenants (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, domain TEXT UNIQUE,
                is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tenant_users (
                id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, user_id TEXT NOT NULL,
                role TEXT DEFAULT 'member', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            );
            CREATE TABLE IF NOT EXISTS quotas (
                tenant_id TEXT PRIMARY KEY, max_users INTEGER DEFAULT 10,
                max_storage_mb INTEGER DEFAULT 1000, max_requests_per_day INTEGER DEFAULT 10000,
                current_storage_mb INTEGER DEFAULT 0, current_requests INTEGER DEFAULT 0,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            );
        """)
        conn.commit()
        conn.close()
    
    def create_tenant(self, name: str, domain: str) -> str:
        import uuid
        tid = str(uuid.uuid4())[:8]
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO tenants (id, name, domain) VALUES (?,?,?)", (tid, name, domain))
        conn.execute("INSERT INTO quotas (tenant_id) VALUES (?)", (tid,))
        conn.commit()
        conn.close()
        return tid
    
    def add_user(self, tenant_id: str, user_id: str, role: str = "member") -> str:
        import uuid
        uid = str(uuid.uuid4())[:8]
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO tenant_users (id, tenant_id, user_id, role) VALUES (?,?,?,?)",
                     (uid, tenant_id, user_id, role))
        conn.commit()
        conn.close()
        return uid
    
    def check_quota(self, tenant_id: str) -> Dict:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT * FROM quotas WHERE tenant_id=?", (tenant_id,)).fetchone()
        conn.close()
        if not row:
            return {"ok": False, "error": "Tenant not found"}
        return {
            "ok": True,
            "max_users": row[1],
            "max_storage_mb": row[2],
            "max_requests_per_day": row[3],
            "current_storage_mb": row[4],
            "current_requests": row[5],
        }

_mt = None
def get_multi_tenant() -> MultiTenant:
    global _mt
    if _mt is None: _mt = MultiTenant()
    return _mt
