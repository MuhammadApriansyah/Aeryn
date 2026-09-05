"""Chat Router — HTTP endpoints for agent interaction.

Supports user-scoped sessions (Fase 5.4): user_id + session_id composite.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    user_id: str = "default"
    model: Optional[str] = None
    stream: bool = False


@router.post("/chat")
async def chat(req: ChatRequest):
    """Send a message and get agent response (user-scoped)."""
    from aeryn_core.agent.loop import AgentLoop
    from aeryn_core.runtime.memory_guard import get_memory_guard

    guard = get_memory_guard()

    # Memory guard: reject with 503 under pressure (P2 anti-OOM)
    ok, reason = guard.check_memory()
    if not ok:
        raise HTTPException(status_code=503, detail=reason)

    async with guard.semaphore:
        agent = AgentLoop()
        response = await agent.run(req.session_id, req.message, user_id=req.user_id)

    return response


@router.post("/chat/async")
async def chat_async(req: ChatRequest):
    """Async chat: enqueue to task queue, return task_id immediately (P0 fix).

    Decouples the LLM call from the HTTP request cycle — the handler returns
    instantly with a task_id; the client polls /v1/tasks/{id} for the result.
    This removes the synchronous-LLM bottleneck found in Gap 1 load testing.
    """
    from aeryn_core.runtime.task_queue import get_task_queue
    from aeryn_core.runtime.chat_async import ensure_worker_started
    from aeryn_core.runtime.memory_guard import get_memory_guard

    guard = get_memory_guard()
    ok, reason = guard.check_memory()
    if not ok:
        raise HTTPException(status_code=503, detail=reason)

    ensure_worker_started()

    queue = get_task_queue()
    task = queue.enqueue(
        "chat",
        {"message": req.message, "session_id": req.session_id, "user_id": req.user_id},
        session_id=req.session_id,
    )
    return {"task_id": task.id, "status": task.status, "message": "poll /v1/tasks/{task_id}"}


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """Send a message and stream agent response."""
    from aeryn_core.agent.loop import AgentLoop
    from fastapi.responses import StreamingResponse

    agent = AgentLoop()

    async def event_generator():
        async for chunk in agent.run_stream(req.session_id, req.message, user_id=req.user_id):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/sessions")
async def list_sessions(user_id: str = "default"):
    """List sessions for a user (isolated)."""
    from aeryn_core.runtime.session_store import get_session_store
    store = get_session_store()
    sessions = store.list_user_sessions(user_id)
    return {"sessions": sessions, "user_id": user_id}


@router.get("/sessions/{session_id}/history")
async def session_history(session_id: str, user_id: str = "default"):
    """Get session history for a user."""
    from aeryn_core.runtime.session_store import get_session_store
    store = get_session_store()
    session = store.load_session(user_id, session_id)
    if not session:
        return {"session_id": session_id, "history": [], "user_id": user_id}
    return {"session_id": session_id, "history": session.messages, "user_id": user_id}


@router.get("/memory-guard/status")
async def memory_guard_status():
    """Memory guard status (P2 anti-OOM monitoring)."""
    from aeryn_core.runtime.memory_guard import get_memory_guard
    guard = get_memory_guard()
    return guard.status()


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user_id: str = "default"):
    """Delete a session for a user."""
    from aeryn_core.runtime.session_store import get_session_store
    store = get_session_store()
    store.delete_session(user_id, session_id)
    return {"status": "deleted", "session_id": session_id, "user_id": user_id}