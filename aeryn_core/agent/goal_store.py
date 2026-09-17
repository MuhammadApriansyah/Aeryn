"""V61.3 — GoalStore: lapisan NIAT Aeryn (F4.1 — self-directed goals).

Aeryn sebagai agen otonom butuh lapisan tujuan: mendaftar goals sendiri,
memecah menjadi langkah, memprioritaskan, menandai progress, dan menutup
goal saat selesai. Tabel PG `goals` (pola sama dgn facts — get_neon).
"""

import json
import uuid
from datetime import datetime, timezone

from aeryn_core.database.neon_db import get_neon


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


SCHEMA = """
CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    priority INTEGER NOT NULL DEFAULT 5,
    progress INTEGER NOT NULL DEFAULT 0,
    steps TEXT,
    source TEXT,
    deadline TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


class GoalStore:
    """Lapisan niat Aeryn — goals yang dia sendiri daftarkan & kejar."""

    def __init__(self, db=None):
        self.db = db or get_neon()
        self.db.execute(SCHEMA)

    # ── Write ────────────────────────────────────────────────

    def create(self, title: str, description: str = "", priority: int = 5,
               steps: list | None = None, source: str = "self",
               deadline: str | None = None) -> str:
        """Daftarkan goal baru (source='self' = inisiatif Aeryn sendiri)."""
        gid = uuid.uuid4().hex[:16]
        self.db.execute(
            "INSERT INTO goals (id, title, description, priority, steps, "
            "source, deadline) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (gid, title, description, priority,
             json.dumps(steps or []), source, deadline),
        )
        return gid

    def update_progress(self, gid: str, progress: int, note: str = "") -> bool:
        """Perbarui progress 0-100; auto-complete saat 100."""
        progress = max(0, min(100, int(progress)))
        status = "completed" if progress >= 100 else "active"
        self.db.execute(
            "UPDATE goals SET progress = %s, status = %s, updated_at = %s "
            "WHERE id = %s",
            (progress, status, _now(), gid),
        )
        if note:
            self.db.execute(
                "UPDATE goals SET description = description || %s WHERE id = %s",
                (f"\n[note {_now()[:10]}] {note}", gid),
            )
        return True

    def complete(self, gid: str, note: str = "") -> bool:
        return self.update_progress(gid, 100, note)

    def cancel(self, gid: str, reason: str = "") -> bool:
        self.db.execute(
            "UPDATE goals SET status = 'cancelled', updated_at = %s "
            "WHERE id = %s",
            (_now(), gid),
        )
        if reason:
            self.db.execute(
                "UPDATE goals SET description = description || %s WHERE id = %s",
                (f"\n[cancelled {_now()[:10]}] {reason}", gid),
            )
        return True

    # ── Read ─────────────────────────────────────────────────

    def list_goals(self, status: str | None = None,
                   include_cancelled: bool = False) -> list:
        """List goals; default = active saja, urut prioritas (1=tertinggi)."""
        if status:
            rows = self.db.fetchall(
                "SELECT * FROM goals WHERE status = %s "
                "ORDER BY priority ASC, updated_at DESC", (status,))
        elif not include_cancelled:
            rows = self.db.fetchall(
                "SELECT * FROM goals WHERE status != 'cancelled' "
                "ORDER BY priority ASC, updated_at DESC", ())
        else:
            rows = self.db.fetchall(
                "SELECT * FROM goals ORDER BY priority ASC, updated_at DESC", ())
        out = []
        for r in rows:
            g = dict(r) if not isinstance(r, dict) else r
            if isinstance(g.get("steps"), str):
                try:
                    g["steps"] = json.loads(g["steps"])
                except (ValueError, TypeError):
                    g["steps"] = []
            out.append(g)
        return out

    def next_goal(self) -> dict | None:
        """Goal aktif ber-prioritas tertinggi (yang akan dikejar daemon)."""
        goals = self.list_goals(status="active")
        return goals[0] if goals else None

    def stats(self) -> dict:
        rows = self.db.fetchall(
            "SELECT status, count(*) AS n FROM goals GROUP BY status", ())
        by = {r["status"] if isinstance(r, dict) else r[0]:
              (r["n"] if isinstance(r, dict) else r[1]) for r in rows}
        total = sum(by.values())
        return {
            "total": total,
            "active": by.get("active", 0),
            "completed": by.get("completed", 0),
            "cancelled": by.get("cancelled", 0),
            "completion_rate": round(by.get("completed", 0) / total, 2)
            if total else 0.0,
        }


_goal_singleton = None


def get_goal_store() -> GoalStore:
    global _goal_singleton
    if _goal_singleton is None:
        _goal_singleton = GoalStore()
    return _goal_singleton
