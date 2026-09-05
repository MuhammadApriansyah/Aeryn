"""Execution Runtime — durable task queue + background worker.

Per research (AWS/Azure production playbook):
- "Standard HTTP endpoint timeout 30s doesn't work for agents"
- Agents run 20 min (support) to 4 hours (research)
- Need durable queue that survives restart + long-running session support

Design:
- TaskQueue: SQLite-backed durable queue (survives restart)
- Background worker: threads that process tasks out of HTTP request cycle
- Task states: pending → running → completed | failed | awaiting_approval

No external dependency (Celery/RQ) — pure SQLite + threading, suitable
for proot/headless single-node deployment.
"""

import os
import json
import sqlite3
import threading
import time
import uuid
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from aeryn_core.utils.config import DATABASE_DIR


@dataclass
class Task:
    """A durable task in the queue."""
    id: str
    type: str
    payload: Dict[str, Any]
    status: str = "pending"  # pending | running | completed | failed | awaiting_approval
    result: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    session_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "payload": self.payload,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "session_id": self.session_id,
        }


class TaskQueue:
    """Durable task queue (PG-backed when available)."""

    def __init__(self, db_path: str = None):
        from aeryn_core.runtime.state_sharing import shared_connect
        self._shared_connect = shared_connect
        self.db_path = db_path or os.path.join(DATABASE_DIR, "tasks.db")
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        return self._shared_connect("tasks")

    def _init_db(self):
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    result TEXT DEFAULT '{}',
                    error TEXT DEFAULT '',
                    created_at REAL,
                    started_at REAL,
                    finished_at REAL,
                    session_id TEXT DEFAULT ''
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            conn.close()

    def enqueue(self, type: str, payload: Dict[str, Any], session_id: str = "") -> Task:
        """Add a task to the queue."""
        task = Task(
            id=str(uuid.uuid4().hex[:16]),
            type=type,
            payload=payload,
            session_id=session_id,
        )
        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT INTO tasks (id, type, payload, status, result, error, created_at, session_id) VALUES (?,?,?,?,?,?,?,?)",
                (task.id, task.type, json.dumps(task.payload), task.status,
                 json.dumps(task.result), task.error, task.created_at, task.session_id)
            )
            conn.commit()
            conn.close()
        return task

    def get_next_pending(self) -> Optional[Task]:
        """Atomically claim the next pending task (mark as running)."""
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            if not row:
                conn.close()
                return None

            cols = ["id", "type", "payload", "status", "result", "error",
                    "created_at", "started_at", "finished_at", "session_id"]
            data = dict(zip(cols, row))

            # Mark as running
            started_at = time.time()
            conn.execute("UPDATE tasks SET status = 'running', started_at = ? WHERE id = ?",
                         (started_at, data["id"]))
            conn.commit()
            conn.close()

            return Task(
                id=data["id"],
                type=data["type"],
                payload=json.loads(data["payload"]),
                status="running",
                result=json.loads(data["result"]),
                error=data["error"],
                created_at=data["created_at"],
                started_at=started_at,
                finished_at=data["finished_at"],
                session_id=data["session_id"],
            )

    def complete(self, task_id: str, result: Dict[str, Any]):
        with self._lock:
            conn = self._connect()
            conn.execute("UPDATE tasks SET status = 'completed', result = ?, finished_at = ? WHERE id = ?",
                         (json.dumps(result), time.time(), task_id))
            conn.commit()
            conn.close()

    def fail(self, task_id: str, error: str):
        with self._lock:
            conn = self._connect()
            conn.execute("UPDATE tasks SET status = 'failed', error = ?, finished_at = ? WHERE id = ?",
                         (error, time.time(), task_id))
            conn.commit()
            conn.close()

    def awaiting_approval(self, task_id: str, approval_data: Dict[str, Any]):
        with self._lock:
            conn = self._connect()
            conn.execute("UPDATE tasks SET status = 'awaiting_approval', result = ? WHERE id = ?",
                         (json.dumps(approval_data), task_id))
            conn.commit()
            conn.close()

    def get(self, task_id: str) -> Optional[Task]:
        conn = self._connect()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        conn.close()
        if not row:
            return None
        cols = ["id", "type", "payload", "status", "result", "error",
                "created_at", "started_at", "finished_at", "session_id"]
        data = dict(zip(cols, row))
        return Task(
            id=data["id"],
            type=data["type"],
            payload=json.loads(data["payload"]),
            status=data["status"],
            result=json.loads(data["result"]),
            error=data["error"],
            created_at=data["created_at"],
            started_at=data["started_at"],
            finished_at=data["finished_at"],
            session_id=data["session_id"],
        )

    def list_tasks(self, status: str = None, limit: int = 20) -> List[Task]:
        conn = self._connect()
        if status:
            rows = conn.execute("SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        conn.close()

        cols = ["id", "type", "payload", "status", "result", "error",
                "created_at", "started_at", "finished_at", "session_id"]
        tasks = []
        for row in rows:
            data = dict(zip(cols, row))
            tasks.append(Task(
                id=data["id"],
                type=data["type"],
                payload=json.loads(data["payload"]),
                status=data["status"],
                result=json.loads(data["result"]),
                error=data["error"],
                created_at=data["created_at"],
                started_at=data["started_at"],
                finished_at=data["finished_at"],
                session_id=data["session_id"],
            ))
        return tasks


class BackgroundWorker:
    """Background worker that processes tasks out of the HTTP cycle."""

    def __init__(self, queue: TaskQueue, handlers: Dict[str, Callable], num_workers: int = 2):
        self.queue = queue
        self.handlers = handlers  # type -> async handler function
        self.num_workers = num_workers
        self._workers: List[threading.Thread] = []
        self._stop = threading.Event()

    def start(self):
        """Start worker threads."""
        for i in range(self.num_workers):
            t = threading.Thread(target=self._worker_loop, name=f"aeryn-worker-{i}", daemon=True)
            t.start()
            self._workers.append(t)

    def stop(self):
        """Stop worker threads."""
        self._stop.set()

    def _worker_loop(self):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while not self._stop.is_set():
            task = self.queue.get_next_pending()
            if task is None:
                time.sleep(1)  # No tasks, idle
                continue

            handler = self.handlers.get(task.type)
            if handler is None:
                self.queue.fail(task.id, f"No handler for task type '{task.type}'")
                continue

            try:
                result = loop.run_until_complete(self._run_handler(handler, task))
                self.queue.complete(task.id, result)
            except Exception as e:
                self.queue.fail(task.id, str(e))

        loop.close()

    async def _run_handler(self, handler, task):
        """Run handler, supporting both sync and async."""
        import inspect
        if inspect.iscoroutinefunction(handler):
            return await handler(task.payload)
        return handler(task.payload)


# Global instances
_queue = None
_worker = None

def get_task_queue() -> TaskQueue:
    global _queue
    if _queue is None:
        _queue = TaskQueue()
    return _queue


def get_background_worker() -> BackgroundWorker:
    global _worker, _queue
    if _worker is None:
        _queue = get_task_queue()
        _worker = BackgroundWorker(_queue, {}, num_workers=2)
    return _worker