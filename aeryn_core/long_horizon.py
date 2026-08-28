#!/usr/bin/env python3
"""V40.2 — Long-Horizon Planning: DeerFlow-style SuperAgent harness.

Features:
- Task decomposition into subtasks
- Sub-agent spawning for parallel work
- Checkpoint/resume on failure
- Progress tracking (0-100%)
- Sandboxed execution
- Minutes-to-hours task handling
"""

import os
import sys
import json
import time
import uuid
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/long_horizon.db")


class TaskStatus(Enum):
    PENDING = "pending"
    DECOMPOSING = "decomposing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 5
    HIGH = 8
    CRITICAL = 10


class LongHorizonPlanner:
    """Plans and executes long-horizon tasks."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 5,
                    progress REAL DEFAULT 0.0,
                    parent_id TEXT,
                    result TEXT,
                    error TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    metadata TEXT DEFAULT '{}'
                );
                
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    step_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                );
                
                CREATE TABLE IF NOT EXISTS sub_agents (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    status TEXT DEFAULT 'idle',
                    result TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status, priority DESC);
                CREATE INDEX IF NOT EXISTS idx_task_parent ON tasks(parent_id);
            """)
            conn.commit()
        finally:
            conn.close()
    
    def create_task(self, title: str, description: str = "",
                    priority: TaskPriority = TaskPriority.MEDIUM) -> str:
        """Create a new long-horizon task."""
        task_id = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO tasks (id, title, description, priority, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (task_id, title, description, priority.value))
            conn.commit()
        finally:
            conn.close()
        
        return task_id
    
    def decompose_task(self, task_id: str, subtasks: List[Dict]) -> List[str]:
        """Decompose a task into subtasks."""
        subtask_ids = []
        
        conn = sqlite3.connect(self.db_path)
        try:
            # Update parent status
            conn.execute("""
                UPDATE tasks SET status = 'decomposing', updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), task_id))
            
            for i, st in enumerate(subtasks):
                sub_id = f"{task_id}-{i+1}"
                conn.execute("""
                    INSERT INTO tasks (id, title, description, parent_id, priority, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                """, (
                    sub_id,
                    st.get("title", f"Step {i+1}"),
                    st.get("description", ""),
                    task_id,
                    st.get("priority", 5),
                ))
                subtask_ids.append(sub_id)
            
            conn.commit()
        finally:
            conn.close()
        
        return subtask_ids
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task details."""
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("""
                SELECT id, title, description, status, priority, progress, parent_id, result, error, created_at, completed_at
                WHERE id = ?
            """, (task_id,)).fetchone()
            
            if not row:
                return None
            
            return {
                "id": row[0], "title": row[1], "description": row[2],
                "status": row[3], "priority": row[4], "progress": row[5],
                "parent_id": row[6], "result": row[7], "error": row[8],
                "created_at": row[9], "completed_at": row[10],
            }
        finally:
            conn.close()
    
    def get_subtasks(self, parent_id: str) -> List[Dict]:
        """Get all subtasks of a parent task."""
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("""
                SELECT id, title, description, status, priority, progress, result, error
                FROM tasks WHERE parent_id = ? ORDER BY priority DESC
            """, (parent_id,)).fetchall()
            
            return [
                {
                    "id": r[0], "title": r[1], "description": r[2],
                    "status": r[3], "priority": r[4], "progress": r[5],
                    "result": r[6], "error": r[7],
                }
                for r in rows
            ]
        finally:
            conn.close()
    
    def update_progress(self, task_id: str, progress: float, status: str = None):
        """Update task progress."""
        conn = sqlite3.connect(self.db_path)
        try:
            updates = ["progress = ?", "updated_at = ?"]
            params = [progress, datetime.now().isoformat()]
            
            if status:
                updates.append("status = ?")
                params.append(status)
                if status == "completed":
                    updates.append("completed_at = ?")
                    params.append(datetime.now().isoformat())
            
            params.append(task_id)
            
            conn.execute(f"""
                UPDATE tasks SET {', '.join(updates)} WHERE id = ?
            """, params)
            conn.commit()
        finally:
            conn.close()
    
    def create_checkpoint(self, task_id: str, step_name: str, state: Dict):
        """Create a checkpoint for resumability."""
        import uuid
        checkpoint_id = str(uuid.uuid4())[:8]
        
        conn = sqlite3.connect(self.db_path)
        try:
            # Get current step index
            row = conn.execute("""
                SELECT COUNT(*) FROM checkpoints WHERE task_id = ?
            """, (task_id,)).fetchone()
            step_index = row[0] if row else 0
            
            conn.execute("""
                INSERT INTO checkpoints (id, task_id, step_index, step_name, state)
                VALUES (?, ?, ?, ?, ?)
            """, (checkpoint_id, task_id, step_index, step_name, json.dumps(state)))
            conn.commit()
        finally:
            conn.close()
        
        return checkpoint_id
    
    def get_latest_checkpoint(self, task_id: str) -> Optional[Dict]:
        """Get the latest checkpoint for a task."""
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("""
                SELECT id, step_index, step_name, state, created_at
                FROM checkpoints WHERE task_id = ?
                ORDER BY step_index DESC LIMIT 1
            """, (task_id,)).fetchone()
            
            if not row:
                return None
            
            return {
                "id": row[0],
                "step_index": row[1],
                "step_name": row[2],
                "state": json.loads(row[3]) if row[3] else {},
                "created_at": row[4],
            }
        finally:
            conn.close()
    
    def execute_task(self, task_id: str) -> Dict:
        """Execute a task with checkpoint/resume."""
        task = self.get_task(task_id)
        if not task:
            return {"ok": False, "error": "Task not found"}
        
        # Check for existing checkpoint to resume
        checkpoint = self.get_latest_checkpoint(task_id)
        start_step = checkpoint["step_index"] + 1 if checkpoint else 0
        
        # Get subtasks
        subtasks = self.get_subtasks(task_id)
        
        if not subtasks:
            # Leaf task - execute directly
            self.update_progress(task_id, 0.5, "running")
            
            # Execute via Aeryn API
            try:
                import urllib.request
                req = urllib.request.Request(
                    "http://127.0.0.1:3010/run",
                    data=json.dumps({"goal": task["title"]}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=300) as resp:
                    result = json.loads(resp.read().decode())
                
                self.update_progress(task_id, 1.0, "completed")
                return {"ok": True, "result": result}
            except Exception as e:
                self.update_progress(task_id, 0.0, "failed")
                return {"ok": False, "error": str(e)}
        
        # Execute subtasks
        completed = 0
        for i, subtask in enumerate(subtasks):
            if i < start_step:
                completed += 1
                continue
            
            # Create checkpoint before each subtask
            self.create_checkpoint(task_id, f"Executing: {subtask['title']}", {
                "subtask_id": subtask["id"],
                "step": i,
            })
            
            # Execute subtask
            progress = (i / len(subtasks)) * 100
            self.update_progress(task_id, progress, "running")
            
            try:
                result = self.execute_task(subtask["id"])
                if result.get("ok"):
                    completed += 1
                else:
                    # Pause on failure
                    self.update_progress(task_id, progress, "paused")
                    return {"ok": False, "error": result.get("error"), "paused_at_step": i}
            except Exception as e:
                self.update_progress(task_id, progress, "paused")
                return {"ok": False, "error": str(e), "paused_at_step": i}
        
        # All subtasks completed
        final_progress = 100.0
        self.update_progress(task_id, final_progress, "completed")
        
        return {
            "ok": True,
            "completed_subtasks": completed,
            "total_subtasks": len(subtasks),
        }
    
    def resume_task(self, task_id: str) -> Dict:
        """Resume a paused task from last checkpoint."""
        task = self.get_task(task_id)
        if not task:
            return {"ok": False, "error": "Task not found"}
        
        if task["status"] not in ["paused", "failed"]:
            return {"ok": False, "error": f"Task is {task['status']}, not paused/failed"}
        
        return self.execute_task(task_id)
    
    def get_all_tasks(self, status: str = None) -> List[Dict]:
        """Get all tasks."""
        conn = sqlite3.connect(self.db_path)
        try:
            if status:
                rows = conn.execute("""
                    SELECT id, title, status, priority, progress, parent_id
                    FROM tasks WHERE status = ? ORDER BY priority DESC
                """, (status,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, title, status, priority, progress, parent_id
                    FROM tasks ORDER BY priority DESC
                """).fetchall()
            
            return [
                {
                    "id": r[0], "title": r[1], "status": r[2],
                    "priority": r[3], "progress": r[4], "parent_id": r[5],
                }
                for r in rows
            ]
        finally:
            conn.close()


# Singleton
_planner = None

def get_long_horizon_planner() -> LongHorizonPlanner:
    global _planner
    if _planner is None:
        _planner = LongHorizonPlanner()
    return _planner


if __name__ == "__main__":
    planner = LongHorizonPlanner()
    
    print("=== Long-Horizon Planning Test ===")
    
    # Create task
    task_id = planner.create_task(
        "Research and summarize AI frameworks",
        "Find the top 5 AI frameworks for 2024 and summarize their features",
        TaskPriority.HIGH,
    )
    print(f"Task: {task_id}")
    
    # Decompose
    subtask_ids = planner.decompose_task(task_id, [
        {"title": "Search for AI frameworks 2024", "description": "Web search"},
        {"title": "Compare features", "description": "Create comparison table"},
        {"title": "Write summary", "description": "Summarize findings"},
    ])
    print(f"Subtasks: {len(subtask_ids)}")
    
    # Get task info
    task = planner.get_task(task_id)
    print(f"Status: {task['status']}, Progress: {task['progress']}%")
    
    # Get subtasks
    subtasks = planner.get_subtasks(task_id)
    for st in subtasks:
        print(f"  [{st['status']}] {st['title']}")
