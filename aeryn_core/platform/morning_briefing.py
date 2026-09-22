#!/usr/bin/env python3
"""GAP1: Ritual briefing pagi otomatis — cron 07:00 harian.

Modul: aeryn_core/platform/morning_briefing.py
- build_briefing(): kumpulkan jadwal (ZSET due hari ini) + goals aktif +
  catatan harian terakhir → teks briefing ramah persona.
- deliver_briefing(): kirim via reminder_delivery (Discord home_channel user /
  termux-notification fallback).
Dipanggil oleh: cron scheduler (action=ping) ATAU worker loop harian.
Real API only."""

import json
import time
from datetime import datetime, timedelta

HOME = __import__("os").path.expanduser("~")


def _due_today_summary() -> list:
    """Jadwal (ZSET) yang due hari ini + besok (briefing pagi = lookahead 24h)."""
    try:
        import aeryn_core.platform.redis_queue as rq
        r = rq.connect()
        jobs = r.zrange(rq.SCHED_KEY, 0, -1, withscores=True)
        now = datetime.now()
        horizon = now + timedelta(hours=36)
        out = []
        for payload, score in jobs:
            due = datetime.fromtimestamp(score)
            if now <= due <= horizon:
                out.append(due)
        return sorted(out)
    except Exception:
        return []


def _active_goals_summary() -> list:
    """Goals aktif (PG) — top 3 by priority."""
    try:
        from aeryn_core.agent.goal_store import get_goal_store
        gs = get_goal_store()
        goals = gs.list_goals(status="active")
        return goals[:3] if goals else []
    except Exception:
        return []


def _latest_note() -> str:
    """Catatan harian terakhir (PG facts user_note)."""
    try:
        from aeryn_core.database.neon_db import get_neon
        db = get_neon()
        rows = db.fetchall(
            "SELECT fact FROM facts WHERE predicate = 'user_note' "
            "ORDER BY valid_from DESC LIMIT 1", None)
        if rows:
            try:
                d = json.loads(rows[0]["fact"])
                return d.get("text", "")[:100]
            except Exception:
                return str(rows[0]["fact"])[:100]
        return ""
    except Exception:
        return ""


def build_briefing() -> str:
    """Bangun teks briefing pagi (persona Aeryn — hangat, kasual Indonesia)."""
    now = datetime.now()
    hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][now.weekday()]
    tgl = now.strftime("%d %b")

    lines = [f"☀️ Pagi, Sen! Briefing {hari}, {tgl} ya~", ""]

    due = _due_today_summary()
    if due:
        lines.append("📅 Jadwal 36 jam ke depan:")
        for d in due:
            lines.append(f"  • {d.strftime('%a %d %b %H:%M')}")
    else:
        lines.append("📅 Tidak ada jadwal terjadwal — radar kosong.")

    goals = _active_goals_summary()
    if goals:
        lines.append("")
        lines.append("🎯 Goal yang dikejar:")
        for g in goals:
            title = g.get("title") if isinstance(g, dict) else str(g)
            progress = g.get("progress", 0) if isinstance(g, dict) else 0
            lines.append(f"  • {title} ({progress}%)")

    note = _latest_note()
    if note:
        lines.append("")
        lines.append(f"📝 Catatan terakhir: {note}")

    lines.append("")
    lines.append("Semangat hari ini ya! ⚡")
    return "\n".join(lines)


def deliver_briefing() -> dict:
    """Kirim briefing ke home_channel user (RM2 path: Discord DM / notification)."""
    text = build_briefing()
    delivered = {"briefing": text, "sent": []}

    # 1) Discord DM — profil dari profile_router sqlite (profile_routes
    #    platform=discord) + fallback users PG table. (GAP1: profiles.db)
    try:
        from aeryn_core.platform.reminder_delivery import send_discord_dm
        import sqlite3 as _sq
        _pdb = _sq.connect(
            HOME + "/aeryn-core-agent/Personalisasi/Database/profiles.db")
        _cur = _pdb.cursor()
        _cur.execute(
            "SELECT platform_chat_id, profile_id FROM profile_routes "
            "WHERE platform = 'discord'")
        for chat_id, pid in _cur.fetchall():
            if send_discord_dm(chat_id, text):
                delivered["sent"].append(f"discord:{pid}")
        _pdb.close()
    except Exception as e:
        delivered["discord_error"] = str(e)[:200]

    # 1b) users PG table (home_channel discord:...) — jika ada
    try:
        from aeryn_core.platform.reminder_delivery import send_discord_dm
        from aeryn_core.database.neon_db import get_neon
        db = get_neon()
        rows = db.fetchall(
            "SELECT id, home_channel FROM users WHERE home_channel LIKE 'discord%'",
            None)
        for row in rows or []:
            chat_id = row.get("home_channel", "")
            uid = row.get("id", "sen")
            if chat_id.startswith("discord:"):
                target = chat_id
            else:
                target = f"discord:{uid}"
            if send_discord_dm(target, text):
                delivered["sent"].append(f"discord:{uid}")
    except Exception as e:
        delivered["discord_error"] = str(e)[:200]

    # 2) termux-notification fallback (HP Sen — selalu tampil)
    try:
        import subprocess
        subprocess.run(
            ["termux-notification",
             "--title", "☀️ Aeryn: Briefing Pagi",
             "--content", text[:200],
             "--priority", "high"],
            capture_output=True, timeout=15)
        delivered["sent"].append("termux-notification")
    except Exception as e:
        delivered["notif_error"] = str(e)[:200]

    return delivered


if __name__ == "__main__":
    result = deliver_briefing()
    print(json.dumps({"sent": result["sent"],
                      "briefing_len": len(result["briefing"])},
                     ensure_ascii=False))
