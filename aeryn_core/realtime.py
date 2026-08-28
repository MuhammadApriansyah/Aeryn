#!/usr/bin/env python3
"""V41.0 — Realtime: Enhanced EventEmitter for all data types."""

import os, sys, json, asyncio, time, threading
from typing import Dict, Set, Optional, Any, Callable
from collections import defaultdict

class EventEmitter:
    """Broadcast events to SSE + WebSocket clients for all data types."""
    
    def __init__(self):
        self._sse_queues: Dict[str, asyncio.Queue] = {}
        self._ws_connections: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._event_history: list = []
        self._max_history = 200
        self._handlers: Dict[str, Callable] = {}  # command handlers for WS
    
    def register_sse(self, client_id: str, queue: asyncio.Queue):
        with self._lock:
            self._sse_queues[client_id] = queue
    
    def unregister_sse(self, client_id: str):
        with self._lock:
            self._sse_queues.pop(client_id, None)
    
    def register_ws(self, client_id: str, ws):
        with self._lock:
            self._ws_connections[client_id] = ws
    
    def unregister_ws(self, client_id: str):
        with self._lock:
            self._ws_connections.pop(client_id, None)
    
    def register_handler(self, command: str, handler: Callable):
        """Register a handler for WebSocket commands."""
        self._handlers[command] = handler
    
    async def handle_command(self, client_id: str, command: str, data: Any) -> Any:
        """Handle a WebSocket command."""
        handler = self._handlers.get(command)
        if handler:
            try:
                return await handler(data)
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"Unknown command: {command}"}
    
    async def broadcast(self, event_type: str, data: Any = None):
        """Broadcast event to all connected clients."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": time.time(),
        }
        
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Push to SSE clients
        dead_clients = []
        for cid, queue in list(self._sse_queues.items()):
            try:
                await asyncio.wait_for(queue.put(event), timeout=1.0)
            except Exception:
                dead_clients.append(cid)
        
        for cid in dead_clients:
            self.unregister_sse(cid)
        
        # Push to WebSocket clients
        dead_ws = []
        for cid, ws in list(self._ws_connections.items()):
            try:
                await ws.send_json(event)
            except Exception:
                dead_ws.append(cid)
        
        for cid in dead_ws:
            self.unregister_ws(cid)
    
    async def send_to_ws(self, client_id: str, event_type: str, data: Any = None):
        """Send event to specific WebSocket client."""
        ws = self._ws_connections.get(client_id)
        if ws:
            try:
                await ws.send_json({"type": event_type, "data": data, "timestamp": time.time()})
            except Exception:
                self.unregister_ws(client_id)
    
    def get_history(self, limit: int = 50) -> list:
        return self._event_history[-limit:]
    
    def get_stats(self) -> Dict:
        return {
            "sse_clients": len(self._sse_queues),
            "ws_clients": len(self._ws_connections),
            "total_events": len(self._event_history),
        }

# Global emitter instance
_emitter = None

def get_emitter() -> EventEmitter:
    global _emitter
    if _emitter is None:
        _emitter = EventEmitter()
    return _emitter
