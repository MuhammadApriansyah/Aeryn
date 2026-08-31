"""Messaging Gateway — Unified interface for Telegram, Discord, Slack."""
import os
import json
import logging
import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


class Message:
    """Unified message format across all platforms."""
    
    def __init__(self, platform: str, user_id: str, chat_id: str,
                 text: str, message_id: str = None, metadata: Dict = None):
        self.platform = platform
        self.user_id = user_id
        self.chat_id = chat_id
        self.text = text
        self.message_id = message_id or hashlib.md5(
            f"{platform}:{user_id}:{text}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "platform": self.platform,
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "text": self.text,
            "message_id": self.message_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class Response:
    """Unified response format."""
    
    def __init__(self, text: str, buttons: List = None, 
                 embed: Dict = None, file_path: str = None):
        self.text = text
        self.buttons = buttons or []
        self.embed = embed
        self.file_path = file_path
    
    def to_telegram(self) -> Dict:
        result = {"text": self.text}
        if self.buttons:
            result["reply_markup"] = {
                "inline_keyboard": [[{"text": b["text"], "callback_data": b.get("data", "")} for b in row] for row in self.buttons]
            }
        return result
    
    def to_discord(self) -> Dict:
        result = {"content": self.text}
        if self.embed:
            result["embed"] = self.embed
        if self.buttons:
            result["components"] = [{"type": 1, "components": [{"type": 2, "label": b["text"], "style": 1, "custom_id": b.get("data", "")} for b in row]} for row in self.buttons]
        return result
    
    def to_slack(self) -> Dict:
        result = {"text": self.text}
        if self.buttons:
            result["blocks"] = [{"type": "actions", "elements": [{"type": "button", "text": {"type": "plain_text", "text": b["text"]}, "action_id": b.get("data", "")} for b in row]} for row in self.buttons]
        return result


class PlatformAdapter:
    """Base class for platform-specific adapters."""
    
    def __init__(self, token: str):
        self.token = token
    
    async def send_message(self, chat_id: str, response: Response):
        raise NotImplementedError
    
    async def handle_webhook(self, data: Dict) -> Optional[Dict]:
        raise NotImplementedError
    
    def parse_message(self, data: Dict) -> Optional[Message]:
        raise NotImplementedError


class TelegramAdapter(PlatformAdapter):
    """Telegram Bot API adapter."""
    
    def __init__(self, token: str):
        super().__init__(token)
        self.api_base = f"https://api.telegram.org/bot{token}"
    
    def parse_message(self, data: Dict) -> Optional[Message]:
        """Parse Telegram update into unified Message."""
        message = data.get("message", {})
        if not message:
            return None
        
        chat = message.get("chat", {})
        text = message.get("text", "")
        if not text:
            return None
        
        return Message(
            platform="telegram",
            user_id=str(chat.get("id", "")),
            chat_id=str(chat.get("id", "")),
            text=text,
            message_id=str(message.get("message_id", "")),
            metadata={"chat_type": chat.get("type", "private")},
        )
    
    async def send_message(self, chat_id: str, response: Response):
        """Send message via Telegram Bot API."""
        import aiohttp
        
        payload = response.to_telegram()
        payload["chat_id"] = chat_id
        payload["parse_mode"] = "HTML"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_base}/sendMessage", json=payload) as resp:
                return await resp.json()
    
    async def handle_webhook(self, data: Dict) -> Optional[Dict]:
        """Handle incoming Telegram webhook."""
        message = self.parse_message(data)
        if not message:
            return None
        return message.to_dict()
    
    async def set_webhook(self, url: str):
        """Set webhook URL."""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_base}/setWebhook", json={"url": url}) as resp:
                return await resp.json()


class DiscordAdapter(PlatformAdapter):
    """Discord Bot API adapter."""
    
    def __init__(self, token: str, application_id: str = None):
        super().__init__(token)
        self.application_id = application_id
        self.api_base = "https://discord.com/api/v10"
    
    def parse_message(self, data: Dict) -> Optional[Message]:
        """Parse Discord interaction into unified Message."""
        # Handle slash commands
        if data.get("type") == 2:  # APPLICATION_COMMAND
            member = data.get("member", {})
            user = member.get("user", {})
            options = data.get("data", {}).get("options", [])
            text = " ".join([opt.get("value", "") for opt in options if opt.get("value")])
            
            return Message(
                platform="discord",
                user_id=str(user.get("id", "")),
                chat_id=str(data.get("channel_id", "")),
                text=text or f"/{data.get('data', {}).get('name', 'unknown')}",
                message_id=str(data.get("id", "")),
                metadata={"username": user.get("username", ""), "type": "command"},
            )
        
        # Handle messages
        if data.get("type") == 0 or "content" in data:
            author = data.get("author", {})
            return Message(
                platform="discord",
                user_id=str(author.get("id", "")),
                chat_id=str(data.get("channel_id", "")),
                text=data.get("content", ""),
                message_id=str(data.get("id", "")),
                metadata={"username": author.get("username", ""), "type": "message"},
            )
        
        return None
    
    async def send_message(self, chat_id: str, response: Response):
        """Send message via Discord webhook/bot API."""
        import aiohttp
        
        payload = response.to_discord()
        
        async with aiohttp.ClientSession(headers={"Authorization": f"Bot {self.token}"}) as session:
            async with session.post(f"{self.api_base}/channels/{chat_id}/messages", json=payload) as resp:
                return await resp.json()
    
    async def handle_webhook(self, data: Dict) -> Optional[Dict]:
        """Handle incoming Discord interaction."""
        message = self.parse_message(data)
        if not message:
            return None
        return message.to_dict()


class SlackAdapter(PlatformAdapter):
    """Slack Bot API adapter."""
    
    def __init__(self, token: str, signing_secret: str = None):
        super().__init__(token)
        self.signing_secret = signing_secret
        self.api_base = "https://slack.com/api"
    
    def parse_message(self, data: Dict) -> Optional[Message]:
        """Parse Slack event into unified Message."""
        event = data.get("event", {})
        text = event.get("text", "")
        if not text:
            return None
        
        return Message(
            platform="slack",
            user_id=event.get("user", ""),
            chat_id=event.get("channel", ""),
            text=text,
            message_id=event.get("ts", ""),
            metadata={"channel_type": event.get("channel_type", "channel")},
        )
    
    async def send_message(self, chat_id: str, response: Response):
        """Send message via Slack Web API."""
        import aiohttp
        
        payload = response.to_slack()
        payload["channel"] = chat_id
        
        async with aiohttp.ClientSession(headers={"Authorization": f"Bearer {self.token}"}) as session:
            async with session.post(f"{self.api_base}/chat.postMessage", json=payload) as resp:
                return await resp.json()
    
    async def handle_webhook(self, data: Dict) -> Optional[Dict]:
        """Handle incoming Slack event."""
        # Handle URL verification
        if data.get("type") == "url_verification":
            return {"challenge": data.get("challenge", "")}
        
        message = self.parse_message(data)
        if not message:
            return None
        return message.to_dict()


class MessagingGateway:
    """Unified messaging gateway for all platforms."""
    
    def __init__(self):
        self.adapters: Dict[str, PlatformAdapter] = {}
        self.command_handlers: Dict[str, Callable] = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Register default command handlers."""
        self.register_command("/start", self._cmd_start)
        self.register_command("/help", self._cmd_help)
        self.register_command("/status", self._cmd_status)
        self.register_command("/search", self._cmd_search)
    
    def register_platform(self, name: str, adapter: PlatformAdapter):
        """Register a platform adapter."""
        self.adapters[name] = adapter
        logger.info(f"Platform registered: {name}")
    
    def register_command(self, command: str, handler: Callable):
        """Register a command handler."""
        self.command_handlers[command] = handler
    
    async def process_message(self, message: Message) -> Response:
        """Process incoming message and return response."""
        # Check if it's a command
        if message.text.startswith("/"):
            parts = message.text.split(" ", 1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            handler = self.command_handlers.get(command)
            if handler:
                return await handler(message, args)
        
        # Default: route to Aeryn chat
        return await self._route_to_aeryn(message)
    
    async def _route_to_aeryn(self, message: Message) -> Response:
        """Route message to Aeryn chat endpoint."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://127.0.0.1:3010/chat",
                    json={
                        "goal": message.text,
                        "session_id": f"{message.platform}_{message.user_id}",
                    },
                ) as resp:
                    data = await resp.json()
                    return Response(text=data.get("response", "Maaf, tidak ada respons."))
        except Exception as e:
            logger.error(f"Aeryn routing error: {e}")
            return Response(text="Maaf, layanan sedang tidak tersedia.")
    
    async def send_response(self, message: Message, response: Response):
        """Send response back to platform."""
        adapter = self.adapters.get(message.platform)
        if adapter:
            await adapter.send_message(message.chat_id, response)
    
    async def handle_webhook(self, platform: str, data: Dict) -> Optional[Dict]:
        """Handle incoming webhook from any platform."""
        adapter = self.adapters.get(platform)
        if not adapter:
            return None
        
        parsed = await adapter.handle_webhook(data)
        if not parsed:
            return None
        
        # Convert dict back to Message
        if isinstance(parsed, dict) and "platform" in parsed:
            message = Message(
                platform=parsed["platform"],
                user_id=parsed["user_id"],
                chat_id=parsed["chat_id"],
                text=parsed["text"],
                message_id=parsed.get("message_id"),
                metadata=parsed.get("metadata", {}),
            )
            response = await self.process_message(message)
            await self.send_response(message, response)
        
        return parsed
    
    # ── Default Commands ──
    
    async def _cmd_start(self, message: Message, args: str) -> Response:
        return Response(
            text="🤖 <b>Aeryn AI Assistant</b>\n\n"
                 "Halo! Saya Aeryn, AI assistant Anda.\n"
                 "Ketik apa saja dan saya akan membantu Anda.\n\n"
                 "Perintah yang tersedia:\n"
                 "/help - Bantuan\n"
                 "/status - Status sistem\n"
                 "/search [query] - Cari di vault",
            buttons=[[{"text": "📊 Status", "data": "/status"}, {"text": "❓ Help", "data": "/help"}]]
        )
    
    async def _cmd_help(self, message: Message, args: str) -> Response:
        return Response(
            text="📖 <b>Bantuan Aeryn</b>\n\n"
                 "Anda bisa:\n"
                 "• Chat langsung (bahasa alami)\n"
                 "/status - Cek status sistem\n"
                 "/search [query] - Cari di vault\n\n"
                 "Fitur:\n"
                 "✅ Multi-divisi (creative, reasoning, psych, gov, infra)\n"
                 "✅ Plugin system\n"
                 "✅ Memory & vault\n"
                 "✅ Observability traces"
        )
    
    async def _cmd_status(self, message: Message, args: str) -> Response:
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://127.0.0.1:3010/health") as resp:
                    health = await resp.json()
                    return Response(
                        text=f"📊 <b>Status Aeryn</b>\n\n"
                             f"Status: {health.get('status', 'unknown')}\n"
                             f"Memory: {health.get('memory_mb', 0)} MB\n"
                             f"Version: {health.get('version', '61.0')}"
                    )
        except Exception:
            return Response(text="❌ Tidak bisa menghubungi server Aeryn.")
    
    async def _cmd_search(self, message: Message, args: str) -> Response:
        if not args:
            return Response(text="Gunakan: /search [query]")
        
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://127.0.0.1:3010/search?q={args}") as resp:
                    data = await resp.json()
                    results = data.get("results", [])
                    if results:
                        text = f"🔍 Hasil pencarian ({len(results)}):\n\n"
                        for r in results[:5]:
                            text += f"• {r.get('title', r.get('path', 'unknown'))}\n"
                        return Response(text=text)
                    return Response(text="Tidak ada hasil.")
        except Exception:
            return Response(text="❌ Gagal mencari.")


# ── Singleton ──────────────────────────────────────────────

_gateway: Optional[MessagingGateway] = None

def get_messaging_gateway() -> MessagingGateway:
    """Get or create gateway singleton."""
    global _gateway
    if _gateway is None:
        _gateway = MessagingGateway()
        
        # Auto-register platforms from environment
        tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if tg_token:
            _gateway.register_platform("telegram", TelegramAdapter(tg_token))
        
        dc_token = os.environ.get("DISCORD_BOT_TOKEN", "")
        if dc_token:
            dc_app_id = os.environ.get("DISCORD_APPLICATION_ID", "")
            _gateway.register_platform("discord", DiscordAdapter(dc_token, dc_app_id))
        
        slack_token = os.environ.get("SLACK_BOT_TOKEN", "")
        if slack_token:
            _gateway.register_platform("slack", SlackAdapter(slack_token))
    
    return _gateway
