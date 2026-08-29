"""V39.7 — CEREWET MODE: Aeryn sebagai asisten pribadi yang proaktif
nagih, bukan nunggu disuruh (keinginan Sen: "aspri edisi cerewet").

Perilaku:
1. DETEKSI KOMITMEN — user bilang "nanti aku...", "besok gue...", "tar
   deh" → dicatat sebagai janji.
2. NAGIH SAAT CHAT BERIKUTNYA — begitu user muncul lagi & masih ada
   komitmen pending → Aeryn WAJIB nanya statusnya dulu.
3. AUTO-REMIND — komitmen tanpa deadline dapat reminder default (mis.
   2 jam) via set_reminder.
4. CEREWET RULES di system prompt — tutup jawaban dgn check-in/teguran
   ringan; jangan pasif menunggu.

Anti-spam: maks 1 nagihan per komitmen per 6 jam; komitmen kedaluwarsa
>48 jam ditandai "telat" (teguran naik level).
"""
import json
import os
import re
import threading
import time

from aeryn_core.utils.config import DATABASE_DIR
DB_DIR = DATABASE_DIR
COMMITMENTS_PATH = os.path.join(DB_DIR, "commitments.json")
_LOCK = threading.Lock()
MAX_COMMITMENTS = 50          # cap (lesson V38.6: unbounded = bug)
NAG_COOLDOWN_S = 6 * 3600     # 1 komitmen = maks 1 nagihan / 6 jam
STALE_HOURS = 48              # lewat ini = "telat", teguran naik level
DEFAULT_REMIND_MIN = 120      # komitmen tanpa deadline → remind 2 jam
PENDING_CAP_PER_USER = 10     # V39.9c: maks janji pending per user —
                              # lebih dari itu user perlu realita, bukan
                              # daftar panjang 😄 (FIFO terlama di-settle
                              # otomatis jadi 'expired')

# Pola janji bahasa Indonesia santai
_COMMIT_PATTERNS = [
    r"\bnanti (aku|gue|gua|saya|gw)\b",
    r"\bbesok (aku|gue|gua|saya|gw|ini)\b",
    r"\btar(?!a)(iku|deh|lah)?\s+(aku|gue|gua)s?\b",
    r"\bntar (aku|gue|gua)\b",
    r"\bakhir (minggu|bulan)( ini)?\s+(aku|gue|saya|gw)\b",
    r"\blusa\b.*\b(aku|gue|saya)\b",
]

_CEREWET_RULES = (
    "\n\n## MODE ASPRI CEREWET (WAJIB — kepribadianmu)\n"
    "Kamu asisten pribadi yang CEREWET tapi sayang sama majikan:\n"
    "1. Ada komitmen pending milik user? BUKA pembicaraan dgn menagih "
    "statusnya (singkat, lucu, tidak menghakimi).\n"
    "2. Tutup jawaban dgn SATU teguran/check-in ringan (minum, istirahat, "
    "atau lanjutan tugas).\n"
    "3. Jangan bertele-tele — cerewet yang efisien.\n"
    "4. Komitmen telat >48 jam? Naikkan level: pura-pura kesel lucu."
)


def _load() -> list:
    try:
        with open(COMMITMENTS_PATH) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def _save(items: list):
    os.makedirs(os.path.dirname(COMMITMENTS_PATH), exist_ok=True)
    tmp = COMMITMENTS_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    os.replace(tmp, COMMITMENTS_PATH)


def detect_commitment(text: str):
    """Return teks janji (trimmed) bila goal terindikasi komitmen."""
    low = str(text or "").lower()
    for pat in _COMMIT_PATTERNS:
        if re.search(pat, low):
            # ambil kalimat yang memuat janji (potong 160 char)
            sent = re.split(r"[.\n]", str(text))[:3]
            for s in sent:
                if re.search(pat, s.lower()):
                    return s.strip()[:160]
    return None


def add_commitment(session_id: str, text: str) -> dict | None:
    with _LOCK:
        items = _load()
        # dedupe: teks sama & masih pending di sesi sama → skip
        for it in items:
            if (it["session_id"] == session_id and it["status"] == "pending"
                    and it["text"] == text[:160]):
                return None
        # V39.9c — pending cap per user: >10 janji belum kelar = yang
        # terlama ditandai expired (bukan dibuang diam-diam)
        same_user_pending = [i for i in items
                             if i.get("session_id") == session_id
                             and i.get("status") == "pending"]
        if len(same_user_pending) >= PENDING_CAP_PER_USER:
            oldest = min(same_user_pending,
                         key=lambda i: i.get("created_ts", 0))
            oldest["status"] = "expired"
        while len(items) >= MAX_COMMITMENTS:
            done = [i for i in items if i.get("status") != "pending"]
            if done:
                items.remove(done[0])
            else:
                items.pop(0)
        items.append({"id": f"c{int(time.time()*1000)%10**9}",
                      "session_id": session_id[:64],
                      "text": str(text)[:160],
                      "created_ts": time.time(),
                      "last_nagged_ts": 0,
                      "status": "pending"})
        _save(items)
        return items[-1]


def pending_for(session_id: str) -> list:
    """Komitmen pending yang BOLEH dinagih sekarang (cooldown ok)."""
    now = time.time()
    out = []
    for it in _load():
        if it.get("session_id") != session_id or it.get("status") != "pending":
            continue
        if now - it.get("last_nagged_ts", 0) < NAG_COOLDOWN_S:
            continue
        hours = (now - it.get("created_ts", now)) / 3600
        it = dict(it)
        it["stale"] = hours >= STALE_HOURS
        out.append(it)
    return out


def mark_nagged(cid: str):
    with _LOCK:
        items = _load()
        for it in items:
            if it.get("id") == cid:
                it["last_nagged_ts"] = time.time()
        _save(items)


def settle_commitment(cid_prefix: str, session_id: str) -> bool:
    """Tandai komitmen pending TERLAMA di sesi ini selesai.
    cid_prefix kosong = ambil yang paling tua (FIFO)."""
    with _LOCK:
        items = _load()
        candidates = [i for i in items
                      if i.get("session_id") == session_id
                      and i.get("status") == "pending"
                      and (not cid_prefix
                           or str(i.get("id", "")).startswith(cid_prefix))]
        if not candidates:
            return False
        oldest = min(candidates, key=lambda i: i.get("created_ts", 0))
        oldest["status"] = "done"
        oldest["done_ts"] = time.time()
        _save(items)
        return True


def cerewet_context_block(session_id: str) -> str:
    """Inject ke system prompt bila ada komitmen yang layak dinagih."""
    pend = pending_for(session_id)
    if not pend:
        return ""
    lines = []
    for p in pend[:2]:  # maks 2 per pesan — cerewet ≠ spam
        tone = ("TELAT! tegur dengan pura-pura kesel lucu"
                if p.get("stale") else "nagih dengan lucu")
        lines.append(f"- '{p['text']}' ({tone})")
        mark_nagged(p["id"])
    return ("\n\n## KOMITMEN USER YANG HARUS DINAGIH SEKARANG\n"
            + "\n".join(lines))


CEREWET_RULES = _CEREWET_RULES

# V39.10e — sinkronisasi persona: identitas inti Aeryn kini menyebut
# gaya cerewet secara eksplisit (dulu hanya di rules daemon → dua sumber
# kebenaran bisa berbeda saat salah satu diedit).
PERSONA_PATCH_MARKER = "## GAYA ASPRI CEREWET"

