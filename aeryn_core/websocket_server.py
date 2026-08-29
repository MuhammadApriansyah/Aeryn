#!/usr/bin/env python3
"""V40.36 — WebSocket Server: Real-time updates and live collaboration."""

import os, sys, json, asyncio, sqlite3
from typing import Dict, List, Optional, Set
from datetime import datetime
from aeryn_core.config import BASE_DIR, VAULT_DIR, DATABASE_DIR

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

DB_PATH = os.path.join(DATABASE_DIR, "websocket.db")

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room: str = "default"):
        await websocket.accept()
        if room not in self._connections:
            self._connections[room] = set()
        self._connections[room].add(websocket)
    
    def disconnect(self, websocket: WebSocket, room: str = "default"):
        if room in self._connections:
            self._connections[room].discard(websocket)
            if not self._connections[room]:
                del self._connections[room]
    
    async def broadcast(self, message: dict, room: str = "default"):
        if room not in self._connections:
            return
        
        disconnected = set()
        for ws in self._connections[room]:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.add(ws)
        
        for ws in disconnected:
            self.disconnect(ws, room)

class WebSocketServer:
    """WebSocket server for real-time updates."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.manager = ConnectionManager()
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS ws_events (
                id TEXT PRIMARY KEY, room TEXT NOT NULL, event_type TEXT NOT NULL,
                payload TEXT DEFAULT '{}', created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS ws_subscriptions (
                id TEXT PRIMARY KEY, room TEXT NOT NULL, user_id TEXT,
                event_types TEXT DEFAULT '[]', created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    async def handle_connection(self, websocket: WebSocket, room: str = "default", user_id: str = "anonymous"):
        """Handle a WebSocket connection."""
        await self.manager.connect(websocket, room)
        
        # Send welcome
        await websocket.send_json({
            "type": "connected",
            "room": room,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
        })
        
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    await self._handle_message(msg, room, user_id)
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "message": "Invalid JSON"})
        except WebSocketDisconnect:
            self.manager.disconnect(websocket, room)
    
    async def _handle_message(self, msg: dict, room: str, user_id: str):
        """Handle incoming message."""
        msg_type = msg.get("type", "unknown")
        
        if msg_type == "ping":
            pass  # Handled by WebSocket framework
        elif msg_type == "subscribe":
            # Subscribe to event types
            pass
        elif msg_type == "message":
            # Broadcast message to room
            await self.manager.broadcast({
                "type": "message",
                "from": user_id,
                "content": msg.get("content", ""),
                "timestamp": datetime.now().isoformat(),
            }, room)
    
    async def notify(self, event_type: str, payload: dict, room: str = "default"):
        """Send notification to all clients in a room."""
        import uuid
        
        # Store event
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO ws_events (id, room, event_type, payload)
            VALUES (?, ?, ?, ?)
        """, (str(uuid.uuid4())[:8], room, event_type, json.dumps(payload)))
        conn.commit()
        conn.close()
        
        # Broadcast
        await self.manager.broadcast({
            "type": event_type,
            "payload": payload,
            "room": room,
            "timestamp": datetime.now().isoformat(),
        }, room)
    
    def get_app(self) -> FastAPI:
        """Get FastAPI app with WebSocket endpoint."""
        if not HAS_FASTAPI:
            raise ImportError("FastAPI not installed")
        
        app = FastAPI()
        
        @app.websocket("/ws/{room}")
        async def websocket_endpoint(websocket: WebSocket, room: str):
            await self.handle_connection(websocket, room)
        
        return app

_ws = None
def get_websocket_server() -> WebSocketServer:
    global _ws
    if _ws is None: _ws = WebSocketServer()
    return _ws
