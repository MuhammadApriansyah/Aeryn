#!/usr/bin/env python3
"""V62.12 — RM2: Reminder → home_channel user (lintas channel, bukan cuma HP Sen).

Worker resolve profil via ProfileRouter (meta.user_id → home_channel) →
kirim reminder ke channel asal user: discord (REST API) / termux-notification
(fallback untuk user tanpa channel).
Real APIs only — no test doubles.
"""

import os
import sys
import json
import time

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


def _load_discord_token() -> str:
    """DISCORD_BOT_TOKEN dari ~/.hermes/.env (never log)."""
    try:
        with open(os.path.join(HOME, ".hermes", ".env")) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DISCORD_BOT_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def resolve_home_channel(user_id: str) -> dict:
    """Resolve user → {platform, chat_id} via ProfileRouter."""
    try:
        from aeryn_core.platform.profile_router import get_profile_router
        router = get_profile_router()
        profile = router.get_profile(user_id)
        if not profile:
            return {"platform": "local", "chat_id": None}
        pid = profile.get("id")
        # Cari route yang ter-bind ke profil ini
        import sqlite3
        conn = sqlite3.connect(router.db_path)
        try:
            row = conn.execute(
                "SELECT platform, platform_chat_id FROM profile_routes WHERE profile_id=? LIMIT 1",
                (pid,),
            ).fetchone()
        finally:
            conn.close()
        if row:
            return {"platform": row[0], "chat_id": row[1]}
        return {"platform": "local", "chat_id": None}
    except Exception:
        return {"platform": "local", "chat_id": None}


def send_discord_dm(chat_id: str, text: str) -> bool:
    """Kirim pesan ke Discord.

    chat_id format:
      - "discord:chan:<channel_id>" → langsung ke channel
      - "discord:<user_id>" → buat/resolve DM channel via API (auto-DM)
    """
    token = _load_discord_token()
    if not token or not chat_id.startswith("discord:"):
        return False
    target = chat_id.replace("discord:", "")

    import asyncio

    async def _send() -> bool:
        import aiohttp
        async with aiohttp.ClientSession() as s:
            h = {"Authorization": f"Bot {token}"}
            channel_id = target
            # USER id (bukan angka channel panjang yang mulai 1551...)? resolve DM
            if not target.startswith("chan:"):
                # Heuristic: channel id milik guild terlihat berbeda — resolve DM via API
                async with s.post(
                    "https://discord.com/api/v10/users/@me/channels",
                    headers=h, json={"recipient_id": target},
                ) as r:
                    if r.status == 200:
                        ch = await r.json()
                        channel_id = ch.get("id", target)
            async with s.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers=h, json={"content": text[:2000]},
            ) as r:
                return r.status in (200, 201)

    try:
        return asyncio.run(_send())
    except Exception:
        return False


def send_local_notification(text: str) -> bool:
    """Fallback: termux-notification (HP Sen)."""
    try:
        out = __import__("subprocess").run(
            ["termux-notification", "--title", "⏰ Aeryn Reminder",
             "--content", text[:200], "--priority", "high"],
            capture_output=True, text=True, timeout=10,
        )
        return out.returncode == 0
    except Exception:
        return False


def deliver_reminder(user_id: str, text: str) -> dict:
    """RM2 core: kirim reminder ke channel asal user (fallback: HP Sen)."""
    ch = resolve_home_channel(user_id)
    results = {"platform": ch["platform"], "chat_id": ch["chat_id"], "delivered": False}

    if ch["platform"] == "discord" and ch["chat_id"]:
        results["delivered"] = send_discord_dm(ch["chat_id"], f"⏰ {text}")
    elif ch["platform"] == "whatsapp" and ch["chat_id"]:
        # WA gateway (WA1) — belum aktif; fallback local
        results["note"] = "WA gateway belum aktif — fallback local"
        results["delivered"] = send_local_notification(f"{text}")
    else:
        # local / tanpa channel → termux-notification
        results["delivered"] = send_local_notification(text)

    # Catat delivery ke facts (audit)
    try:
        from aeryn_core.memory.fact_store import get_fact_store
        fs = get_fact_store()
        fs.record(
            entity="reminder",
            predicate="delivery",
            fact=json.dumps({
                "user_id": user_id, "text": text[:100],
                "platform": results["platform"], "delivered": results["delivered"],
                "at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }),
            source="reminder-worker",
        )
    except Exception:
        pass
    return results


# ── Wire ke queue_worker.handle_job ──

def handle_reminder_job(job: dict) -> None:
    """Handler untuk job type=reminder (dari trust layer scheduled queue)."""
    meta = job.get("meta", {})
    user_id = meta.get("user_id", "default")
    # Text dari command (extract payload antara quotes) atau meta
    cmd = job.get("command", "")
    text = ""
    if '"content"' in cmd:
        try:
            # command: termux-notification --title "..." --content "TEXT" ...
            import re
            m = re.search(r'--content\s+"([^"]+)"', cmd)
            if m:
                text = m.group(1)
        except Exception:
            pass
    if not text:
        text = meta.get("text", "Reminder")
    result = deliver_reminder(user_id, text)
    print(f"[worker] reminder delivered: {result}", flush=True)
