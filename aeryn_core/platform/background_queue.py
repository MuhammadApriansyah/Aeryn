#!/usr/bin/env python3
"""V41.0 — Phase 1: Background Task Queue.

Async task queue with worker pool for long-running operations.
"""

import os, json, asyncio, time, uuid
from typing import Dict, Optional, Callable, Any
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    def __init__(self, name: str, func: Callable, args: tuple = (), kwargs: dict = None):
        self.id = str(uuid.uuid4())[:12]
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.progress = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
        }


class BackgroundTaskQueue:
    """Async task queue with worker pool."""
    
    def __init__(self, max_workers: int = 3):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._tasks: Dict[str, Task] = {}
        self._max_workers = max_workers
        self._workers = []
        self._running = False
    
    async def start(self):
        """Start worker pool."""
        self._running = True
        for i in range(self._max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
    
    async def stop(self):
        """Stop worker pool."""
        self._running = False
        for worker in self._workers:
            worker.cancel()
        self._workers = []
    
    async def submit(self, name: str, func: Callable, *args, **kwargs) -> str:
        """Submit a task to the queue."""
        task = Task(name, func, args, kwargs)
        self._tasks[task.id] = task
        await self._queue.put(task)
        return task.id
    
    async def _worker(self, name: str):
        """Worker that processes tasks."""
        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            try:
                if asyncio.iscoroutinefunction(task.func):
                    result = await task.func(*task.args, **task.kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, lambda: task.func(*task.args, **task.kwargs)
                    )
                task.result = str(result)[:1000] if result else None
                task.status = TaskStatus.COMPLETED
            except Exception as e:
                task.error = str(e)[:1000]
                task.status = TaskStatus.FAILED
            
            task.completed_at = datetime.now()
            self._queue.task_done()
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        task = self._tasks.get(task_id)
        return task.to_dict() if task else None
    
    def get_all_tasks(self) -> list:
        return [t.to_dict() for t in self._tasks.values()]
    
    def get_pending_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)
    
    def get_running_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)

    def _update_status(self, task_id: str, status: str, result: str = None) -> bool:
        """Update task status (used by AgentDaemon). Real method, not stub."""
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.status = TaskStatus(status.lower())
        if result is not None:
            task.result = result
        task.updated_at = time.time()
        return True


# ── Singleton ─────────────────────────────────

_queue: Optional[BackgroundTaskQueue] = None

def get_task_queue() -> BackgroundTaskQueue:
    global _queue
    if _queue is None:
        _queue = BackgroundTaskQueue()
    return _queue
