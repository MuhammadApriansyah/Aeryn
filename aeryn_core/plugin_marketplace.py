#!/usr/bin/env python3
"""
V41.0 — Plugin Marketplace.
Registry dan validator untuk community plugins.
"""

import os
import json
import uuid
import re
import hashlib
import ast
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from aeryn_core.neon_db import get_neon
from aeryn_core.logger import info, warn, error


class PluginMarketplace:
    """Marketplace untuk plugin Aeryn."""
    
    def __init__(self):
        self.db = get_neon()
        self._init_table()
    
    def _init_table(self):
        """Inisialisasi tabel plugins."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS plugins (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                display_name TEXT,
                version TEXT DEFAULT '0.1.0',
                description TEXT DEFAULT '',
                author TEXT DEFAULT '',
                entry_point TEXT DEFAULT 'main.py',
                tags TEXT DEFAULT '[]',
                dependencies TEXT DEFAULT '[]',
                is_public INTEGER DEFAULT 0,
                is_verified INTEGER DEFAULT 0,
                download_count INTEGER DEFAULT 0,
                rating_avg REAL DEFAULT 0.0,
                rating_count INTEGER DEFAULT 0,
                source_code TEXT,
                icon_url TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_plugins_public ON plugins(is_public, created_at DESC);
        """)
    
    def publish(self, user_id: str, name: str, source_code: str,
                display_name: str = None, description: str = None,
                version: str = "0.1.0", tags: List[str] = None,
                dependencies: List[str] = None, entry_point: str = "main.py",
                is_public: bool = True) -> Optional[Dict]:
        """Publish plugin ke marketplace."""
        # Validate name
        if not re.match(r'^[a-z][a-z0-9_]*$', name):
            warn("Invalid plugin name", name=name)
            return None
        
        # Validate source code syntax
        try:
            ast.parse(source_code)
        except SyntaxError as e:
            warn("Invalid source code", name=name, error=str(e))
            return None
        
        # Check if plugin exists
        existing = self.db.fetchone(
            "SELECT id FROM plugins WHERE name = %s",
            (name,)
        )
        
        if existing:
            # Update existing
            self.db.execute("""
                UPDATE plugins SET
                    display_name = %s, description = %s, version = %s,
                    tags = %s, dependencies = %s, entry_point = %s,
                    source_code = %s, is_public = %s, updated_at = %s
                WHERE name = %s
            """, (
                display_name or name,
                description or "",
                version,
                json.dumps(tags or []),
                json.dumps(dependencies or []),
                entry_point,
                source_code,
                is_public,
                datetime.now(),
                name,
            ))
            plugin_id = existing['id']
            info("Plugin updated", name=name, user_id=user_id)
        else:
            # Create new
            plugin_id = f"pl_{uuid.uuid4().hex[:12]}"
            self.db.insert('plugins', {
                'id': plugin_id,
                'user_id': user_id,
                'name': name,
                'display_name': display_name or name,
                'version': version,
                'description': description or '',
                'entry_point': entry_point,
                'tags': json.dumps(tags or []),
                'dependencies': json.dumps(dependencies or []),
                'is_public': is_public,
                'source_code': source_code,
            })
            info("Plugin published", name=name, user_id=user_id)
        
        return {
            "id": plugin_id,
            "name": name,
            "version": version,
        }
    
    def get(self, plugin_id: str) -> Optional[Dict]:
        """Get plugin by ID."""
        return self.db.fetchone(
            "SELECT * FROM plugins WHERE id = %s",
            (plugin_id,)
        )
    
    def search(self, query: str = None, tags: List[str] = None,
               limit: int = 20, offset: int = 0) -> List[Dict]:
        """Search plugins."""
        if query:
            return self.db.fetchall("""
                SELECT id, name, display_name, version, description, author,
                       tags, download_count, rating_avg, is_verified
                FROM plugins
                WHERE is_public = 1 AND (name ILIKE %s OR display_name ILIKE %s)
                ORDER BY download_count DESC, rating_avg DESC
                LIMIT %s OFFSET %s
            """, (f"%{query}%", f"%{query}%", limit, offset))
        else:
            return self.db.fetchall("""
                SELECT id, name, display_name, version, description, author,
                       tags, download_count, rating_avg, is_verified
                FROM plugins
                WHERE is_public = 1
                ORDER BY download_count DESC, rating_avg DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
    
    def list_user_plugins(self, user_id: str) -> List[Dict]:
        """List plugin milik user."""
        return self.db.fetchall("""
            SELECT id, name, display_name, version, is_public, download_count, rating_avg
            FROM plugins
            WHERE user_id = %s
            ORDER BY updated_at DESC
        """, (user_id,))
    
    def rate(self, plugin_id: str, user_id: str, rating: float) -> bool:
        """Rate plugin (1-5)."""
        if rating < 1 or rating > 5:
            return False
        
        # Simple rating update
        plugin = self.db.fetchone(
            "SELECT rating_avg, rating_count FROM plugins WHERE id = %s",
            (plugin_id,)
        )
        
        if not plugin:
            return False
        
        new_count = (plugin.get('rating_count') or 0) + 1
        old_avg = plugin.get('rating_avg') or 0
        new_avg = ((old_avg * (new_count - 1)) + rating) / new_count
        
        self.db.execute("""
            UPDATE plugins SET rating_avg = %s, rating_count = %s WHERE id = %s
        """, (new_avg, new_count, plugin_id))
        
        return True
    
    def increment_download(self, plugin_id: str):
        """Increment download count."""
        self.db.execute("""
            UPDATE plugins SET download_count = download_count + 1 WHERE id = %s
        """, (plugin_id,))


# Singleton
_plugin_marketplace = None

def get_plugin_marketplace() -> PluginMarketplace:
    global _plugin_marketplace
    if _plugin_marketplace is None:
        _plugin_marketplace = PluginMarketplace()
    return _plugin_marketplace
