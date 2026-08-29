#!/usr/bin/env python3
"""
V41.0 — Rust SSE Broadcaster wrapper.
Drop-in replacement untuk realtime.py.
"""

import json
from typing import Dict, Any, Optional
from aeryn_engine import SSEBroadcaster as RustSSEBroadcaster

class RealtimeBroadcaster:
    """Wrapper Python untuk Rust SSE Broadcaster."""
    
    def __init__(self):
        self._broadcaster = RustSSEBroadcaster()
        self._event_handlers = {}
    
    def subscribe(self, client_id: str) -> None:
        self._broadcaster.subscribe(client_id)
    
    def unsubscribe(self, client_id: str) -> None:
        self._broadcaster.unsubscribe(client_id)
    
    def broadcast(self, event_type: str, data: Any) -> int:
        data_json = json.dumps(data) if not isinstance(data, str) else data
        return self._broadcaster.broadcast(event_type, data_json)
    
    @property
    def subscriber_count(self) -> int:
        return self._broadcaster.subscriber_count()
    
    def get_stats(self) -> Dict:
        return {
            "subscribers": self.subscriber_count,
            "type": "rust_sse"
        }
