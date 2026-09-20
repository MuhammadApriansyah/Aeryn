#!/usr/bin/env python3
"""V62.8 — G1: Gateway Channel — Discord bot wired ke AgentLoop + ProfileRouter.

Bot menerima pesan Discord → resolve profil via ProfileRouter → AgentLoop
(trust layer otomatis di dalamnya) → balas di channel. Token dari
~/.hermes/.env (DISCORD_BOT_TOKEN) — tidak pernah di-log.
Real APIs only — no test doubles.
"""

import os
import sys
import json
import asyncio
import re

REPO = os.environ.get(
    "AERYN_REPO",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."),
)
REPO = os.path.abspath(REPO)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")
os.environ.setdefault("MEMORY_LIBRARY", os.path.join(HOME, "hermes-memory-library"))
os.environ.setdefault(
    "MEMORY_GRAPH_DB", os.path.join(HOME, "hermes-memory-library", "memory_graph.db")
)


def load_token() -> str:
    """Load DISCORD_BOT_TOKEN dari ~/.hermes/.env (never log it)."""
    env_file = os.path.join(HOME, ".hermes", ".env")
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DISCORD_BOT_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return os.environ.get("DISCORD_BOT_TOKEN", "")


def load_allowed_users() -> list:
    """DISCORD_ALLOWED_USERS (comma-separated user ids, kosong = allow all)."""
    env_file = os.path.join(HOME, ".hermes", ".env")
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DISCORD_ALLOWED_USERS="):
                    raw = line.split("=", 1)[1].strip().strip('"').strip("'")
                    return [u.strip() for u in raw.split(",") if u.strip()]
    except OSError:
        pass
    return []


async def resolve_profile(discord_user_id: str, display_name: str) -> dict:
    """Resolve/buat profil untuk Discord user (auto-onboarding)."""
    from aeryn_core.platform.profile_router import get_profile_router
    router = get_profile_router()
    # Platform chat id: discord:<user_id>
    chat_id = f"discord:{discord_user_id}"
    profile = router.resolve("discord", chat_id)
    if not profile:
        # Auto-create profil (onboarding otomatis)
        router.create_profile(
            user_id=f"dc-{discord_user_id}",
            display_name=display_name,
            platform="discord",
        )
        router.bind_route("discord", chat_id, f"dc-{discord_user_id}")
        profile = router.resolve("discord", chat_id)
    return profile or {}


async def handle_message(message: dict) -> None:
    """Handle one Discord MESSAGE_CREATE → AgentLoop → reply."""
    import aiohttp

    author = message.get("author", {})
    discord_user_id = author.get("id", "")
    display_name = author.get("display_name") or author.get("username", "friend")
    content = (message.get("content") or "").strip()
    channel_id = message.get("channel_id", "")

    if not content or not discord_user_id:
        return
    # Ignore bot sendiri (anti-loop)
    if author.get("bot"):
        return
    # Allowlist (kosong = allow all)
    allowed = load_allowed_users()
    if allowed and discord_user_id not in allowed:
        return

    # Resolve profil (auto-onboarding)
    profile = await resolve_profile(discord_user_id, display_name)
    user_id = profile.get("user_id", f"dc-{discord_user_id}")

    # AgentLoop dengan session per-user + per-channel (isolasi penuh)
    try:
        from aeryn_core.agent.loop import AgentLoop
        agent = AgentLoop()
        session_id = f"discord/{channel_id}"
        resp = await agent.run(session_id, content, user_id=user_id)
        reply = resp.get("content", "(kosong)")
    except Exception as e:
        reply = f"⚠️ Aku error: {str(e)[:150]}"

    # Reply via REST API (aiohttp)
    token = load_token()
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    async with aiohttp.ClientSession() as session:
        await session.post(
            url,
            headers={"Authorization": f"Bot {token}"},
            json={"content": reply[:2000]},
        )


class GatewayBot:
    """Discord gateway bot — minimal, wired ke AgentLoop."""

    def __init__(self, token: str):
        self.token = token
        self._running = False
        self._heartbeat_interval = 41.25
        self._last_seq = None

    async def start(self):
        import aiohttp

        self._running = True
        async with aiohttp.ClientSession() as session:
            while self._running:
                try:
                    async with session.ws_connect(
                        "wss://gateway.discord.gg/?v=10&encoding=json"
                    ) as ws:
                        # Identify
                        await ws.send_json({
                            "op": 2,
                            "d": {
                                "token": self.token,
                                "intents": 32768 | 512,  # GUILD_MESSAGES + MESSAGE_CONTENT
                                "properties": {
                                    "os": "linux",
                                    "browser": "aeryn",
                                    "device": "aeryn",
                                },
                            },
                        })
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                await self._handle(ws, data)
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                break
                except Exception as e:
                    print(f"[gateway] reconnect in 5s: {str(e)[:100]}", flush=True)
                    await asyncio.sleep(5)

    async def _handle(self, ws, data: dict) -> None:
        op = data.get("op")
        if op == 10:  # Hello
            hb = data.get("d", {}).get("heartbeat_interval", 41250)
            asyncio.create_task(self._heartbeat(ws, hb / 1000))
        elif op == 0 and data.get("t") == "MESSAGE_CREATE":
            asyncio.create_task(handle_message(data.get("d", {})))
        elif op == 7:  # Reconnect
            self._running = False

    async def _heartbeat(self, ws, interval: float) -> None:
        while self._running:
            try:
                await ws.send_json({"op": 1, "d": self._last_seq})
            except Exception:
                return
            await asyncio.sleep(interval)


def main() -> None:
    token = load_token()
    if not token:
        print("[gateway] DISCORD_BOT_TOKEN tidak ada — mati", flush=True)
        return
    print(f"[gateway] Aeryn Discord gateway starting (token [REDACTED])", flush=True)
    bot = GatewayBot(token)
    asyncio.run(bot.start())


if __name__ == "__main__":
    main()
