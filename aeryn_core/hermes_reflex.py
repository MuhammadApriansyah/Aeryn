"""V37 — Refleks kontinuitas lintas-otak (Hermes activity reflex).

Membaca aktivitas Hermes terakhir milik majikan dari ~/.hermes/state.db
secara READ-ONLY, lalu merangkumnya jadi digest pendek bahasa Indonesia
untuk di-inject ke prompt Aeryn. Tujuannya kontinuitas: Aeryn tahu apa
yang baru dibicarakan majikan dengan Hermes tanpa harus ditanya ulang.

Aturan keras:
- JANGAN PERNAH menulis ke state.db (buka dengan mode=ro, uri=True).
- Semua fungsi total: db hilang/korup/skema beda -> hasil aman ([] / '').
"""

from __future__ import annotations

import os
import sqlite3
import time
from typing import Any, Dict, List

# Path default store sesi Hermes; bisa dioverride lewat env (dipakai test).
DEFAULT_STATE_DB = os.environ.get(
    "AERYN_HERMES_STATE_DB",
    os.path.join(os.path.expanduser("~"), ".hermes", "state.db"),
)


def recent_hermes_activity(
    limit: int = 5,
    hours: float = 6,
    db_path: str | None = None,
) -> List[Dict[str, Any]]:
    """Ambil pesan user terakhir dari state.db Hermes.

    Returns list of {ts, session_id, head} — head adalah cuplikan awal
    isi pesan (maks ~120 char, satu baris). Read-only penuh: koneksi
    dibuka dengan mode=ro sehingga SQLite menolak write dari sisi kita.
    Db tak ada / tabel beda / korup -> [] (tidak pernah raise).
    """
    try:
        path = db_path or DEFAULT_STATE_DB
        if not path or not os.path.exists(path):
            return []
        cutoff = time.time() - max(0.0, hours) * 3600.0
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            cur = con.execute(
                "SELECT timestamp, session_id, content FROM messages "
                "WHERE role = 'user' AND active = 1 AND compacted = 0 "
                "AND timestamp >= ? "
                "ORDER BY timestamp DESC LIMIT ?",
                (cutoff, max(1, int(limit))),
            )
            rows = cur.fetchall()
        finally:
            con.close()
        out: List[Dict[str, Any]] = []
        for ts, sid, content in rows:
            # Rapikan head: buang newline & pangkas panjangnya.
            head = " ".join(str(content or "").split())[:120]
            out.append({"ts": ts, "session_id": sid, "head": head})
        return out
    except Exception:
        # Korup / skema beda / permission — refleks tidak boleh bikin crash.
        return []


def render_activity_digest(activities: List[Dict[str, Any]]) -> str:
    """Render list aktivitas jadi digest pendek bahasa Indonesia.

    Kosong -> string kosong. Output dipangkas agar tetap pendek untuk
    injeksi prompt (tiap item cukup judul/topiknya).
    """
    if not activities:
        return ""
    lines = []
    for a in activities[:5]:
        head = str(a.get("head", "")).strip()
        if not head:
            continue
        lines.append(head[:80])
    if not lines:
        return ""
    body = "; ".join(lines)
    return f"[Konteks lintas-otak] Majikan baru saja bicara dengan Hermes tentang: {body}"


def get_reflex_digest(
    limit: int = 5,
    hours: float = 6,
    db_path: str | None = None,
) -> str:
    """Kombinasi recent_hermes_activity + render_activity_digest.

    Max ~600 char, tidak pernah raise.
    """
    try:
        acts = recent_hermes_activity(limit=limit, hours=hours, db_path=db_path)
        digest = render_activity_digest(acts)
        if len(digest) > 600:
            digest = digest[:597].rstrip() + "..."
        return digest
    except Exception:
        return ""
