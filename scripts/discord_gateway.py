"""Aeryn Discord Gateway — jalan TERPISAH dari Hermes gateway.

Arsitektur:
  Discord (WebSocket) → pesan → POST http://127.0.0.1:3010/agent/run
  → jawaban Aeryn → balas di channel.

Fitur:
- Mention ("@Agy ...") ATAU DM → diproses sebagai goal agentic.
- Prefix "!" opsional: "!<goal>".
- Lock per-channel: satu run per channel sekaligus (antrean sederhana).
- Jawaban >1900 char dipecah otomatis (limit Discord 2000).
- Fail-soft: error daemon → pesan ramah, tanpa stack trace bocor.

Env (~/aeryn-core-agent/.env):
  AERYN_DISCORD_TOKEN, AERYN_DISCORD_GUILD_ID, AERYN_DISCORD_CHANNEL_ID,
  AERYN_DAEMON_URL (default http://127.0.0.1:3010)

Jalankan: ./venv-proot/bin/python scripts/discord_gateway.py
"""
import asyncio
import json
import os
import sys

import urllib.request

import discord
from discord.ext import commands

BASE_DIR = os.path.expanduser("~/aeryn-core-agent")
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))  # V38 — utk production_guard


def _env(key: str, default: str = "") -> str:
    for line in open(os.path.join(BASE_DIR, ".env")):
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip()
    return default


TOKEN = _env("AERYN_DISCORD_TOKEN")
DAEMON = _env("AERYN_DAEMON_URL", "http://127.0.0.1:3010")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# lock per channel id — antrean sederhana anti tabrakan
_channel_locks: dict = {}


def _lock(channel_id):
    import threading
    return _channel_locks.setdefault(channel_id, threading.Lock())


# ---------------------------------------------------------------------------
# V36 — Parity Hermes: session_id per thread/reply Discord.
#
# Hermes menangani thread dengan session terpisah per thread; gateway lama
# cenderung flat per channel sehingga riwayat dua thread tercampur.
# Sejak V35 ada session_history per-session, jadi session_id yang benar
# semakin penting.
#
# Fungsi murni (tanpa I/O discord.py) supaya mudah dites:
#   resolve_session_id(user_id, channel_id, thread_id=None) -> str
# ---------------------------------------------------------------------------

def resolve_session_id(user_id, channel_id, thread_id=None) -> str:
    """Session id turunan untuk pesan Discord.

    - Kalau pesan berasal dari thread -> pakai id thread.
    - Selain itu (termasuk DM / reply ke bot tanpa thread) -> pakai id channel.
    Format: f"dc_{user_id}_{thread_or_channel_id}"
    """
    owner = thread_id if thread_id else channel_id
    return f"dc_{user_id}_{owner}"


def extract_thread_id(message) -> "int | None":
    """Ambil id thread dari objek discord.Message (atau channel).

    - message.thread ada (bot melihat konteks thread) -> id thread tsb.
    - channel-nya sendiri bertipe public_thread/private_thread
      (mis. pesan webhook atau on_raw) -> id channel itu.
    - Selain itu (teks channel biasa, DM, dsb.) -> None.
    Tidak melakukan I/O dan tidak butuh token — aman dipanggil dari test
    dengan mock/duck-typed object.
    """
    thread = getattr(message, "thread", None)
    if thread is not None and getattr(thread, "id", None):
        return thread.id
    ch = getattr(message, "channel", message)
    try:
        ctype = getattr(ch, "type", None)
        if ctype in (discord.ChannelType.public_thread,
                     discord.ChannelType.private_thread,
                     discord.ChannelType.news_thread):
            return ch.id
    except Exception:
        pass
    return None


def session_for_message(message) -> str:
    """Pemetaan pesan -> session_id, dipakai on_message (murni, tanpa I/O)."""
    return resolve_session_id(
        str(getattr(message, "author").id),
        str(message.channel.id),
        extract_thread_id(message))


def call_aeryn(goal: str, session_id: str, timeout_s: int = 120) -> dict:
    """POST ke daemon /agent/run — sinkron, dipanggil via to_thread."""
    payload = json.dumps({"goal": goal, "session_id": session_id,
                          "max_iterations": 6}).encode()
    req = urllib.request.Request(
        f"{DAEMON}/agent/run", data=payload,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as r:
        return json.loads(r.read())


def chunk(text: str, size: int = 1900) -> list:
    out = []
    while len(text) > size:
        cut = text.rfind("\n", 0, size)
        if cut < size // 2:
            cut = size
        out.append(text[:cut])
        text = text[cut:].lstrip()
    if text:
        out.append(text)
    return out


@bot.event
async def on_ready():
    print(f"[aeryn-gw] login sebagai {bot.user} | guild/channel target siap", flush=True)


@bot.event
async def on_message(message: discord.Message):
    print(f"[aeryn-gw] pesan dari {message.author} (bot={message.author.bot}): {message.content[:60]!r}", flush=True)
    # abaikan PESAN DIRI SENDIRI saja. Webhook (author.bot=True) DITERIMA —
    # dipakai untuk test & integrasi via webhook user-sim.
    if message.author.id == bot.user.id:
        return
    # V32 — Option A: balas SEMUA pesan di channel target (hanya 1:1 test)
    is_dm = message.guild is None
    TARGET_CHANNELS = {"1541581954439454850"}  # #general di server Agy
    in_target = str(message.channel.id) in TARGET_CHANNELS
    if not is_dm and not in_target:
        return

    # strip mention jika ada, biar tetap rapi
    goal = message.content.replace(f"<@{bot.user.id}>", "").strip()
    if not goal:
        await message.reply("Sebutkan goal-nya — misal: `baca Cargo.toml sebutkan versinya`")
        return

    # V37.4-SEC — ALLOWLIST user: hanya majikan yang boleh memerintah Aeryn.
    # Dulu SIAPA PUN di channel bisa mengeksekusi tool (termasuk terminal).
    import os as _os
    _allowed_env = _os.getenv("AERYN_DISCORD_ALLOWED_USERS", "").strip()
    if _allowed_env:
        allowed_ids = {u.strip() for u in _allowed_env.split(",") if u.strip()}
        author_id = str(message.author.id)
        if author_id not in allowed_ids:
            print(f"[aeryn-gw] TOLAK pesan dari user tak-diizinkan "
                  f"{message.author} ({author_id})", flush=True)
            return

    # V38 — rate limit per-user (anti flood): 10 pesan/menit
    global _GW_LIMITER
    try:
        _GW_LIMITER
    except NameError:
        from aeryn_core.safety_engine import RateLimiter as _RL
        _GW_LIMITER = _RL(max_requests=10, window_seconds=60)
    if not _GW_LIMITER.allow(str(message.author.id)):
        await message.reply("Eits, pelan-pelan~ maksimal 10 pesan/menit 😅",
                            mention_author=False)
        return

    # V36 — Parity Hermes: session per thread/reply.
    # Thread -> pakai id thread; channel/DM biasa (termasuk reply tanpa
    # thread) -> tetap id channel (perilaku non-thread dipertahankan).
    session_id = session_for_message(message)
    lock = _lock(session_id)
    print(f"[aeryn-gw] session={session_id}", flush=True)

    # V32 — Path terpisah untuk social queries (tanpa agent loop)
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from social_generator import generate_social_response, _is_social_query
    if _is_social_query(goal):
        social_resp = generate_social_response(goal, str(message.author.id),
                                               message.channel)
        if social_resp:
            for part in chunk(social_resp):
                await message.reply(part[:2000], mention_author=False)
            return

    # V32 — perkenalkan author ke social memory daemon (pakai user_id sebagai key)
    try:
        user_part = session_id.split("_")[-1] if "_" in session_id else session_id
        who = urllib.request.Request(
            f"{DAEMON}/agent/remember",
            data=json.dumps({"session_id": user_part,
                             "fact": f"Discord user: {message.author.name}",
                             "nama": message.author.display_name,
                             "relation": "kenalan di Discord"}).encode(),
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(who, timeout=10)
    except Exception:
        pass

    async with message.channel.typing():
        resp = await asyncio.get_event_loop().run_in_executor(
            None, lambda: _safe_run(goal, session_id, lock))
    answer = str(resp or "(jawaban kosong)")
    for part in chunk(answer):
        await message.reply(part[:2000], mention_author=False)


def _safe_run(goal: str, sid: str, lock) -> str:
    with lock:
        try:
            out = call_aeryn(goal, sid)
            answer = out.get("answer") or ""
            if out.get("timed_out"):
                answer += "\n> ⏱️ Run terpotong wall-budget."
            # V32 — filter jawaban kosong/error: ganti dengan natural
            if not answer or answer.strip() in {"(tidak ada jawaban)", "{}", "None"}:
                answer = "Maaf, aku lagi bingung nih. Coba tanya yang lain? :)"
            # V32 — filter internal leak & regenerate natural
            import re as _re
            if answer:
                # Hapus bagian yang mengandung internal info (sambil simpan sisa naturalnya)
                _leak_patterns = [
                    r"Karena\s+(hasil\s+)?(pencarian|web|search)?\s*(kosong|tidak\s+ada\s+hasil)",
                    r"(hasil|pencarian|web|search)\s*(kosong|tidak\s+ada\s+hasil|tidak\s+ditemukan)",
                    r"(web_search|fs_read|http_get|web_fetch|terminal)\b",
                    r"(Karena|Tapi|Namun)\s+saya\s+tidak\s+(bisa|dapat)\s+(menemukan|membantu)",
                    r"tidak\s+ada\s+informasi\s+relevan",
                    r"(menggunakan|mencoba)\s+(fungsi|tool|fitur)\s+lain",
                    r"(Tidak\s+ada|Belum\s+ada)\s+hasil\s+dari",
                    r"jawaban\s+(ini|sebelumnya)\s+(salah|gagal|kosong)",
                ]
                original = answer
                # Coba hapus kalimat yang mengandung leak
                for pat in _leak_patterns:
                    if _re.search(pat, answer, _re.I):
                        # Hapus kalimat yang mengandung pattern
                        sentences = answer.split(". ")
                        filtered = [s for s in sentences if not _re.search(pat, s, _re.I)]
                        answer = ". ".join(filtered).strip()
                        # Hapus titik ganda atau trailing
                        answer = _re.sub(r"\.{2,}", ".", answer).strip(" .")
                        break
                if not answer or len(answer) < 10:
                    answer = "Maaf, aku lagi bingung. Coba tanya yang lain? :)"
            return answer
        except Exception as e:
            return "⚠️ Daemon Aeryn bermasalah. Coba lagi nanti."


if __name__ == "__main__":
    if not TOKEN:
        print("AERYN_DISCORD_TOKEN tidak ditemukan di .env", file=sys.stderr)
        sys.exit(1)
    bot.run(TOKEN, log_handler=None)
