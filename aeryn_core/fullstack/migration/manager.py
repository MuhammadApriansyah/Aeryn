#!/usr/bin/env python3
"""Database Migration Manager."""
import os
import sqlite3
import time
import json
from typing import Dict, List, Optional

class MigrationManager:
    """Manage database migrations."""
    
    def __init__(self, db_path="app.db", migrations_dir="migrations"):
        self.db_path = db_path
        self.migrations_dir = migrations_dir
        self._ensure_migration_table()
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _ensure_migration_table(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                applied_at REAL
            )
        """)
        conn.commit()
        conn.close()
    
    def get_applied(self) -> List[str]:
        conn = self._get_conn()
        cursor = conn.execute("SELECT name FROM _migrations ORDER BY id")
        applied = [row[0] for row in cursor.fetchall()]
        conn.close()
        return applied
    
    def get_pending(self) -> List[Dict]:
        applied = set(self.get_applied())
        pending = []
        
        if os.path.exists(self.migrations_dir):
            for filename in sorted(os.listdir(self.migrations_dir)):
                if filename.endswith('.sql') and filename not in applied:
                    filepath = os.path.join(self.migrations_dir, filename)
                    with open(filepath, 'r') as f:
                        pending.append({
                            "name": filename,
                            "sql": f.read(),
                            "filepath": filepath,
                        })
        
        return pending
    
    def apply(self, name: str, sql: str):
        conn = self._get_conn()
        try:
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO _migrations (name, applied_at) VALUES (?, ?)",
                (name, time.time())
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def rollback(self, name: str):
        rollback_file = os.path.join(self.migrations_dir, f"{name}.rollback.sql")
        if not os.path.exists(rollback_file):
            raise FileNotFoundError(f"No rollback file for {name}")
        
        conn = self._get_conn()
        try:
            with open(rollback_file, 'r') as f:
                conn.executescript(f.read())
            conn.execute("DELETE FROM _migrations WHERE name = ?", (name,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def migrate(self):
        pending = self.get_pending()
        applied = []
        for migration in pending:
            self.apply(migration["name"], migration["sql"])
            applied.append(migration["name"])
        return applied
    
    def status(self) -> Dict:
        applied = self.get_applied()
        pending = self.get_pending()
        return {
            "applied": applied,
            "pending": [p["name"] for p in pending],
            "total": len(applied) + len(pending),
        }

migration_manager = MigrationManager()
