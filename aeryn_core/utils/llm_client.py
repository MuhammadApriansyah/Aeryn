#!/usr/bin/env python3
"""V41.0 — Aeryn LLM Client: Hybrid Mode + SQLite Persistence."""

import os, json, time, asyncio, sqlite3, urllib.request
from typing import Optional, List, Dict, Any
from datetime import datetime

from aeryn_core.utils.config import DATABASE_DIR

def _load_env_file():
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key, value = key.strip(), value.strip()
                    if key and value and key not in os.environ:
                        os.environ[key] = value
    # Load Aeryn-specific env
    aeryn_env = os.path.expanduser("~/.aeryn/.env")
    if os.path.exists(aeryn_env):
        with open(aeryn_env) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key, value = key.strip(), value.strip()
                    if key and value and key not in os.environ:
                        os.environ[key] = value

_load_env_file()

AERYN_MODE = os.environ.get("AERYN_MODE", "standalone")
_DB_DIR = DATABASE_DIR
os.makedirs(_DB_DIR, exist_ok=True)

_PROVIDERS = {
    "gemini": {
        "base_url": os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
        "models": ["gemini-3.5-flash-lite", "gemini-2.0-flash"],
        "api_key_env": "GEMINI_API_KEY",
    },
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "models": ["auto"], "api_key_env": "OPENROUTER_API_KEY"},
    "deepseek": {"base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"), "models": ["deepseek-chat"], "api_key_env": "DEEPSEEK_API_KEY"},
}

_FALLBACK_CHAIN = []
for _p in ["gemini", "openrouter", "deepseek"]:
    _k = os.environ.get(_PROVIDERS[_p]["api_key_env"], "")
    if _k and _k != "***":
        _FALLBACK_CHAIN.append(_p)


class _SQLiteStore:
    def __init__(self, name):
        self.db_path = os.path.join(_DB_DIR, name)
        self._init()
    def _init(self):
        c = sqlite3.connect(self.db_path)
        c.execute("PRAGMA journal_mode=WAL")
        c.commit(); c.close()
    def conn(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        return c


class ConversationStore(_SQLiteStore):
    def __init__(self): super().__init__("conversations.db")
    def _init(self):
        super()._init()
        c = self.conn()
        c.execute("""CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
            role TEXT NOT NULL, content TEXT NOT NULL, reasoning TEXT DEFAULT '',
            metadata TEXT DEFAULT '{}', created_at TEXT DEFAULT (datetime('now')))""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id)")
        c.commit(); c.close()
    def add_message(self, sid, role, content, reasoning=""):
        c = self.conn()
        c.execute("INSERT INTO conversations (session_id, role, content, reasoning) VALUES (?,?,?,?)", (sid, role, content, reasoning))
        c.commit(); c.close()
    def history(self, sid, limit=50):
        c = self.conn()
        rows = c.execute("SELECT role, content, reasoning, created_at FROM conversations WHERE session_id=? ORDER BY id ASC LIMIT ?", (sid, limit)).fetchall()
        c.close()
        return [dict(r) for r in rows]
    def sessions(self, limit=50):
        c = self.conn()
        rows = c.execute("SELECT session_id, COUNT(*) as messages, MAX(created_at) as last_active FROM conversations GROUP BY session_id ORDER BY last_active DESC LIMIT ?", (limit,)).fetchall()
        c.close()
        return [dict(r) for r in rows]


class ReasoningStore(_SQLiteStore):
    def __init__(self): super().__init__("reasoning.db")
    def _init(self):
        super()._init()
        c = self.conn()
        c.execute("""CREATE TABLE IF NOT EXISTS reasoning (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
            step INTEGER NOT NULL, description TEXT NOT NULL,
            detail TEXT DEFAULT '', timestamp TEXT DEFAULT (datetime('now')))""")
        c.commit(); c.close()
    def add_step(self, sid, step, desc, detail=""):
        c = self.conn()
        c.execute("INSERT INTO reasoning (session_id, step, description, detail) VALUES (?,?,?,?)", (sid, step, desc, detail))
        c.commit(); c.close()
    def get_steps(self, sid):
        c = self.conn()
        rows = c.execute("SELECT step, description, detail FROM reasoning WHERE session_id=? ORDER BY step", (sid,)).fetchall()
        c.close()
        return [dict(r) for r in rows]


class AerynLLMClient:
    def __init__(self):
        self._request_count = 0
        self._error_count = 0
        self._reasoning_store = ReasoningStore()

    async def chat(self, messages, session_id="default", model=None, temperature=0.7, max_tokens=4000, tools=None):
        steps = []
        n = 0

        n += 1
        from aeryn_core.safety.safety_engine import get_safety_engine
        eng = get_safety_engine()
        user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        safety = eng.check_input(user_msg)
        steps.append({"step": n, "description": "Safety check", "detail": f"Risk: {safety.risk}"})
        self._reasoning_store.add_step(session_id, n, "Safety check", f"Risk: {safety.risk}")

        if not safety.safe:
            return {"content": "Message blocked by safety filter", "reasoning": steps, "provider": "none", "model": "none", "tokens": 0}

        n += 1
        steps.append({"step": n, "description": "Build prompt", "detail": f"Messages: {len(messages)}"})
        self._reasoning_store.add_step(session_id, n, "Build prompt", f"Total: {len(messages)}")

        n += 1
        prov = _FALLBACK_CHAIN[0] if _FALLBACK_CHAIN else "none"
        steps.append({"step": n, "description": "Provider selection", "detail": prov})
        self._reasoning_store.add_step(session_id, n, "Provider selection", prov)

        n += 1
        steps.append({"step": n, "description": "Send request", "detail": f"Sending to {prov}..."})
        self._reasoning_store.add_step(session_id, n, "Send request", prov)

        if not _FALLBACK_CHAIN:
            return {"content": "No LLM providers available. Please set OPENROUTER_API_KEY, NOUS_API_KEY, or GEMINI_API_KEY in environment or ~/.aeryn/.env", "reasoning": steps, "provider": "none", "model": "none", "tokens": 0}

        for attempt, prov_name in enumerate(_FALLBACK_CHAIN):
            p = _PROVIDERS[prov_name]
            key = os.environ.get(p["api_key_env"], "")
            if not key or key == "***":
                continue
            try:
                result = await self._request(p, key, messages, model, temperature, max_tokens, tools)
                self._request_count += 1
                n += 1
                steps.append({"step": n, "description": "Response received", "detail": f"Tokens: {result['tokens']}"})
                self._reasoning_store.add_step(session_id, n, "Response received", f"Tokens: {result['tokens']}")
                result["reasoning"] = steps
                return result
            except Exception as e:
                self._error_count += 1
                n += 1
                steps.append({"step": n, "description": "Provider error", "detail": f"{prov_name}: {str(e)[:80]}"})
                self._reasoning_store.add_step(session_id, n, "Provider error", str(e)[:80])
                if attempt < len(_FALLBACK_CHAIN) - 1:
                    await asyncio.sleep(1)
                    continue
                raise

        return {"content": "All providers failed", "reasoning": steps, "provider": "none", "model": "none", "tokens": 0}

    async def _request(self, p, key, messages, model, temperature, max_tokens, tools):
        url = f"{p['base_url']}/chat/completions"
        use_model = model or p["models"][0]
        body = {"model": use_model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        if tools: body["tools"] = tools
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, method="POST")
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=60))
        data = json.loads(resp.read().decode())
        choice = data["choices"][0]
        return {"content": choice["message"]["content"], "provider": p["api_key_env"], "model": use_model,
                "tokens": data.get("usage", {}).get("total_tokens", 0)}


class SessionManager:
    def __init__(self, sid, max_hist=50):
        self.session_id = sid
        self.max_history = max_hist
        self.messages: List[Dict[str, str]] = []
        self.title = ""
        self._conv_store = ConversationStore()

    def add_message(self, role, content, reasoning=""):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_history:
            self.messages.pop(0)
        # Persist to SQLite
        self._conv_store.add_message(self.session_id, role, content, reasoning)

    def get_context_window(self):
        return self.messages.copy()


class ConversationMemory:
    def __init__(self):
        self._conv_store = ConversationStore()

    def add_message(self, sid, role, content, reasoning=""):
        self._conv_store.add_message(sid, role, content, reasoning)

    def store(self, sid, role, content, reasoning=""):
        self._conv_store.add_message(sid, role, content, reasoning)

    def get_history(self, sid, limit=50):
        return self._conv_store.history(sid, limit)

    def get_sessions(self, limit=50):
        return self._conv_store.sessions(limit)


class ModeRouter:
    def __init__(self):
        self.mode = AERYN_MODE
        self.llm = AerynLLMClient()
        self.sessions: Dict[str, SessionManager] = {}
        self.memory = ConversationMemory()

    def is_standalone(self): return self.mode == "standalone"
    def is_plugin(self): return self.mode == "plugin"
    def get_or_create_session(self, sid):
        if sid not in self.sessions:
            self.sessions[sid] = SessionManager(sid)
        return self.sessions[sid]


_router = None
def get_mode_router() -> ModeRouter:
    global _router
    if _router is None: _router = ModeRouter()
    return _router
