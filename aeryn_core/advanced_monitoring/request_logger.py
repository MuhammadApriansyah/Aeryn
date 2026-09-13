"""V61.1 — Request logging & observability (fitur Hermes: log terstruktur).

Merekam tiap request API ke PostgreSQL (via neon_db) — method, path, status,
duration_ms — lalu menyediakan agregasi: total, error-rate (5xx), latency avg,
path terlambat/error terbanyak.

Memberi observability nyata (bukan tebakan): kita bisa tahu delay & titik gagal.
"""
from __future__ import annotations

import uuid
from datetime import datetime


def _now_iso():
    return datetime.utcnow().isoformat(sep=" ", timespec="milliseconds")


class RequestLogger:
    def __init__(self, db=None):
        from aeryn_core.database.neon_db import get_neon
        self.db = db or get_neon()
        self._ensure()

    def _ensure(self):
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS request_logs ("
            "id TEXT PRIMARY KEY, ts TIMESTAMP DEFAULT now(), "
            "method TEXT, path TEXT, status INTEGER, duration_ms INTEGER, "
            "client TEXT)")

    def log(self, method, path, status, duration_ms, client=""):
        try:
            self.db.execute(
                "INSERT INTO request_logs (id,method,path,status,duration_ms,client) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (uuid.uuid4().hex[:14], method, path[:200], int(status),
                 int(duration_ms), (client or "")[:80]))
        except Exception:
            pass  # logging tak boleh memblokir request utama

    # ── Agregasi ─────────────────────────────────────────────
    def stats(self, window_hours: int = 24) -> dict:
        """Ringkasan observability dalam window (default 24 jam)."""
        rows = self.db.fetchall(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE status >= 500) AS err5xx, "
            "COUNT(*) FILTER (WHERE status >= 400 AND status < 500) AS err4xx, "
            "COALESCE(AVG(duration_ms),0) AS avg_ms, "
            "COALESCE(MAX(duration_ms),0) AS max_ms "
            "FROM request_logs WHERE ts >= now() - make_interval(hours := %s)",
            (window_hours,))
        row = rows[0] if rows else {}
        total = row.get("total", 0) or 0

        slow = self.db.fetchall(
            "SELECT method, path, status, duration_ms, ts FROM request_logs "
            "WHERE ts >= now() - make_interval(hours := %s) "
            "ORDER BY duration_ms DESC LIMIT 8", (window_hours,))
        err_paths = self.db.fetchall(
            "SELECT path, method, COUNT(*) AS n FROM request_logs "
            "WHERE status >= 500 AND ts >= now() - make_interval(hours := %s) "
            "GROUP BY path, method ORDER BY n DESC LIMIT 8", (window_hours,))

        return {
            "window_hours": window_hours,
            "total": total,
            "error_rate": round((row.get("err5xx", 0) or 0) / total * 100, 2) if total else 0.0,
            "err5xx": row.get("err5xx", 0) or 0,
            "err4xx": row.get("err4xx", 0) or 0,
            "avg_ms": round(float(row.get("avg_ms", 0) or 0), 1),
            "max_ms": row.get("max_ms", 0) or 0,
            "slowest": slow,
            "top_error_paths": err_paths,
            "as_of": _now_iso(),
        }

    def recent(self, limit: int = 40) -> list:
        return self.db.fetchall(
            "SELECT ts, method, path, status, duration_ms FROM request_logs "
            "ORDER BY ts DESC LIMIT %s", (limit,))


_logger = None


def get_request_logger():
    global _logger
    if _logger is None:
        _logger = RequestLogger()
    return _logger