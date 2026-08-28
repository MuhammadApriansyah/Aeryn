#!/usr/bin/env python3
"""V41.0 — Aeryn LLM Client: Hybrid Mode Support.

Aeryn can now operate in two modes:
1. Standalone: Uses its own LLM client (NOUS → Gemini → Groq)
2. Plugin: Uses Hermes LLM client via plugin integration

The mode is selected based on environment:
- AERYN_MODE=standalone → Use own LLM client
- AERYN_MODE=plugin → Use Hermes LLM client (default)
"""

import os
import json
import time
import asyncio
import urllib.request
from typing import Optional, List, Dict, Any
from datetime import datetime

# ── Configuration ────────────────────────────

AERYN_MODE = os.environ.get("AERYN_MODE", "plugin")  # standalone | plugin

# Provider configuration
PROVIDERS = {
    "nous": {
        "base_url": "https://inference-api.nousresearch.com/v1",
        "models": ["meituan/longcat-2.0:free", "poolside/laguna-s-2.1:free"],
        "api_key_env": "NOUS_API_KEY",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "models": ["gemini-3.5-flash-lite"],
        "api_key_env": "GEMINI_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "models": ["auto"],
        "api_key_env": "OPENROUTER_API_KEY",
    },
}

# Fallback chain
FALLBACK_CHAIN = ["nous", "gemini", "openrouter"]


# ── LLM Client ────────────────────────────────

class AerynLLMClient:
    """Multi-provider LLM client with auto-fallback."""
    
    def __init__(self):
        self._provider_idx = 0
        self._request_count = 0
        self._error_count = 0
        self._total_tokens = 0
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        tools: List[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Send chat completion request with auto-fallback.
        
        Returns: {"content": str, "provider": str, "model": str, "tokens": int}
        """
        for attempt, provider_name in enumerate(FALLBACK_CHAIN):
            provider = PROVIDERS[provider_name]
            api_key = os.environ.get(provider["api_key_env"], "")
            
            if not api_key:
                continue
            
            try:
                result = await self._request_provider(
                    provider, api_key, messages, model, temperature, max_tokens, tools
                )
                self._request_count += 1
                return result
            except Exception as e:
                self._error_count += 1
                if attempt < len(FALLBACK_CHAIN) - 1:
                    await asyncio.sleep(1)
                    continue
                raise
    
    async def _request_provider(
        self, provider, api_key, messages, model, temperature, max_tokens, tools
    ) -> Dict[str, Any]:
        """Request to specific provider."""
        base_url = provider["base_url"]
        use_model = model or provider["models"][0]
        
        url = f"{base_url}/chat/completions"
        body = {
            "model": use_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            body["tools"] = tools
        
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        
        # Run in thread pool to not block
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: urllib.request.urlopen(req, timeout=60)
        )
        data = json.loads(response.read().decode())
        
        choice = data["choices"][0]
        return {
            "content": choice["message"]["content"],
            "provider": provider,
            "model": use_model,
            "tokens": data.get("usage", {}).get("total_tokens", 0),
        }
    
    async def embed(self, text: str) -> List[float]:
        """Get embedding for text."""
        # Use NOUS embedding or fallback to local hash-bag
        provider = PROVIDERS["nous"]
        api_key = os.environ.get(provider["api_key_env"], "")
        
        if not api_key:
            return self._local_embed(text)
        
        try:
            url = f"{provider['base_url']}/embeddings"
            body = {"model": "text-embedding-3-small", "input": text}
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: urllib.request.urlopen(req, timeout=30)
            )
            data = json.loads(response.read().decode())
            return data["data"][0]["embedding"]
        except Exception:
            return self._local_embed(text)
    
    def _local_embed(self, text: str) -> List[float]:
        """Fallback: deterministic hash-bag embedding (256-dim)."""
        import hashlib
        import math
        
        vec = [0.0] * 256
        words = text.lower().split()
        for word in words:
            h = hashlib.md5(word.encode()).hexdigest()
            for i in range(0, 32, 2):
                idx = int(h[i:i+2], 16)
                vec[idx] += 1.0
        
        # L2 normalize
        mag = math.sqrt(sum(x*x for x in vec)) or 1.0
        return [x/mag for x in vec]
    
    def get_stats(self) -> Dict:
        return {
            "requests": self._request_count,
            "errors": self._error_count,
            "total_tokens": self._total_tokens,
            "current_provider": FALLBACK_CHAIN[self._provider_idx],
        }


# ── Session Management ────────────────────────

class Session:
    """Conversation session with memory."""
    
    def __init__(self, session_id: str, max_history: int = 50):
        self.id = session_id
        self.history: List[Dict[str, str]] = []
        self.context: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.max_history = max_history
    
    def add_message(self, role: str, content: str, metadata: dict = None):
        """Add message to session history."""
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if metadata:
            msg["metadata"] = metadata
        self.history.append(msg)
        self.last_active = datetime.now()
        
        # Trim if too long
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_context_window(self, max_tokens: int = 8000) -> List[Dict[str, str]]:
        """Get messages fitting in context window."""
        # Simple: return last N messages
        # TODO: Implement token counting + summarization
        return self.history[-20:]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "history_length": len(self.history),
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
        }


class SessionManager:
    """Manage multiple sessions."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.expanduser(
            "~/aeryn-core-agent/Personalisasi/Database/sessions.db"
        )
        self._sessions: Dict[str, Session] = {}
        self._init_db()
    
    def _init_db(self):
        import sqlite3
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def get_or_create(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id)
        return self._sessions[session_id]
    
    def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)
    
    def save(self, session: Session):
        """Persist session to SQLite."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO sessions (id, data, updated_at)
            VALUES (?, ?, ?)
        """, (session.id, json.dumps(session.history), datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def load(self, session_id: str) -> Optional[Session]:
        """Load session from SQLite."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT data FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        conn.close()
        
        if row:
            session = Session(session_id)
            session.history = json.loads(row[0])
            self._sessions[session_id] = session
            return session
        return None


# ── Conversation Memory ───────────────────────

class ConversationMemory:
    """Store and retrieve conversation history."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.expanduser(
            "~/aeryn-core-agent/Personalisasi/Database/conversations.db"
        )
        self._init_db()
    
    def _init_db(self):
        import sqlite3
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id, created_at DESC);
        """)
        conn.commit()
        conn.close()
    
    def store(self, session_id: str, role: str, content: str, metadata: dict = None):
        """Store a conversation message."""
        import sqlite3
        import uuid
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO conversations (id, session_id, role, content, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4())[:12],
            session_id,
            role,
            content[:10000],  # Cap at 10K chars
            json.dumps(metadata or {}),
        ))
        conn.commit()
        conn.close()
    
    def get_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Get conversation history for session."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT role, content, metadata, created_at
            FROM conversations
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (session_id, limit)).fetchall()
        conn.close()
        
        return [
            {
                "role": r[0],
                "content": r[1],
                "metadata": json.loads(r[2]),
                "timestamp": r[3],
            }
            for r in reversed(rows)
        ]
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search conversations by content."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT session_id, role, content, created_at
            FROM conversations
            WHERE content LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (f"%{query}%", limit)).fetchall()
        conn.close()
        
        return [
            {
                "session_id": r[0],
                "role": r[1],
                "content": r[2][:200],
                "timestamp": r[3],
            }
            for r in rows
        ]


# ── Mode Router ───────────────────────────────

class ModeRouter:
    """Route between standalone and plugin mode."""
    
    def __init__(self):
        self.mode = AERYN_MODE
        self._llm_client: Optional[AerynLLMClient] = None
        self._session_manager: Optional[SessionManager] = None
        self._conversation_memory: Optional[ConversationMemory] = None
    
    @property
    def llm(self) -> AerynLLMClient:
        if self._llm_client is None:
            self._llm_client = AerynLLMClient()
        return self._llm_client
    
    @property
    def sessions(self) -> SessionManager:
        if self._session_manager is None:
            self._session_manager = SessionManager()
        return self._session_manager
    
    @property
    def memory(self) -> ConversationMemory:
        if self._conversation_memory is None:
            self._conversation_memory = ConversationMemory()
        return self._conversation_memory
    
    def is_standalone(self) -> bool:
        return self.mode == "standalone"
    
    def is_plugin(self) -> bool:
        return self.mode == "plugin"


# ── Singleton ─────────────────────────────────

_mode_router: Optional[ModeRouter] = None

def get_mode_router() -> ModeRouter:
    global _mode_router
    if _mode_router is None:
        _mode_router = ModeRouter()
    return _mode_router


# ── Quick Test ────────────────────────────────

if __name__ == "__main__":
    router = get_mode_router()
    print(f"Mode: {router.mode}")
    print(f"Standalone: {router.is_standalone()}")
    print(f"Plugin: {router.is_plugin()}")
    print(f"LLM Client: {router.llm.__class__.__name__}")
    print(f"Sessions: {router.sessions.__class__.__name__}")
    print(f"Memory: {router.memory.__class__.__name__}")
