#!/usr/bin/env python3
"""V40.48 — Multi-Region Deploy: Geo-distribution and failover."""

import os, sys, json, sqlite3
from typing import Dict, List, Optional
from datetime import datetime
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "multi_region.db")

class MultiRegionDeploy:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS regions (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, location TEXT,
                endpoint TEXT, is_active INTEGER DEFAULT 1,
                latency_ms INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS deploy_targets (
                id TEXT PRIMARY KEY, region_id TEXT NOT NULL, service_name TEXT,
                status TEXT DEFAULT 'active', last_health_check TEXT,
                FOREIGN KEY (region_id) REFERENCES regions(id)
            );
            CREATE TABLE IF NOT EXISTS failover_log (
                id TEXT PRIMARY KEY, from_region TEXT, to_region TEXT,
                reason TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def add_region(self, name: str, location: str, endpoint: str) -> str:
        import uuid
        rid = str(uuid.uuid4())[:8]
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO regions (id, name, location, endpoint) VALUES (?,?,?,?)",
                     (rid, name, location, endpoint))
        conn.commit()
        conn.close()
        return rid
    
    def get_healthy_regions(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT * FROM regions WHERE is_active=1 ORDER BY latency_ms").fetchall()
        conn.close()
        return [{"id": r[0], "name": r[1], "location": r[2], "endpoint": r[3], "latency_ms": r[5]} for r in rows]

_mr = None
def get_multi_region() -> MultiRegionDeploy:
    global _mr
    if _mr is None: _mr = MultiRegionDeploy()
    return _mr
