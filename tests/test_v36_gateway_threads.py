"""V36 — Parity thread/reply Discord di gateway Aeryn.

Gap: Hermes menangani thread WA/Discord dengan session terpisah per thread;
gateway Aeryn masih flat per channel sehingga riwayat dua thread Discord
tercampur. Sejak V35 ada session_history per-session, jadi session_id yang
benar semakin penting.

Fungsi murni yang diuji (tanpa I/O discord.py, tanpa token):
  - resolve_session_id(user_id, channel_id, thread_id=None)
  - extract_thread_id(message)      # duck-typed, mock via SimpleNamespace
  - session_for_message(message)    # pemetaan level on_message

Catatan: on_message async-nya sendiri tidak dijalankan di test (butuh bot
live + daemon), tapi pemetaan session-nya kini dipusatkan di
session_for_message yang murni dan diuji penuh di sini.
"""
import os
import sys
from types import SimpleNamespace

BASE_DIR = os.path.expanduser("~/aeryn-core-agent")
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

import discord  # noqa: E402  (terpasang di venv-proot; import tanpa token aman)
from discord_gateway import (  # noqa: E402
    extract_thread_id,
    resolve_session_id,
    session_for_message,
)


# ---------------------------------------------------------------------------
# resolve_session_id — fungsi murni
# ---------------------------------------------------------------------------

def test_resolve_with_thread_id():
    assert resolve_session_id("111", "222", 333) == "dc_111_333"
    assert resolve_session_id("111", "222", "333") == "dc_111_333"


def test_resolve_without_thread_uses_channel():
    assert resolve_session_id("111", "222") == "dc_111_222"
    assert resolve_session_id("111", "222", None) == "dc_111_222"


def test_resolve_falsy_thread_falls_back_to_channel():
    # thread_id 0 / "" tidak boleh menghasilkan dc_user_
    assert resolve_session_id("111", "222", 0) == "dc_111_222"
    assert resolve_session_id("111", "222", "") == "dc_111_222"


def test_resolve_format_two_threads_distinct_sessions():
    a = resolve_session_id("42", "1000", 7001)
    b = resolve_session_id("42", "1000", 7002)
    c = resolve_session_id("42", "1000")
    assert a != b != c
    assert all(s.startswith("dc_42_") for s in (a, b, c))


# ---------------------------------------------------------------------------
# extract_thread_id — duck-typed mock, tanpa token
# ---------------------------------------------------------------------------

def _msg(thread=None, channel_type=None, channel_id=1000):
    ch = SimpleNamespace(id=channel_id, type=channel_type)
    return SimpleNamespace(thread=thread, channel=ch)


def test_extract_via_message_thread():
    m = _msg(thread=SimpleNamespace(id=555))
    assert extract_thread_id(m) == 555


def test_extract_channel_is_public_thread():
    m = _msg(channel_type=discord.ChannelType.public_thread, channel_id=555)
    assert extract_thread_id(m) == 555


def test_extract_channel_is_private_thread():
    m = _msg(channel_type=discord.ChannelType.private_thread, channel_id=777)
    assert extract_thread_id(m) == 777


def test_extract_channel_is_news_thread():
    m = _msg(channel_type=discord.ChannelType.news_thread, channel_id=888)
    assert extract_thread_id(m) == 888


def test_extract_text_channel_returns_none():
    m = _msg(channel_type=discord.ChannelType.text, channel_id=1000)
    assert extract_thread_id(m) is None


def test_extract_dm_channel_returns_none():
    m = _msg(channel_type=discord.ChannelType.private, channel_id=999)
    assert extract_thread_id(m) is None


def test_extract_no_type_attr_returns_none():
    # DM channel duck-typed tanpa .type sama sekali
    m = SimpleNamespace(thread=None, channel=SimpleNamespace(id=999))
    assert extract_thread_id(m) is None


# ---------------------------------------------------------------------------
# session_for_message — pemetaan level on_message
# ---------------------------------------------------------------------------

def test_mapping_thread_message():
    m = _msg(thread=SimpleNamespace(id=7001))
    m.author = SimpleNamespace(id=42)
    assert session_for_message(m) == "dc_42_7001"


def test_mapping_reply_in_channel_without_thread_keeps_channel_id():
    # reply ke pesan bot di channel biasa / DM tanpa thread -> id channel
    m = _msg(channel_type=discord.ChannelType.private, channel_id=999)
    m.author = SimpleNamespace(id=42)
    assert session_for_message(m) == "dc_42_999"


def test_mapping_guild_text_channel():
    m = _msg(channel_type=discord.ChannelType.text, channel_id="1541581954439454850")
    m.author = SimpleNamespace(id=42)
    assert session_for_message(m) == "dc_42_1541581954439454850"


def test_mapping_two_threads_same_user_never_share_session():
    t1 = _msg(thread=SimpleNamespace(id=7001)); t1.author = SimpleNamespace(id=42)
    t2 = _msg(thread=SimpleNamespace(id=7002)); t2.author = SimpleNamespace(id=42)
    base = _msg(channel_type=discord.ChannelType.text, channel_id=1000)
    base.author = SimpleNamespace(id=42)
    sessions = {session_for_message(x) for x in (t1, t2, base)}
    assert len(sessions) == 3
