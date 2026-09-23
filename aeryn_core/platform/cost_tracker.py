"""Cost Tracking — token usage + spend per session (SUBAGENT-5).

Sumber data: spans nyata di traces.db (ATTR_TOKENS_TOTAL per LLM span).
- summary(): token total + per session + per hari (dari spans nyata)
- estimate_spend(): estimasi biaya (tokens × tarif per juta) — tarif default
  berbasis promo Sonnet-class ($2/$10 per MTok) — label ESTIMATE eksplisit.

Real API only — no test doubles: membaca spans nyata yang tertulis oleh
tracer middleware + agent loop.
"""

import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# DATABASE_DIR sama dengan tracing.py (repo root /data)
import aeryn_core.observability.tracing as _tracing_mod

# Tarif estimasi (USD per 1M tokens) — label ESTIMATE, bukan tagihan nyata.
# Sesuaikan AERYN_COST_INPUT/AERYN_COST_OUTPUT bila tarif provider berubah.
DEFAULT_INPUT_RATE = float(os.environ.get("AERYN_COST_INPUT", "2.0"))
DEFAULT_OUTPUT_RATE = float(os.environ.get("AERYN_COST_OUTPUT", "10.0"))


def _traces_db_path() -> str:
    return os.path.join(_tracing_mod.DATABASE_DIR, "traces.db")


def _sessions_from_spans(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Kumpulkan (session, tokens, model) dari spans nyata (attributes JSON)."""
    rows = conn.execute(
        "SELECT attributes FROM spans WHERE attributes LIKE '%gen_ai.usage.total_tokens%'"
    ).fetchall()
    out = []
    for r in rows:
        try:
            attrs = json.loads(r[0])
            sess = attrs.get("gen_ai.session.id") or attrs.get("session") or "unknown"
            tokens = int(attrs.get("gen_ai.usage.total_tokens", 0) or 0)
            model = attrs.get("gen_ai.model.name") or attrs.get("model") or "unknown"
            out.append({"session": sess, "tokens": tokens, "model": model})
        except Exception:
            continue
    return out


def summary() -> Dict[str, Any]:
    """Token usage per session + per hari (dari spans nyata)."""
    path = _traces_db_path()
    if not os.path.exists(path):
        return {"ok": True, "total_tokens": 0, "sessions": {}, "days": {},
                "llm_spans": 0, "note": "traces.db belum ada — belum ada LLM span"}

    conn = sqlite3.connect(path)
    try:
        recs = _sessions_from_spans(conn)
    finally:
        conn.close()

    total = 0
    by_session: Dict[str, int] = {}
    by_day: Dict[str, int] = {}
    for r in recs:
        total += r["tokens"]
        by_session[r["session"]] = by_session.get(r["session"], 0) + r["tokens"]
        by_day[datetime.now().strftime("%Y-%m-%d")] = by_day.get(
            datetime.now().strftime("%Y-%m-%d"), 0) + r["tokens"]

    return {"ok": True, "total_tokens": total, "sessions": by_session,
            "days": by_day, "llm_spans": len(recs)}


def estimate_spend() -> Dict[str, Any]:
    """Estimasi biaya (USD) dari token nyata × tarif — label ESTIMATE eksplisit."""
    s = summary()
    if not s.get("ok"):
        return s
    total = s.get("total_tokens", 0)
    # Estimasi kasar: 25% input / 75% output (chat umum) — label eksplisit
    input_tokens = total * 0.25
    output_tokens = total * 0.75
    cost = (input_tokens / 1_000_000) * DEFAULT_INPUT_RATE + \
           (output_tokens / 1_000_000) * DEFAULT_OUTPUT_RATE
    return {"ok": True, "total_tokens": total,
            "estimate_usd": round(cost, 6),
            "rates": {"input_per_mtok": DEFAULT_INPUT_RATE,
                      "output_per_mtok": DEFAULT_OUTPUT_RATE},
            "assumption": "25% input / 75% output, tarif promo Sonnet-class — ESTIMATE, bukan tagihan",
            "sessions": s.get("sessions", {})}
