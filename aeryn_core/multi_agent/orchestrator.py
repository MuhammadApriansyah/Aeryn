#!/usr/bin/env python3
"""
V42.0 — Multi-Agent Orchestration Engine.
Coordinate multiple agents for complex workflows.
"""

import uuid
import time
import json
import sqlite3
import threading
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

DATABASE_DIR = Path.home() / "aeryn-core-agent" / "Personalisasi" / "Database"
DB_PATH = DATABASE_DIR / "multi_agent.db"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """A task to be executed by an agent."""
    
    def __init__(self, name: str, description: str, agent_id: str,
                 args: Dict = None, dependencies: List[str] = None,
                 priority: int = 5, timeout: int = 300):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.description = description
        self.agent_id = agent_id
        self.args = args or {}
        self.dependencies = dependencies or []
        self.priority = priority
        self.timeout = timeout
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None


class Workflow:
    """A workflow consisting of multiple tasks."""
    
    def __init__(self, name: str, description: str):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.description = description
        self.tasks: Dict[str, Task] = {}
        self.status = TaskStatus.PENDING
        self.created_at = time.time()
        self.completed_at = None
    
    def add_task(self, task: Task):
        self.tasks[task.id] = task
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (dependencies met)."""
        ready = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            deps_completed = all(
                self.tasks.get(dep_id, Task("", "", "")).status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            
            if deps_completed:
                ready.append(task)
        
        # Sort by priority (higher first)
        ready.sort(key=lambda t: t.priority, reverse=True)
        return ready


class MultiAgentOrchestrator:
    """Orchestrate multiple agents for complex workflows."""
    
    def __init__(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._agents: Dict[str, Dict] = {}
        self._workflows: Dict[str, Workflow] = {}
        self._init_db()
    
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    status TEXT,
                    created_at REAL,
                    completed_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT,
                    name TEXT,
                    agent_id TEXT,
                    status TEXT,
                    result TEXT,
                    error TEXT,
                    created_at REAL,
                    started_at REAL,
                    completed_at REAL
                )
            """)
            conn.commit()
            conn.close()
    
    def register_agent(self, agent_id: str, name: str, capabilities: List[str]):
        """Register an agent with the orchestrator."""
        self._agents[agent_id] = {
            "id": agent_id,
            "name": name,
            "capabilities": capabilities,
            "registered_at": time.time(),
        }
    
    def create_workflow(self, name: str, description: str) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow(name, description)
        self._workflows[workflow.id] = workflow
        
        with self._lock:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute(
                "INSERT INTO workflows (id, name, description, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (workflow.id, name, description, "pending", time.time())
            )
            conn.commit()
            conn.close()
        
        return workflow
    
    def execute_workflow(self, workflow_id: str) -> Dict:
        """Execute a workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}
        
        workflow.status = TaskStatus.RUNNING
        
        while True:
            ready_tasks = workflow.get_ready_tasks()
            if not ready_tasks:
                break
            
            for task in ready_tasks:
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()
                
                # Execute task
                result = self._execute_task(task)
                
                if result.get("error"):
                    task.status = TaskStatus.FAILED
                    task.error = result["error"]
                else:
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                
                task.completed_at = time.time()
        
        # Check if all tasks completed
        all_completed = all(t.status == TaskStatus.COMPLETED for t in workflow.tasks.values())
        workflow.status = TaskStatus.COMPLETED if all_completed else TaskStatus.FAILED
        workflow.completed_at = time.time()
        
        return {
            "workflow_id": workflow_id,
            "status": workflow.status.value,
            "tasks": len(workflow.tasks),
        }
    
    def _execute_task(self, task: Task) -> Dict:
        """Execute a single task."""
        agent = self._agents.get(task.agent_id)
        if not agent:
            return {"error": f"Agent '{task.agent_id}' not found"}
        
        # Simulate task execution
        return {
            "agent": agent["name"],
            "task": task.name,
            "result": f"Completed {task.name}",
        }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow status."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return None
        
        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status.value,
            "tasks": {
                tid: {"name": t.name, "status": t.status.value}
                for tid, t in workflow.tasks.items()
            }
        }


orchestrator = MultiAgentOrchestrator()
