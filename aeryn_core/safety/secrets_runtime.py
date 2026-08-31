#!/usr/bin/env python3
"""V41.0 — Phase 3: Secrets Management + Plugin Runtime."""

import os, json, sqlite3, secrets
from typing import Dict, Optional
from aeryn_core.utils.config import BASE_DIR, VAULT_DIR, DATABASE_DIR


class SecretsManager:
    """Simple secrets vault for API keys and tokens."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(DATABASE_DIR, "secrets.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS secrets (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_secret_name ON secrets(user_id, name);
        """)
        conn.commit()
        conn.close()
    
    def set(self, user_id: str, name: str, value: str, description: str = None):
        import uuid
        from datetime import datetime
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO secrets (id, user_id, name, value, description, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4())[:12], user_id, name, value, description, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    
    def get(self, user_id: str, name: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT value FROM secrets WHERE user_id = ? AND name = ?",
            (user_id, name)
        ).fetchone()
        conn.close()
        return row[0] if row else None
    
    def list(self, user_id: str) -> list:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT name, description, created_at FROM secrets WHERE user_id = ?",
            (user_id,)
        ).fetchall()
        conn.close()
        return [{"name": r[0], "description": r[1], "created_at": r[2]} for r in rows]


class PluginRuntime:
    """Execute plugins in isolated processes."""
    
    def __init__(self, plugins_dir: str = None):
        self.plugins_dir = plugins_dir or os.path.expanduser(
            "~/aeryn-core-agent/plugins"
        )
        os.makedirs(self.plugins_dir, exist_ok=True)
    
    def list_plugins(self) -> list:
        """List installed plugins."""
        plugins = []
        if not os.path.isdir(self.plugins_dir):
            return plugins
        
        for entry in os.listdir(self.plugins_dir):
            plugin_dir = os.path.join(self.plugins_dir, entry)
            if os.path.isdir(plugin_dir):
                manifest_path = os.path.join(plugin_dir, "plugin.json")
                if os.path.exists(manifest_path):
                    with open(manifest_path) as f:
                        plugins.append(json.load(f))
        return plugins
    
    def run_plugin(self, plugin_name: str, action: str, params: dict = None) -> dict:
        """Run a plugin action."""
        plugin_dir = os.path.join(self.plugins_dir, plugin_name)
        manifest_path = os.path.join(plugin_dir, "plugin.json")
        
        if not os.path.exists(manifest_path):
            return {"error": f"Plugin not found: {plugin_name}"}
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        # Find the action - check both 'actions' and 'tools' keys
        actions = manifest.get("actions", {})
        tools = manifest.get("tools", [])
        
        # If no actions, build from tools
        if not actions and tools:
            for tool in tools:
                actions[tool["name"]] = tool
        
        if action not in actions:
            return {"error": f"Action not found: {action}"}
        
        action_config = actions[action]
        entry_point = action_config.get("entry_point", "main.py")
        entry_path = os.path.join(plugin_dir, entry_point)
        
        if not os.path.exists(entry_path):
            return {"error": f"Entry point not found: {entry_point}"}
        
        # Execute
        import subprocess
        try:
            proc = subprocess.run(
                ["python3", entry_path, json.dumps(params or {})],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=plugin_dir,
            )
            return {
                "ok": proc.returncode == 0,
                "stdout": proc.stdout[:5000],
                "stderr": proc.stderr[:1000],
            }
        except subprocess.TimeoutExpired:
            return {"error": "Plugin timed out"}
        except Exception as e:
            return {"error": str(e)}


# ── Singletons ────────────────────────────────

_secrets: Optional[SecretsManager] = None
_plugin_runtime: Optional[PluginRuntime] = None

def get_secrets_manager() -> SecretsManager:
    global _secrets
    if _secrets is None:
        _secrets = SecretsManager()
    return _secrets

def get_plugin_runtime() -> PluginRuntime:
    global _plugin_runtime
    if _plugin_runtime is None:
        _plugin_runtime = PluginRuntime()
    return _plugin_runtime
