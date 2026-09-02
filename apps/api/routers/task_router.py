"""Task Router — async task queue endpoints for long-running agents."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])


class TaskRequest(BaseModel):
    type: str
    payload: Dict[str, Any] = {}
    session_id: str = ""


@router.post("/submit")
async def submit_task(req: TaskRequest):
    """Submit a task to the background queue (returns immediately)."""
    from aeryn_core.runtime.task_queue import get_task_queue
    queue = get_task_queue()
    task = queue.enqueue(req.type, req.payload, req.session_id)
    return {"task_id": task.id, "status": "pending"}


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Get task status and result."""
    from aeryn_core.runtime.task_queue import get_task_queue
    queue = get_task_queue()
    task = queue.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.get("/")
async def list_tasks(status: Optional[str] = None, limit: int = 20):
    """List tasks (optionally filtered by status)."""
    from aeryn_core.runtime.task_queue import get_task_queue
    queue = get_task_queue()
    tasks = queue.list_tasks(status=status, limit=limit)
    return {"tasks": [t.to_dict() for t in tasks], "count": len(tasks)}


@router.post("/submit-chat")
async def submit_chat(req: TaskRequest):
    """Submit a chat agent task (long-running) to the background queue."""
    from aeryn_core.runtime.task_queue import get_task_queue, get_background_worker

    # Register agent chat handler if not already
    worker = get_background_worker()
    if "chat" not in worker.handlers:
        async def chat_handler(payload):
            from aeryn_core.agent.loop import AgentLoop
            agent = AgentLoop()
            session_id = payload.get("session_id", "default")
            message = payload.get("message", "")
            return await agent.run(session_id, message)
        worker.handlers["chat"] = chat_handler
        worker.start()

    queue = get_task_queue()
    task = queue.enqueue("chat", req.payload, req.session_id)
    return {"task_id": task.id, "status": "pending"}