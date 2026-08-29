#!/usr/bin/env python3
"""
V42.0 — Integration SDK.
SDK for third-party developers to build Aeryn integrations.
"""

import json
import time
import sqlite3
import threading
import urllib.request
from typing import Dict, List, Optional, Any
from pathlib import Path

DATABASE_DIR = Path.home() / "aeryn-core-agent" / "Personalisasi" / "Database"
DB_PATH = DATABASE_DIR / "integrations.db"


class IntegrationSDK:
    """SDK for building Aeryn integrations."""
    
    def __init__(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS integrations (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    author TEXT,
                    version TEXT,
                    category TEXT,
                    config_schema TEXT,
                    endpoint TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at REAL
                )
            """)
            conn.commit()
            conn.close()
    
    def register(self, name: str, description: str, author: str,
                 version: str, category: str, config_schema: Dict, endpoint: str):
        """Register an integration."""
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("""
                INSERT OR REPLACE INTO integrations (id, name, description, author, version, category, config_schema, endpoint, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, name, description, author, version, category, json.dumps(config_schema), endpoint, time.time()))
            conn.commit()
            conn.close()
    
    def list_integrations(self) -> List[Dict]:
        """List all integrations."""
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.execute("SELECT name, description, author, version, category, endpoint FROM integrations WHERE enabled = 1")
            integrations = [
                {"name": r[0], "description": r[1], "author": r[2], "version": r[3], "category": r[4], "endpoint": r[5]}
                for r in cursor.fetchall()
            ]
            conn.close()
        return integrations
    
    def call(self, name: str, action: str, args: Dict) -> Dict:
        """Call an integration."""
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.execute("SELECT endpoint FROM integrations WHERE name = ? AND enabled = 1", (name,))
            row = cursor.fetchone()
            conn.close()
        
        if not row:
            return {"error": f"Integration '{name}' not found"}
        
        endpoint = row[0]
        try:
            data = json.dumps({"action": action, "arguments": args}).encode()
            req = urllib.request.Request(endpoint, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}


integration_sdk = IntegrationSDK()
