#!/usr/bin/env python3
"""V40.1 — Multi-Agent Collaboration: A2A Protocol + Shared Task Queue.

Implements:
- Agent-to-agent communication protocol
- Shared task queue across agent instances
- Lead/worker coordination pattern
- Cross-agent memory sharing via broadcast
"""

import os
import sys
import json
import time
import uuid
import sqlite3
import threading
from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(DATABASE_DIR, "multi_agent.db")


class AgentRole(Enum):
    LEAD = "lead"
    WORKER = "worker"
    COORDINATOR = "coordinator"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 5
    HIGH = 8
    CRITICAL = 10


class A2AMessage:
    """Agent-to-agent message."""
    
    def __init__(self, sender: str, receiver: str, msg_type: str,
                 payload: Dict, priority: TaskPriority = TaskPriority.MEDIUM):
        self.id = str(uuid.uuid4())[:12]
        self.sender = sender
        self.receiver = receiver
        self.msg_type = msg_type
        self.payload = payload
        self.priority = priority
        self.timestamp = datetime.now().isoformat()
        self.status = "pending"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "msg_type": self.msg_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "status": self.status,
        }


class MultiAgentOrchestrator:
    """Orchestrates multiple agent instances."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._lock = threading.Lock()
        self._agents: Dict[str, Dict] = {}
        self._message_handlers: Dict[str, Callable] = {}
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT DEFAULT 'worker',
                    capabilities TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'active',
                    last_heartbeat TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS shared_tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    assigned_to TEXT,
                    assigned_by TEXT,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 5,
                    result TEXT,
                    error TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    parent_id TEXT
                );
                
                CREATE TABLE IF NOT EXISTS a2a_messages (
                    id TEXT PRIMARY KEY,
                    sender TEXT NOT NULL,
                    receiver TEXT NOT NULL,
                    msg_type TEXT NOT NULL,
                    payload TEXT DEFAULT '{}',
                    priority INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    processed_at TEXT
                );
                
                CREATE TABLE IF NOT EXISTS shared_memory (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    visibility TEXT DEFAULT 'public',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON shared_tasks(status, priority DESC);
                CREATE INDEX IF NOT EXISTS idx_messages_receiver ON a2a_messages(receiver, status);
                CREATE INDEX IF NOT EXISTS idx_shared_mem ON shared_memory(visibility, created_at DESC);
            """)
            conn.commit()
        finally:
            conn.close()
    
    def register_agent(self, name: str, role: AgentRole = AgentRole.WORKER,
                       capabilities: List[str] = None) -> str:
        """Register a new agent."""
        agent_id = str(uuid.uuid4())[:8]
        
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    INSERT INTO agents (id, name, role, capabilities, last_heartbeat)
                    VALUES (?, ?, ?, ?, ?)
                """, (agent_id, name, role.value, json.dumps(capabilities or []),
                      datetime.now().isoformat()))
                conn.commit()
            finally:
                conn.close()
        
        self._agents[agent_id] = {
            "name": name,
            "role": role,
            "capabilities": capabilities or [],
            "status": "active",
        }
        
        return agent_id
    
    def heartbeat(self, agent_id: str):
        """Update agent heartbeat."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                UPDATE agents SET last_heartbeat = ? WHERE id = ?
            """, (datetime.now().isoformat(), agent_id))
            conn.commit()
        finally:
            conn.close()
    
    def get_active_agents(self) -> List[Dict]:
        """Get all active agents."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, name, role, capabilities, status FROM agents
                WHERE status = 'active'
                ORDER BY role, name
            """).fetchall()
            
            return [
                {
                    "id": r[0], "name": r[1], "role": r[2],
                    "capabilities": json.loads(r[3]) if r[3] else [],
                    "status": r[4],
                }
                for r in rows
            ]
        finally:
            conn.close()
    
    def create_task(self, title: str, description: str = "",
                    assigned_to: str = None, assigned_by: str = None,
                    priority: TaskPriority = TaskPriority.MEDIUM,
                    parent_id: str = None) -> str:
        """Create a shared task."""
        task_id = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO shared_tasks (id, title, description, assigned_to,
                                          assigned_by, priority, parent_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (task_id, title, description, assigned_to, assigned_by,
                  priority.value, parent_id))
            conn.commit()
        finally:
            conn.close()
        
        return task_id
    
    def get_tasks(self, assigned_to: str = None, status: str = None) -> List[Dict]:
        """Get tasks with optional filters."""
        conn = sqlite3.connect(self.db_path)
        try:
            query = "SELECT * FROM shared_tasks WHERE 1=1"
            params = []
            
            if assigned_to:
                query += " AND assigned_to = ?"
                params.append(assigned_to)
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY priority DESC, created_at"
            rows = conn.execute(query, params).fetchall()
            
            columns = ["id", "title", "description", "assigned_to", "assigned_by",
                      "status", "priority", "result", "error", "created_at",
                      "completed_at", "parent_id"]
            
            return [dict(zip(columns, r)) for r in rows]
        finally:
            conn.close()
    
    def complete_task(self, task_id: str, result: str = None, error: str = None):
        """Mark a task as completed."""
        conn = sqlite3.connect(self.db_path)
        try:
            status = "completed" if not error else "failed"
            conn.execute("""
                UPDATE shared_tasks
                SET status = ?, result = ?, error = ?, completed_at = ?
                WHERE id = ?
            """, (status, result, error, datetime.now().isoformat(), task_id))
            conn.commit()
        finally:
            conn.close()
    
    def send_message(self, sender: str, receiver: str, msg_type: str,
                     payload: Dict, priority: TaskPriority = TaskPriority.MEDIUM) -> str:
        """Send an A2A message."""
        msg = A2AMessage(sender, receiver, msg_type, payload, priority)
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO a2a_messages (id, sender, receiver, msg_type, payload, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (msg.id, msg.sender, msg.receiver, msg.msg_type,
                  json.dumps(msg.payload), msg.priority.value))
            conn.commit()
        finally:
            conn.close()
        
        return msg.id
    
    def get_messages(self, receiver: str, status: str = "pending") -> List[Dict]:
        """Get pending messages for an agent."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, sender, receiver, msg_type, payload, priority, created_at
                FROM a2a_messages WHERE receiver = ? AND status = ?
                ORDER BY priority DESC, created_at
            """, (receiver, status)).fetchall()
            
            return [
                {
                    "id": r[0], "sender": r[1], "receiver": r[2],
                    "msg_type": r[3], "payload": json.loads(r[4]) if r[4] else {},
                    "priority": r[5], "created_at": r[6],
                }
                for r in rows
            ]
        finally:
            conn.close()
    
    def process_message(self, msg_id: str):
        """Mark message as processed."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                UPDATE a2a_messages SET status = 'processed', processed_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), msg_id))
            conn.commit()
        finally:
            conn.close()
    
    def share_memory(self, agent_id: str, memory_type: str, content: str,
                     visibility: str = "public") -> str:
        """Share memory across agents."""
        mem_id = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO shared_memory (id, agent_id, memory_type, content, visibility)
                VALUES (?, ?, ?, ?, ?)
            """, (mem_id, agent_id, memory_type, content, visibility))
            conn.commit()
        finally:
            conn.close()
        
        return mem_id
    
    def get_shared_memory(self, agent_id: str = None, visibility: str = "public",
                          limit: int = 20) -> List[Dict]:
        """Get shared memory."""
        conn = sqlite3.connect(self.db_path)
        try:
            if agent_id:
                rows = conn.execute("""
                    SELECT id, agent_id, memory_type, content, visibility, created_at
                    FROM shared_memory WHERE agent_id = ? AND visibility = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (agent_id, visibility, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, agent_id, memory_type, content, visibility, created_at
                    FROM shared_memory WHERE visibility = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (visibility, limit)).fetchall()
            
            return [
                {
                    "id": r[0], "agent_id": r[1], "memory_type": r[2],
                    "content": r[3], "visibility": r[4], "created_at": r[5],
                }
                for r in rows
            ]
        finally:
            conn.close()
    
    def decompose_task(self, title: str, subtasks: List[str],
                       lead_id: str = None) -> List[str]:
        """Decompose a task into subtasks."""
        parent_id = self.create_task(title, assigned_by=lead_id)
        
        subtask_ids = []
        for subtask_title in subtasks:
            tid = self.create_task(
                subtask_title,
                parent_id=parent_id,
                assigned_by=lead_id,
            )
            subtask_ids.append(tid)
        
        return subtask_ids


# Singleton
_orchestrator = None

def get_multi_agent_orchestrator() -> MultiAgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiAgentOrchestrator()
    return _orchestrator


if __name__ == "__main__":
    orchestrator = MultiAgentOrchestrator()
    
    print("=== Multi-Agent Collaboration Test ===")
    
    # Register agents
    lead_id = orchestrator.register_agent("Lead", AgentRole.LEAD, ["planning", "coordination"])
    worker1_id = orchestrator.register_agent("Worker-1", AgentRole.WORKER, ["coding", "debugging"])
    worker2_id = orchestrator.register_agent("Worker-2", AgentRole.WORKER, ["research", "writing"])
    
    print(f"Registered: Lead={lead_id}, W1={worker1_id}, W2={worker2_id}")
    
    # Create tasks
    task_ids = orchestrator.decompose_task("Build feature X", [
        "Research existing solutions",
        "Write implementation",
        "Test and debug",
    ], lead_id=lead_id)
    print(f"Decomposed into {len(task_ids)} subtasks")
    
    # Send messages
    orchestrator.send_message(lead_id, worker1_id, "task_assigned", {"task_id": task_ids[1]})
    orchestrator.send_message(lead_id, worker2_id, "task_assigned", {"task_id": task_ids[0]})
    
    # Share memory
    orchestrator.share_memory(worker2_id, "research", "Found 3 relevant libraries", "public")
    
    # Check messages
    msgs = orchestrator.get_messages(worker1_id)
    print(f"Worker-1 messages: {len(msgs)}")
    
    # Shared memory
    memory = orchestrator.get_shared_memory()
    print(f"Shared memory entries: {len(memory)}")
    
    # Active agents
    agents = orchestrator.get_active_agents()
    print(f"Active agents: {len(agents)}")
