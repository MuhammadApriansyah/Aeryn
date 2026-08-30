#!/usr/bin/env python3
"""Workspace Manager — Multi-tenant workspace management."""
import json
import datetime
import sqlite3
import threading
from typing import Dict, List, Optional

DATABASE_DIR = "Personalisasi/Database"
DB_PATH = f"{DATABASE_DIR}/workspaces.db"


class WorkspaceManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            conn.execute("CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, description TEXT, settings TEXT DEFAULT '{}', is_active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            conn.execute("CREATE TABLE IF NOT EXISTS workspace_members (id INTEGER PRIMARY KEY AUTOINCREMENT, workspace_id INTEGER NOT NULL, user_id TEXT NOT NULL, role TEXT DEFAULT 'member', joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE, UNIQUE(workspace_id, user_id))")
            conn.commit()
            conn.close()
    
    def create_workspace(self, name: str, description: str = "", owner_id: str = "default") -> int:
        with self._lock:
            conn = self._get_conn()
            cursor = conn.execute("INSERT INTO workspaces (name, description) VALUES (?, ?)", (name, description))
            ws_id = cursor.lastrowid
            conn.execute("INSERT INTO workspace_members (workspace_id, user_id, role) VALUES (?, ?, ?)", (ws_id, owner_id, "owner"))
            conn.commit()
            conn.close()
        return ws_id
    
    def list_workspaces(self, user_id: str = "default") -> List[Dict]:
        conn = self._get_conn()
        rows = conn.execute("SELECT w.* FROM workspaces w JOIN workspace_members m ON w.id = m.workspace_id WHERE m.user_id = ? AND w.is_active = 1 ORDER BY w.updated_at DESC", (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]


def get_workspace_manager():
    return WorkspaceManager()
