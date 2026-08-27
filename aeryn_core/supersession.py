"""V39.49 — Supersession/Deprecation Workflow (Uteke-style).

Implements:
1. Mark memories as superseded by newer versions
2. Track supersession chains (A → B → C)
3. Flag superseded memories at recall time
4. Query current "live" version of a memory
5. Rollback/undo supersession
"""

import os
import sqlite3
import time
from typing import List, Dict, Optional

import sys
sys.path.insert(0, '/home/sen/aeryn-core-agent')

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/supersession.db")


class SupersessionManager:
    """Memory supersession workflow manager."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize supersession database."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Supersession records
            conn.execute("""
                CREATE TABLE IF NOT EXISTS supersessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    old_memory_id TEXT NOT NULL,
                    new_memory_id TEXT NOT NULL,
                    reason TEXT,
                    created_at REAL,
                    UNIQUE(old_memory_id, new_memory_id)
                )
            """)
            
            # Supersession chains for fast lookup
            conn.execute("""
                CREATE TABLE IF NOT EXISTS supersession_chains (
                    root_id TEXT,
                    leaf_id TEXT,
                    depth INTEGER,
                    PRIMARY KEY (root_id, leaf_id)
                )
            """)
            
            # Deprecated memories view
            conn.execute("""
                CREATE TABLE IF NOT EXISTS deprecated_memories (
                    memory_id TEXT PRIMARY KEY,
                    superseded_by TEXT,
                    deprecated_at REAL,
                    reason TEXT
                )
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def supersede(self, old_memory_id: str, new_memory_id: str, 
                  reason: str = "") -> bool:
        """
        Mark old_memory_id as superseded by new_memory_id.
        
        Creates a bidirectional relationship:
        - old → new (superseded_by)
        - new → old (supersedes)
        
        Updates the supersession chain for all related memories.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            now = time.time()
            
            # Insert supersession record
            conn.execute("""
                INSERT OR REPLACE INTO supersessions 
                (old_memory_id, new_memory_id, reason, created_at)
                VALUES (?, ?, ?, ?)
            """, (old_memory_id, new_memory_id, reason, now))
            
            # Mark old memory as deprecated
            conn.execute("""
                INSERT OR REPLACE INTO deprecated_memories
                (memory_id, superseded_by, deprecated_at, reason)
                VALUES (?, ?, ?, ?)
            """, (old_memory_id, new_memory_id, now, reason))
            
            # Update supersession chains
            # Find all chains where old_memory_id is the leaf
            cursor = conn.execute("""
                SELECT root_id FROM supersession_chains WHERE leaf_id = ?
            """, (old_memory_id,))
            
            roots = [row[0] for row in cursor.fetchall()]
            
            # If no existing chain, old_memory_id becomes its own root
            if not roots:
                roots = [old_memory_id]
                conn.execute("""
                    INSERT OR IGNORE INTO supersession_chains (root_id, leaf_id, depth)
                    VALUES (?, ?, 0)
                """, (old_memory_id, old_memory_id))
            
            # Create new chains with new_memory_id as leaf
            for root in roots:
                conn.execute("""
                    INSERT OR REPLACE INTO supersession_chains (root_id, leaf_id, depth)
                    VALUES (?, ?, ?)
                """, (root, new_memory_id, len(roots)))
            
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()
    
    def get_current_version(self, memory_id: str) -> str:
        """Get the current (latest) version of a memory."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT new_memory_id FROM supersessions
                WHERE old_memory_id = ?
                ORDER BY created_at DESC LIMIT 1
            """, (memory_id,))
            
            row = cursor.fetchone()
            if row:
                return self.get_current_version(row[0])
            return memory_id
        finally:
            conn.close()
    
    def get_superseded_chain(self, memory_id: str) -> List[Dict]:
        """Get the full supersession chain for a memory."""
        conn = sqlite3.connect(self.db_path)
        try:
            chain = []
            current = memory_id
            
            while current:
                cursor = conn.execute("""
                    SELECT old_memory_id, new_memory_id, reason, created_at
                    FROM supersessions WHERE old_memory_id = ?
                    ORDER BY created_at DESC LIMIT 1
                """, (current,))
                
                row = cursor.fetchone()
                if row:
                    chain.append({
                        "from": row[0],
                        "to": row[1],
                        "reason": row[2],
                        "timestamp": row[3]
                    })
                    current = row[1]
                else:
                    break
            
            return chain
        finally:
            conn.close()
    
    def is_deprecated(self, memory_id: str) -> bool:
        """Check if a memory has been superseded."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT 1 FROM deprecated_memories WHERE memory_id = ?
            """, (memory_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()
    
    def get_replacement(self, memory_id: str) -> Optional[str]:
        """Get the replacement for a deprecated memory."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT superseded_by FROM deprecated_memories WHERE memory_id = ?
            """, (memory_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()
    
    def restore_memory(self, memory_id: str) -> bool:
        """
        Undo supersession — restore a deprecated memory as current.
        Removes the supersession record but keeps history.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Get the replacement
            cursor = conn.execute("""
                SELECT superseded_by FROM deprecated_memories WHERE memory_id = ?
            """, (memory_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            new_memory_id = row[0]
            
            # Remove supersession record
            conn.execute("""
                DELETE FROM supersessions WHERE old_memory_id = ? AND new_memory_id = ?
            """, (memory_id, new_memory_id))
            
            # Remove from deprecated
            conn.execute("""
                DELETE FROM deprecated_memories WHERE memory_id = ?
            """, (memory_id,))
            
            # Update chains
            conn.execute("""
                DELETE FROM supersession_chains WHERE leaf_id = ?
            """, (new_memory_id,))
            
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()
    
    def get_deprecated_memories(self) -> List[Dict]:
        """Get all deprecated memories."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                SELECT memory_id, superseded_by, deprecated_at, reason
                FROM deprecated_memories
                ORDER BY deprecated_at DESC
            """)
            
            return [{
                "memory_id": row[0],
                "superseded_by": row[1],
                "deprecated_at": row[2],
                "reason": row[3]
            } for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def flag_if_deprecated(self, memories: List[Dict]) -> List[Dict]:
        """
        Flag deprecated memories in a list of results.
        Adds 'is_deprecated' and 'superseded_by' fields.
        """
        for mem in memories:
            mem_id = mem.get("memory_id", "")
            if self.is_deprecated(mem_id):
                mem["is_deprecated"] = True
                mem["superseded_by"] = self.get_replacement(mem_id)
            else:
                mem["is_deprecated"] = False
        return memories


# Singleton
_manager = None

def get_supersession_manager() -> SupersessionManager:
    global _manager
    if _manager is None:
        _manager = SupersessionManager()
    return _manager
