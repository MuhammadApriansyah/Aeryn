#!/usr/bin/env python3
"""V40.36 — Telegram Bot Integration via Bot API."""

import os, sys, json, sqlite3
from typing import Dict, List, Optional
from datetime import datetime

DB_PATH = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database/telegram_bot.db")

class TelegramBot:
    def __init__(self, token: str = None, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS telegram_users (
                user_id TEXT PRIMARY KEY, username TEXT, first_name TEXT,
                chat_id TEXT, is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS telegram_messages (
                id TEXT PRIMARY KEY, user_id TEXT, message_text TEXT,
                response_text TEXT, message_type TEXT DEFAULT 'text', created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        conn.close()
    
    def handle_update(self, update: Dict) -> Optional[Dict]:
        message = update.get("message", {})
        chat = message.get("chat", {})
        user_id = str(chat.get("id", ""))
        text = message.get("text", "")
        
        if not text:
            return None
        
        # Process via Aeryn
        response = self._process_message(user_id, text)
        
        return {
            "method": "sendMessage",
            "chat_id": chat.get("id"),
            "text": response,
        }
    
    def _process_message(self, user_id: str, text: str) -> str:
        import urllib.request
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:3010/run",
                data=json.dumps({"goal": text}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                return result.get("response", "No response")
        except Exception as e:
            return f"Error: {str(e)}"

    def get_commands(self) -> List[Dict]:
        """Get bot commands."""
        return [
            {"command": "start", "description": "Start the bot"},
            {"command": "help", "description": "Show help"},
            {"command": "ask", "description": "Ask Aeryn a question"},
        ]

_tb = None
def get_telegram_bot() -> TelegramBot:
    global _tb
    if _tb is None: _tb = TelegramBot()
    return _tb

if __name__ == "__main__":
    bot = get_telegram_bot()
    update = {"message": {"chat": {"id": 12345}, "text": "Hello Aeryn"}}
    result = bot.handle_update(update)
    print(f"Telegram: {result}")
