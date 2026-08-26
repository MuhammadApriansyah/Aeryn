"""V39.3 — Reminder internal: Aeryn bisa menyetel pengingat untuk dirinya.

Bukan cron eksternal — file-based scheduler yang diperiksa thread daemon
tiap 30 detik. Saat jatuh tempo → dikirim ke /agent/run sebagai goal
(reminder mode) dan ditandai terkirim.

Persist: Personalisasi/Database/reminders.json
Format: [{id, due_ts, note, session_id, status: pending|fired}]
"""
import json
import os
import threading
import time

from aeryn_core.social_memory import SocialMemory

DB_DIR = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database")
REMINDERS_PATH = os.path.join(DB_DIR, "reminders.json")
_LOCK = threading.Lock()
MAX_REMINDERS = 100  # V38.6 lesson: unbounded growth = bug


def _load() -> list:
    try:
        with open(REMINDERS_PATH) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def _save(items: list):
    os.makedirs(os.path.dirname(REMINDERS_PATH), exist_ok=True)
    tmp = REMINDERS_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    os.replace(tmp, REMINDERS_PATH)


def set_reminder(note: str, delay_minutes: float = 30,
                 session_id: str = "") -> dict:
    """Set pengingat `delay_minutes` dari sekarang."""
    note = str(note or "").strip()
    if not note:
        return {"ok": False, "error": "note kosong"}
    try:
        delay_minutes = float(delay_minutes)
    except (TypeError, ValueError):
        return {"ok": False, "error": "delay_minutes harus angka"}
    if not (0.1 <= delay_minutes <= 60 * 24 * 7):  # 10 menit s/d 7 hari
        return {"ok": False,
                "error": "delay di luar rentang (0.1 menit s/d 7 hari)"}
    with _LOCK:
        items = _load()
        # cap + evict fired tertua
        while len(items) >= MAX_REMINDERS:
            fired = [i for i in items if i.get("status") == "fired"]
            if fired:
                items.remove(fired[0])
            else:
                items.pop(0)
        rid = f"r{int(time.time()*1000)%10**9}"
        items.append({"id": rid, "note": note[:300],
                      "due_ts": time.time() + delay_minutes * 60,
                      "session_id": str(session_id)[:64],
                      "status": "pending"})
        _save(items)
    return {"ok": True, "id": rid, "fires_in_minutes": round(delay_minutes, 1),
            "note": note[:120]}


def due_reminders() -> list:
    """Ambil & tandai semua reminder yang jatuh tempo (atomic pop)."""
    now = time.time()
    with _LOCK:
        items = _load()
        due = [r for r in items
               if r.get("status") == "pending" and r["due_ts"] <= now]
        if due:
            for r in due:
                r["status"] = "fired"
                r["fired_at"] = now
            _save(items)
    return due


def pending_count() -> int:
    return sum(1 for r in _load() if r.get("status") == "pending")


REMINDER_SCHEMA = {
    "type": "function", "function": {"name": "set_reminder",
    "description": ("Set pengingat internal untuk dirimu sendiri. Saat "
                    "jatuh tempo, kamu akan menerima goal '[PENGINGAT] ...' "
                    "— laporkan ke user saat itu."),
    "parameters": {"type": "object", "properties": {
        "note": {"type": "string", "description": "apa yang harus "
                 "diingatkan"},
        "delay_minutes": {"type": "number", "description": "dalam berapa "
                          "menit (default 30)"}},
        "required": ["note"]}},
}
