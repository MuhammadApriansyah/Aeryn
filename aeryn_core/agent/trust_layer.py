#!/usr/bin/env python3
"""V62.6 — T1: Trust Layer — janji = aksi (no false promises).

Promise detector: parse intent janji dari user message ("catat", "ingetin",
"ingat", "jangan lupa", "nanti", "besok") → dispatch ke penyimpanan NYATA:
- note  → fact_store.record (bitemporal facts, entity=note)
- reminder → fact_store.record + redis queue job (scheduled)
Return hasil nyata: {acted: bool, what: [...], failed: [...]} — dipakai
agent loop buat jawaban JUJUR (janji gagal → bilang gagal).
Real APIs only — no test doubles.
"""

import os
import sys
import re
import json
from datetime import datetime, timedelta

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

# Intent patterns (bahasa Indonesia + Inggris, kasual)
NOTE_PATTERNS = [
    r"\bcatat\b", r"\bcatatin\b", r"\bcatat ya\b", r"\bingat\b(?!in)", r"\bremember\b",
    r"\bjangan lupa\s+(bahwa\s+)?aku\b", r"\bnote\b", r"\bpreferensi\b",
]
# B1: fakta pribadi — statement identitas/user ("aku punya X", "laptopku Y")
PERSONAL_FACT_PATTERNS = [
    r"\baku\s+(punya|pakai|pake|suka|benci|tinggal|kerja|belajar|lagi\s+belajar)\b",
    r"\b(namaku|panggil(?:an)?ku)\b",
    r"\b(laptopku|hpku|mobilmu|mobilk|mobilmu|rumahku|motorku|kipasku|kursiku)\b",
    r"\b(my|our)\s+(name|laptop|phone|home|job|car)\s+(is|are)\b",
    r"\bi\s+(have|use|like|hate|live|work|study)\b",
]
REMINDER_PATTERNS = [
    r"\bingetin\b", r"\bingatin\b", r"\bremind(?:er)?\b", r"\bjangan lupa\b",
    r"\bdelete\b.*\bnggak jadi\b",  # negative lookahead handled below
]
TIME_PATTERNS = [
    (r"\bbesok\s+(pagi|siang|sore|malam)\b", "besok"),
    (r"\bbesok\s+(?:jam\s+|pukul\s+)?(\d{1,2})(?::(\d{2}))?", "besok_jam"),
    (r"\bbesok\b", "besok"),
    (r"\bnanti\b", "nanti"),
    (r"\b(\d+)\s*(menit|jam)\b", "relative"),
    (r"\b(?:jam|pukul)\s*(\d{1,2})(?::(\d{2}))?\b", "jam_n"),
    (r"\b(senin|selasa|rabu|kamis|jumat|jumat|sabtu|minggu)\s+depan\b", "weekday_depan"),
    (r"\b(iberapa|lusa)\b", "lusa"),
]

# GAP2_MULTI: hari → nomor weekday (monday=0)
WEEKDAY_MAP = {"senin": 0, "selasa": 1, "rabu": 2, "kamis": 3,
               "jumat": 4, "sabtu": 5, "minggu": 6}


def _detect_intent(message: str) -> dict:
    """Detect promise intent: note / reminder + time + payload."""
    msg = (message or "").lower()
    is_note = any(re.search(p, msg) for p in NOTE_PATTERNS)
    is_reminder = any(re.search(p, msg) for p in REMINDER_PATTERNS)
    # GAP2_MULTI: kumpulkan SEMUA time matches (bukan cuma yang pertama) —
    # "besok 7 lembur, lusa meeting jam 10, senin depan review" = 3 reminder.
    time_hints = []
    for pat, kind in TIME_PATTERNS:
        for m in re.finditer(pat, msg):
            hint = {"kind": kind, "match": m.group(0)}
            groups = [g for g in m.groups() if g is not None]
            if groups:
                hint["groups"] = groups
            if hint not in time_hints:
                time_hints.append(hint)
    if not time_hints:
        time_hints = []
    else:
        # B2 DEDUP v3: dedup hint yang resolve ke WAKTU SAMA.
        # "besok jam 8 backup" → besok(7:00), besok_jam(8:00), jam_n(8:00 besok)
        #   → 1 reminder jam 8 (spesifik menang), bukan 3 bell.
        # "besok 7 lembur, lusa meeting jam 10, senin depan review" →
        #   3 waktu BERBEDA → tetap 3 reminder (multi-hari utuh).
        specific_kinds = ("besok_jam", "jam_n", "relative")
        specific = [h for h in time_hints if h["kind"] in specific_kinds]
        if specific:
            # hint spesifik menang; buang generik yang subset-nya tercakup
            generic = [h for h in time_hints if h["kind"] not in specific_kinds]
            generic = [h for h in generic if h["kind"] in ("weekday_depan",)]
            # dedup antar-spesifik by match (jam_n "jam 8" duplikat besok_jam
            # "besok jam 8" — resolved sama; buang jam_n yang match substring)
            kept = []
            for h in specific:
                if h["kind"] == "jam_n" and any(
                        h["match"] in k["match"] for k in kept):
                    continue  # "jam 8" ⊂ "besok jam 8" — sudah tercakup
                kept.append(h)
            time_hints = kept + generic
        else:
            # semua generik: dedup by match + substring
            # ("besok pagi" ⊃ "besok" — satu hint saja)
            kept_g = []
            for h in time_hints:
                if any(h["match"] in k["match"] or k["match"] in h["match"]
                       for k in kept_g):
                    continue
                kept_g.append(h)
            time_hints = kept_g
    is_personal = any(re.search(p, msg) for p in PERSONAL_FACT_PATTERNS)
    return {
        "is_note": is_note,
        "is_reminder": is_reminder,
        "is_personal_fact": is_personal,
        "time": time_hints[0] if time_hints else None,
        "times": time_hints,  # GAP2_MULTI: semua hints
    }


def _extract_payload(message: str) -> str:
    """Extract the thing being promised (payload setelah kata janji)."""
    msg = message.strip()
    # "tolong catat ya, aku suka X" → "aku suka X"
    m = re.search(r"(?:catat(?:in)?|inget(?:in)?|ingat|remember)[^,;.:\n]*[,;.:\n]\s*(.+)", msg, re.IGNORECASE)
    if m:
        return m.group(1).strip()[:300]
    # "catat X" → "X"
    m = re.search(r"(?:catat(?:in)?|inget(?:in)?|remember)\s+(.+)", msg, re.IGNORECASE)
    if m:
        return m.group(1).strip()[:300]
    return msg[:300]


def _compute_remind_at(time_hint: dict) -> str:
    """Compute reminder datetime from time hint."""
    now = datetime.now()
    if not time_hint:
        return (now + timedelta(hours=1)).isoformat()
    kind = time_hint["kind"]
    if kind == "besok":
        period = time_hint.get("match", "")
        hour = 7  # default pagi
        if "siang" in period:
            hour = 12
        elif "sore" in period:
            hour = 16
        elif "malam" in period:
            hour = 20
        target = (now + timedelta(days=1)).replace(hour=hour, minute=0, second=0)
        return target.isoformat()
    if kind == "relative":
        m = re.search(r"(\d+)\s*(menit|jam)", time_hint["match"])
        if m:
            n = int(m.group(1))
            delta = timedelta(minutes=n) if m.group(2) == "menit" else timedelta(hours=n)
            return (now + delta).isoformat()
    if kind == "lusa":
        return (now + timedelta(days=2)).replace(hour=7, minute=0).isoformat()
    # GAP2_MULTI: 'jam 10' / 'pukul 10:30' → hari ini (atau besok jika lewat)
    if kind == "jam_n":
        g = time_hint.get("groups", [])
        hour = int(g[0]) if g else 9
        minute = int(g[1]) if len(g) > 1 else 0
        target = now.replace(hour=hour, minute=minute, second=0)
        if target <= now:
            target += timedelta(days=1)
        return target.isoformat()
    # GAP2_MULTI: 'besok jam 7' → besok + jam spesifik
    if kind == "besok_jam":
        g = time_hint.get("groups", [])
        hour = int(g[0]) if g else 7
        target = (now + timedelta(days=1)).replace(hour=hour, minute=0, second=0)
        return target.isoformat()
    # GAP2_MULTI: 'senin depan' → weekday depan + jam 9 default
    if kind == "weekday_depan":
        g = time_hint.get("groups", [])
        wd = WEEKDAY_MAP.get((g[0] if g else "senin").lower(), 0)
        days_ahead = (wd - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return (now + timedelta(days=days_ahead)).replace(
            hour=9, minute=0, second=0).isoformat()
    return (now + timedelta(hours=1)).isoformat()


def handle_promises(user_message: str, user_id: str = "default",
                    session_id: str = "default") -> dict:
    """Detect + execute promises from a user message. Trust Layer core.

    Returns:
        {acted: bool, what: [...], failed: [...], intent: {...}}
    """
    intent = _detect_intent(user_message)
    if not (intent["is_note"] or intent["is_reminder"]
            or intent.get("is_personal_fact")):
        return {"acted": False, "what": [], "failed": [], "intent": intent}

    what, failed = [], []
    payload = _extract_payload(user_message)

    # ── LEDGER3_FINANCE: intent keuangan → tool_spending_log (NYATA) ──
    if any(k in (user_message or "").lower() for k in
           ("pengeluaran", "penghasilan", "gajian", "income ", "expense ")):
        try:
            from aeryn_core.platform.ledger_tools import tool_spending_log
            r = tool_spending_log(user_message, user_id=user_id)
            if r.get("ok"):
                what.append({"kind": "finance", "fact": r["fact"],
                             "text": r["message"][:100]})
            else:
                failed.append({"kind": "finance", "error": r.get("error", "")[:150]})
        except Exception as e:
            failed.append({"kind": "finance", "error": str(e)[:150]})

    # ── B1: PERSONAL FACT — statement pribadi user → fact store permanen ──
    if intent.get("is_personal_fact") and not intent["is_note"]:
        try:
            from aeryn_core.memory.fact_store import get_fact_store
            fs = get_fact_store()
            fid = fs.record(
                entity=user_id or "sen",
                predicate="personal_fact",
                fact=json.dumps({"text": payload, "user_id": user_id}),
                source=f"trust-layer:{user_id}",
                confidence=1.0,
            )
            # index embedding agar recall semantic menemukannya
            try:
                from aeryn_core.memory.embedding import get_embedding_index
                import hashlib as _hl
                get_embedding_index().add(
                    _hl.sha256(f"facts:{fid}".encode()).hexdigest(),
                    payload, source="facts:personal")
            except Exception:
                pass
            what.append({"kind": "personal_fact", "id": fid,
                         "text": payload[:100]})
        except Exception as e:
            failed.append({"kind": "personal_fact", "error": str(e)[:200]})

    # ── NOTE: simpan ke bitemporal facts (NYATA) ──
    if intent["is_note"]:
        try:
            from aeryn_core.memory.fact_store import get_fact_store
            fs = get_fact_store()
            fid = fs.record(
                entity="note",
                predicate="user_note",
                fact=json.dumps({"text": payload, "user_id": user_id}),
                source=f"trust-layer:{user_id}",
                confidence=1.0,
            )
            # Temuan PA-2: index ke dense embedding agar query umum (sinonim)
            # tetap menemukan fact ini (keyword ILIKE butuh match kata persis)
            try:
                from aeryn_core.memory.embedding import get_embedding_index
                import hashlib as _hl
                get_embedding_index().add(
                    _hl.sha256(f"facts:{fid}".encode()).hexdigest(),
                    payload, source="facts:user_note")
            except Exception:
                pass
            what.append({"kind": "note", "id": fid, "text": payload[:100]})
        except Exception as e:
            failed.append({"kind": "note", "error": str(e)[:200]})

    # ── REMINDER: fact + redis queue job scheduled (NYATA) ──
    if intent["is_reminder"]:
        # GAP2_MULTI: loop SEMUA time_hints — tiap hint = 1 reminder terpisah
        # (besok 7 lembur, lusa meeting jam 10, senin depan review = 3 entries).
        all_times = intent.get("times") or ([intent["time"]] if intent["time"] else [])
        seen_reminds = set()
        for t_hint in all_times:
            remind_at = _compute_remind_at(t_hint)
            if remind_at in seen_reminds:
                continue  # hint berbeda tapi waktu sama (besok + besok pagi)
            seen_reminds.add(remind_at)
            fid = None
            try:
                from aeryn_core.memory.fact_store import get_fact_store
                fs = get_fact_store()
                fid = fs.record(
                    entity="reminder",
                    predicate="user_reminder",
                    fact=json.dumps({
                        "text": payload, "user_id": user_id,
                        "remind_at": remind_at, "status": "scheduled",
                        "time_hint": t_hint.get("match", ""),
                    }),
                    source=f"trust-layer:{user_id}",
                    confidence=1.0,
                )
                what.append({"kind": "reminder", "id": fid, "remind_at": remind_at,
                             "text": payload[:100]})
            except Exception as e:
                failed.append({"kind": "reminder", "error": str(e)[:200]})
                continue
            # Schedule ke redis ZSET (G2: delayed — menembak saat waktunya tiba)
            # GAP2_MULTI: juga kirim ke home_channel user (RM2 — lintas channel)
            try:
                from aeryn_core.platform.redis_queue import schedule
                from datetime import datetime as _dt
                try:
                    epoch = _dt.fromisoformat(remind_at).timestamp()
                except Exception:
                    epoch = _dt.now().timestamp() + 3600
                jid = schedule({
                    "type": "shell",
                    "command": (
                        f'termux-notification --title "⏰ Aeryn: {payload[:40]}" '
                        f'--content "{payload[:100]}" --priority high 2>/dev/null'
                    ),
                    "meta": {"remind_at": remind_at, "user_id": user_id,
                             "fid": fid, "kind": "reminder"},
                }, epoch)
                what.append({"kind": "queue_job", "job_id": jid,
                             "remind_at": remind_at})
            except Exception as e:
                failed.append({"kind": "queue_job", "error": str(e)[:200]})

    return {"acted": bool(what), "what": what, "failed": failed, "intent": intent}


def format_for_response(result: dict) -> str:
    """Format trust result jadi kalimat jujur (dipakai agent loop)."""
    if not result.get("acted"):
        if result.get("failed"):
            return "(Catatan: percobaan nyatat/ingetin gagal — jangan bilang 'udah dicatat'.)"
        return ""
    parts = []
    ok = result.get("what", [])
    failed = result.get("failed", [])
    if any(x["kind"] == "note" for x in ok):
        parts.append("✅ Tercatat ke memori")
    if any(x["kind"] == "reminder" for x in ok):
        at = next(x["remind_at"] for x in ok if x["kind"] == "reminder")
        try:
            dt = datetime.fromisoformat(at)
            at_str = dt.strftime("%d %b %H:%M")
        except Exception:
            at_str = at[:16]
        parts.append(f"⏰ Reminder terjadwal {at_str}")
    if failed:
        parts.append(f"⚠️ {len(failed)} aksi gagal")
    return "(" + " · ".join(parts) + ")" if parts else ""
