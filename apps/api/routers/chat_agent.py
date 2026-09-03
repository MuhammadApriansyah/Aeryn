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

    agent = AgentLoop()
    response = await agent.run(req.session_id, req.message, user_id=req.user_id)

    return response


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


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user_id: str = "default"):
    """Delete a session for a user."""
    from aeryn_core.runtime.session_store import get_session_store
    store = get_session_store()
    store.delete_session(user_id, session_id)
    return {"status": "deleted", "session_id": session_id, "user_id": user_id}