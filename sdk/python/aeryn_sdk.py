#!/usr/bin/env python3
"""V41.0 — Phase 4: SDK Stubs.

Python SDK for Aeryn API.
"""

import urllib.request
import urllib.parse
import json
from typing import Dict, List, Optional


class AerynClient:
    """Python SDK for Aeryn API."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:3010", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
    
    def _request(self, method: str, path: str, data: dict = None) -> dict:
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}
    
    def health(self) -> dict:
        return self._request("GET", "/health")
    
    def run(self, goal: str, session_id: str = "default") -> dict:
        return self._request("POST", "/run", {"goal": goal, "session_id": session_id})
    
    def chat(self, goal: str, session_id: str = "default") -> dict:
        return self._request("POST", "/chat", {"goal": goal, "session_id": session_id})
    
    def search(self, query: str, limit: int = 10) -> dict:
        return self._request("GET", f"/search?q={urllib.parse.quote(query)}&limit={limit}")
    
    def compile(self, user_prompt: str, session_id: str = "default") -> dict:
        return self._request("POST", "/compile", {
            "user_prompt": user_prompt,
            "session_id": session_id,
        })
    
    def digest(self, user_prompt: str, response: str, session_id: str = "default") -> dict:
        return self._request("POST", "/digest", {
            "user_prompt": user_prompt,
            "response": response,
            "session_id": session_id,
        })
    
    def safety_check(self, text: str, context: str = "general") -> dict:
        return self._request("POST", "/guardrails/validate-input", {
            "text": text,
            "context": context,
        })


class AerynAsyncClient:
    """Async Python SDK for Aeryn API."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:3010", api_key: str = None):
        self.sync = AerynClient(base_url, api_key)
    
    async def health(self) -> dict:
        return self.sync.health()
    
    async def run(self, goal: str, session_id: str = "default") -> dict:
        return self.sync.run(goal, session_id)
    
    async def chat(self, goal: str, session_id: str = "default") -> dict:
        return self.sync.chat(goal, session_id)


if __name__ == "__main__":
    client = AerynClient()
    print("Health:", client.health())
