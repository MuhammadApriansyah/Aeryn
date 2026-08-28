#!/usr/bin/env python3
"""V40.55 — Realtime: SSE + WebSocket infrastructure for dashboard.

Provides:
- EventEmitter: broadcast events to SSE + WebSocket clients
- SSE endpoint: /dashboard/stream (server pushes stats every 5s)
- WebSocket endpoint: /ws/dashboard (two-way commands)
"""

import os, sys, json, asyncio, time, threading
from typing import Dict, Set, Optional, Any
from collections import defaultdict

class EventEmitter:
    """Broadcast events to SSE + WebSocket subscribers."""
    
    def __init__(self):
        self._sse_queues: Dict[str, asyncio.Queue] = {}
        self._ws_connections: Dict[str, Any] = {}  # websocket objects
        self._lock = threading.Lock()
        self._event_history: list = []
        self._max_history = 100
    
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
    
    async def broadcast(self, event_type: str, data: Any = None):
        """Broadcast event to all connected clients."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": time.time(),
        }
        
        # Store in history
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
