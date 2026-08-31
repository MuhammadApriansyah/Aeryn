"""Messaging Gateway API Routes."""
from fastapi import APIRouter, Request
from typing import Optional

router = APIRouter()

_gateway = None

def _get_gateway():
    global _gateway
    if _gateway is None:
        from . import get_messaging_gateway
        _gateway = get_messaging_gateway()
    return _gateway


@router.get("/messaging/status")
async def messaging_status():
    """Get messaging gateway status."""
    try:
        gw = _get_gateway()
        return {
            "status": "ok",
            "platforms": list(gw.adapters.keys()),
            "commands": list(gw.command_handlers.keys()),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/messaging/webhook/{platform}")
async def messaging_webhook(platform: str, request: Request):
    """Handle incoming webhook from any platform."""
    try:
        gw = _get_gateway()
        data = await request.json()
        result = await gw.handle_webhook(platform, data)
        return result or {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/messaging/send/{platform}")
async def messaging_send(platform: str, body: dict):
    """Send message to a platform."""
    try:
        gw = _get_gateway()
        from . import Message, Response
        
        chat_id = body.get("chat_id")
        text = body.get("text")
        if not chat_id or not text:
            return {"error": "chat_id and text required"}
        
        # Create a dummy message for routing
        message = Message(
            platform=platform,
            user_id="api",
            chat_id=chat_id,
            text="",
        )
        response = Response(text=text)
        await gw.send_response(message, response)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
