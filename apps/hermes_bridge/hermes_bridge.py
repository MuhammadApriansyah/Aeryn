#!/usr/bin/env python3
"""V39.64 — Hermes Bridge: integrates Aeryn with Hermes gateway."""

import os
import sys
import json
import asyncio
import websockets
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.safety_engine import get_safety_engine, sanitize_output
from aeryn_core.adapters import get_active_adapter, render_adapter_context
from aeryn_core.reasoning_style import needs_research
from aeryn_core.persona_engine import load_persona
from aeryn_core.social_memory import SocialMemory
from aeryn_core.config import ensure_dirs

class HermesBridge:
    """Bridge between Hermes gateway and Aeryn core."""
    
    def __init__(self, hermes_url: str = "ws://127.0.0.1:3000"):
        self.hermes_url = hermes_url
        self.eng = get_safety_engine()
        self.sm = SocialMemory()
    
    async def handle_message(self, message: dict) -> dict:
        """Handle incoming message from Hermes."""
        text = message.get("text", "")
        user_id = message.get("user_id", "default")
        session_id = message.get("session_id", "default")
        
        # Safety check
        safety = self.eng.check_input(text)
        if not safety.safe:
            return {
                "type": "error",
                "text": f"Request blocked: {safety.reason}",
                "fallback": safety.fallback,
            }
        
        # Get social context
        facts = self.sm.get_facts(user_id)
        social_context = ""
        if facts:
            social_context = f"User facts: {', '.join(str(f) for f in facts[:5])}"
        
        # Detect research
        research = needs_research(text)
        
        # Select adapter
        adapter = get_active_adapter(text)
        adapter_name = adapter.name if adapter else None
        
        # Build response
        response_parts = []
        
        if research:
            response_parts.append("[Research needed — would query web]")
        
        if adapter:
            response_parts.append(f"[Using adapter: {adapter_name}]")
            ctx = render_adapter_context(text)
            if ctx:
                response_parts.append(ctx)
        
        if social_context:
            response_parts.append(f"[{social_context}]")
        
        response_parts.append(f"\nProcessing: {text[:200]}")
        response_parts.append("\n[Full LLM integration would generate response here]")
        
        response = "\n".join(response_parts)
        
        # Sanitize output
        clean = sanitize_output(response)
        
        return {
            "type": "response",
            "text": clean,
            "adapter": adapter_name,
            "needs_research": research,
            "session_id": session_id,
        }
    
    async def start(self):
        """Start WebSocket client to Hermes."""
        print(f"Connecting to Hermes at {self.hermes_url}")
        async with websockets.connect(self.hermes_url) as ws:
            print("Connected to Hermes gateway")
            async for message in ws:
                try:
                    data = json.loads(message)
                    response = await self.handle_message(data)
                    await ws.send(json.dumps(response))
                except json.JSONDecodeError:
                    await ws.send(json.dumps({"type": "error", "text": "Invalid JSON"}))
                except Exception as e:
                    await ws.send(json.dumps({"type": "error", "text": str(e)}))


if __name__ == "__main__":
    ensure_dirs()
    bridge = HermesBridge()
    asyncio.run(bridge.start())
