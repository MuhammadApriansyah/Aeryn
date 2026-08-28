#!/usr/bin/env python3
"""V41.0 — Aeryn LLM Client: Hybrid Mode Support."""

import os
import json
import time
import asyncio
import urllib.request
from typing import Optional, List, Dict, Any
from datetime import datetime

def _load_env_file():
    """Load API keys from ~/.hermes/.env if available."""
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value and key not in os.environ:
                        os.environ[key] = value

_load_env_file()

AERYN_MODE = os.environ.get("AERYN_MODE", "plugin")

PROVIDERS = {
    "gemini": {
        "base_url": os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
        "models": ["gemini-3.5-flash-lite", "gemini-2.0-flash"],
        "api_key_env": "GEMINI_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "models": ["auto"],
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "deepseek": {
        "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        "models": ["deepseek-chat"],
        "api_key_env": "DEEPSEEK_API_KEY",
    },
}

FALLBACK_CHAIN = []
for provider in ["gemini", "openrouter", "deepseek"]:
    key = os.environ.get(PROVIDERS[provider]["api_key_env"], "")
    if key and key != "***":
        FALLBACK_CHAIN.append(provider)

class AerynLLMClient:
    def __init__(self):
        self._request_count = 0
        self._error_count = 0
    
    async def chat(self, messages: List[Dict[str, str]], model: str = None, temperature: float = 0.7, max_tokens: int = 4000, tools: List[Dict] = None) -> Dict[str, Any]:
        if not FALLBACK_CHAIN:
            return {"content": "No LLM providers available.", "provider": "none", "model": "none", "tokens": 0}
        
        for attempt, provider_name in enumerate(FALLBACK_CHAIN):
            provider = PROVIDERS[provider_name]
            api_key = os.environ.get(provider["api_key_env"], "")
            if not api_key or api_key == "***":
                continue
            try:
                result = await self._request_provider(provider, api_key, messages, model, temperature, max_tokens, tools)
                self._request_count += 1
                return result
            except Exception as e:
                self._error_count += 1
                if attempt < len(FALLBACK_CHAIN) - 1:
                    await asyncio.sleep(1)
                    continue
                raise
    
    async def _request_provider(self, provider, api_key, messages, model, temperature, max_tokens, tools):
        base_url = provider["base_url"]
        use_model = model or provider["models"][0]
        url = f"{base_url}/chat/completions"
        body = {"model": use_model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        if tools:
            body["tools"] = tools
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}, method="POST")
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=60))
        data = json.loads(response.read().decode())
        choice = data["choices"][0]
        return {"content": choice["message"]["content"], "provider": provider, "model": use_model, "tokens": data.get("usage", {}).get("total_tokens", 0)}

class SessionManager:
    def __init__(self, session_id: str, max_history: int = 50):
        self.session_id = session_id
        self.max_history = max_history
        self.messages: List[Dict[str, str]] = []
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_history:
            self.messages.pop(0)
    def get_context_window(self) -> List[Dict[str, str]]:
        return self.messages.copy()

class ConversationMemory:
    def __init__(self):
        self._store: Dict[str, List[Dict]] = {}
    def store(self, session_id: str, role: str, content: str):
        if session_id not in self._store:
            self._store[session_id] = []
        self._store[session_id].append({"role": role, "content": content})

class ModeRouter:
    def __init__(self):
        self.mode = AERYN_MODE
        self.llm = AerynLLMClient()
        self.sessions = {}
        self.memory = ConversationMemory()
    def is_standalone(self) -> bool:
        return self.mode == "standalone"
    def is_plugin(self) -> bool:
        return self.mode == "plugin"
    def get_or_create_session(self, session_id: str) -> SessionManager:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionManager(session_id)
        return self.sessions[session_id]

_router = None
def get_mode_router() -> ModeRouter:
    global _router
    if _router is None:
        _router = ModeRouter()
    return _router
