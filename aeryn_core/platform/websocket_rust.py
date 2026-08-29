#!/usr/bin/env python3
"""
V41.0 — Rust WebSocketServer wrapper.
"""

from aeryn_engine import WebSocketServer as RustWebSocketServer

class WebSocketServer:
    """Wrapper Python untuk Rust WebSocketServer."""
    
    def __init__(self, url: str = "ws://localhost:3010/ws"):
        self._server = RustWebSocketServer(url)
    
    @property
    def url(self) -> str:
        return self._server.get_url()
    
    def start(self) -> str:
        return self._server.start()
    
    def __repr__(self) -> str:
        return f"WebSocketServer(url={self.url})"
