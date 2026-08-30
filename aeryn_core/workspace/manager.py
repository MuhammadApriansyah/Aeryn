#!/usr/bin/env python3
"""Workspace Management — Multi-tenant workspace support."""
import os
import sqlite3
import threading
import time
from typing import Dict, List, Optional

DATABASE_DIR = os.path.join(os.path.expanduser("~"), "aeryn-core-agent", "Personalisasi", "Database")
DB_PATH = os.path.join(DATABASE_DIR, "workspaces.db")

class WorkspaceManager:
    def __init__(self):
        os.makedirs(DATABASE_DIR, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, description TEXT, created_at REAL, updated_at REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS workspace_members (id INTEGER PRIMARY KEY AUTOINCREMENT, workspace_id INTEGER, user_id TEXT, role TEXT, FOREIGN KEY(workspace_id) REFERENCES workspaces(id))")
            conn.execute("CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, workspace_id INTEGER, name TEXT, path TEXT, FOREIGN KEY(workspace_id) REFERENCES workspaces(id))")
            conn.commit()
            conn.close()
    
    def create_workspace(self, name: str, description: str = "", owner_id: str = "default") -> Dict:
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.execute("INSERT INTO workspaces (name, description, created_at, updated_at) VALUES (?, ?, ?, ?)", (name, description, time.time(), time.time()))
            ws_id = cursor.lastrowid
            conn.execute("INSERT INTO workspace_members (workspace_id, user_id, role) VALUES (?, ?, ?)", (ws_id, owner_id, "owner"))
            conn.commit()
            conn.close()
        return {"id": ws_id, "name": name, "description": description}
    
    def list_workspaces(self, user_id: str = "default") -> List[Dict]:
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.execute("SELECT w.id, w.name, w.description FROM workspaces w JOIN workspace_members m ON w.id = m.workspace_id WHERE m.user_id = ?", (user_id,))
            results = [{"id": r[0], "name": r[1], "description": r[2]} for r in cursor.fetchall()]
            conn.close()
        return results
    
    def add_project(self, workspace_id: int, name: str, path: str):
        with self._lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("INSERT INTO projects (workspace_id, name, path) VALUES (?, ?, ?)", (workspace_id, name, path))
            conn.commit()
            conn.close()

workspace_manager = WorkspaceManager()
