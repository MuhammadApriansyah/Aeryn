"""Chat Router — HTTP endpoints for agent interaction."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    model: Optional[str] = None
    stream: bool = False


@router.post("/chat")
async def chat(req: ChatRequest):
    """Send a message and get agent response."""
    from aeryn_core.agent.loop import AgentLoop
    
    agent = AgentLoop()
    response = await agent.run(req.session_id, req.message)
    
    return response


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """Send a message and stream agent response."""
    from aeryn_core.agent.loop import AgentLoop
    from fastapi.responses import StreamingResponse
    
    agent = AgentLoop()
    
    async def event_generator():
        async for chunk in agent.run_stream(req.session_id, req.message):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/sessions")
async def list_sessions():
    """List active sessions."""
    from aeryn_core.utils.llm_client import get_mode_router
    router = get_mode_router()
    sessions = router.memory.get_sessions()
    return {"sessions": sessions}


@router.get("/sessions/{session_id}/history")
async def session_history(session_id: str):
    """Get session history."""
    from aeryn_core.utils.llm_client import get_mode_router
    router = get_mode_router()
    history = router.memory.get_history(session_id)
    return {"session_id": session_id, "history": history}
