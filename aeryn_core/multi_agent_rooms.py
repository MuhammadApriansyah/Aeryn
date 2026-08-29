#!/usr/bin/env python3
"""V39.74 — Multi-Agent Rooms: Shared memory across agent instances.

Allows multiple Aeryn instances to share:
- Common room/space state
- Shared memories within a room
- Cross-agent recall
"""

import os
import sys
import json
import time
import sqlite3
import threading
from typing import List, Dict, Optional
from datetime import datetime
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

DB_PATH = os.path.join(DATABASE_DIR, "multi_agent_rooms.db")


class Room:
    """A shared space for agents to collaborate."""
    
    def __init__(self, room_id: str, name: str, description: str = ""):
        self.room_id = room_id
        self.name = name
        self.description = description
        self.created_at = datetime.now().isoformat()
        self.agents: List[str] = []
        self.shared_memories: List[Dict] = []
    
    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "agents": self.agents,
            "shared_memories": self.shared_memories,
        }


class MultiAgentRoomManager:
    """Manage rooms and shared state across agents."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize database."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS rooms (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    agents TEXT DEFAULT '[]'
                );
                
                CREATE TABLE IF NOT EXISTS room_memories (
                    id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL,
                    agent_id TEXT DEFAULT 'default',
                    content TEXT NOT NULL,
                    memory_type TEXT DEFAULT 'note',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (room_id) REFERENCES rooms(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_room_memories ON room_memories(room_id, created_at DESC);
            """)
            conn.commit()
        finally:
            conn.close()
    
    def create_room(self, name: str, description: str = "") -> str:
        """Create a new room."""
        import uuid
        room_id = str(uuid.uuid4())[:8]
        
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    INSERT INTO rooms (id, name, description, agents)
                    VALUES (?, ?, ?, ?)
                """, (room_id, name, description, "[]"))
                conn.commit()
            finally:
                conn.close()
        
        return room_id
    
    def get_room(self, room_id: str) -> Optional[dict]:
        """Get room info."""
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("""
                SELECT id, name, description, created_at, agents FROM rooms WHERE id = ?
            """, (room_id,)).fetchone()
            
            if not row:
                return None
            
            return {
                "room_id": row[0],
                "name": row[1],
                "description": row[2],
                "created_at": row[3],
                "agents": json.loads(row[4]) if row[4] else [],
            }
        finally:
            conn.close()
    
    def list_rooms(self) -> List[dict]:
        """List all rooms."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, name, description, created_at FROM rooms ORDER BY created_at DESC
            """).fetchall()
            
            return [
                {"room_id": r[0], "name": r[1], "description": r[2], "created_at": r[3]}
                for r in rows
            ]
        finally:
            conn.close()
    
    def add_agent_to_room(self, room_id: str, agent_id: str):
        """Add an agent to a room."""
        room = self.get_room(room_id)
        if not room:
            return False
        
        agents = room["agents"]
        if agent_id not in agents:
            agents.append(agent_id)
            
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                try:
                    conn.execute("""
                        UPDATE rooms SET agents = ? WHERE id = ?
                    """, (json.dumps(agents), room_id))
                    conn.commit()
                finally:
                    conn.close()
        
        return True
    
    def add_memory(self, room_id: str, content: str, agent_id: str = "default",
                   memory_type: str = "note", metadata: dict = None) -> str:
        """Add a shared memory to a room."""
        import uuid
        memory_id = str(uuid.uuid4())[:8]
        
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    INSERT INTO room_memories (id, room_id, agent_id, content, memory_type, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (memory_id, room_id, agent_id, content, memory_type,
                      json.dumps(metadata or {})))
                conn.commit()
            finally:
                conn.close()
        
        return memory_id
    
    def get_memories(self, room_id: str, limit: int = 20) -> List[dict]:
        """Get shared memories in a room."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, agent_id, content, memory_type, created_at, metadata
                FROM room_memories WHERE room_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (room_id, limit)).fetchall()
            
            return [
                {
                    "id": r[0], "agent_id": r[1], "content": r[2],
                    "memory_type": r[3], "created_at": r[4],
                    "metadata": json.loads(r[5]) if r[5] else {}
                }
                for r in rows
            ]
        finally:
            conn.close()
    
    def search_memories(self, room_id: str, query: str) -> List[dict]:
        """Search memories in a room."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, agent_id, content, memory_type, created_at
                FROM room_memories WHERE room_id = ? AND content LIKE ?
                ORDER BY created_at DESC
            """, (room_id, f"%{query}%")).fetchall()
            
            return [
                {
                    "id": r[0], "agent_id": r[1], "content": r[2],
                    "memory_type": r[3], "created_at": r[4]
                }
                for r in rows
            ]
        finally:
            conn.close()


# Singleton
_manager = None

def get_room_manager() -> MultiAgentRoomManager:
    global _manager
    if _manager is None:
        _manager = MultiAgentRoomManager()
    return _manager


if __name__ == "__main__":
    mgr = MultiAgentRoomManager()
    
    print("=== Multi-Agent Rooms Test ===")
    
    # Create room
    room_id = mgr.create_room("Project Aeryn", "Main project collaboration")
    print(f"Room created: {room_id}")
    
    # Add agents
    mgr.add_agent_to_room(room_id, "aeryn-1")
    mgr.add_agent_to_room(room_id, "aeryn-2")
    
    # Add memories
    mgr.add_memory(room_id, "Deploy v1.2 to staging", "aeryn-1", "task")
    mgr.add_memory(room_id, "All tests passed", "aeryn-2", "update")
    mgr.add_memory(room_id, "Need to update docs", "aeryn-1", "note")
    
    # Get memories
    memories = mgr.get_memories(room_id)
    print(f"Room memories: {len(memories)}")
    for m in memories:
        print(f"  [{m['agent_id']}] {m['content']}")
    
    # Search
    results = mgr.search_memories(room_id, "test")
    print(f"Search 'test': {len(results)} results")
    
    # Room info
    room = mgr.get_room(room_id)
    print(f"Room: {room['name']} | Agents: {room['agents']}")
