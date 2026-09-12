"""V61.1 — Bitemporal Knowledge Graph fact store.

Bitemporal = dua sumbu waktu:
  - VALID TIME  (valid_from / valid_to): kapan fakta benar di dunia nyata.
  - TRANSACTION TIME (tx_from / tx_to): kapan fakta tercatat di sistem (audit).

Satu fakt bisa punya banyak versi transaksional. Versi "aktif" = tx_to IS NULL.
Pertanyaan khas yang didukung:
  - "apa yang Aeryn ketahui SEKARANG tentang entity X"   (point-in-time, kini)
  - "apa yang diketahui pada TANGGAL Y"                  (point-in-time, as-of)
  - riwayat perubahan sebuah fakta dll.                   (full history)

Backend: PostgreSQL via aeryn_core.database.neon_db (get_neon). Dijalankan
terhadap NEON_DATABASE_URL (lokal 127.0.0.1:5432/aeryn). Memakai tabel `facts`.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone


def _now() -> str:
    """Return current UTC as Postgres timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def _ts(iso: str) -> str:
    """Coerce an ISO datetime or None into a Postgres-friendly value."""
    if iso is None:
        return None
    return iso


class FactStore:
    """Bitemporal fact store on PostgreSQL."""

    def __init__(self, db=None):
        # Import lazy supaya tidak gagal saat Neon tidak tersedia.
        from aeryn_core.database.neon_db import get_neon
        self.db = db or get_neon()

    # ── Write ────────────────────────────────────────────────

    def record(self, entity, predicate, fact, source=None, confidence=1.0,
               valid_from=None, valid_to=None) -> str:
        """Insert a new fact (new transaction version).

        If a fact with the same (entity, predicate) is currently active
        (tx_to IS NULL), we close its window (set tx_to) and open a new one —
        preserving the audit trail. This is the bitemporal update pattern.
        """
        fid = uuid.uuid4().hex[:16]

        # 1) Close the currently-active version of this (entity, predicate)
        #    if it exists, so there's never two active versions.
        self.db.execute(
            "UPDATE facts SET tx_to = %s, valid_to = COALESCE(valid_to, %s) "
            "WHERE entity = %s AND predicate = %s AND tx_to IS NULL",
            (_now(), valid_from, entity, predicate),
        )

        # 2) Insert the new active version.
        self.db.execute(
            "INSERT INTO facts (id, entity, predicate, fact, source, confidence, "
            "valid_from, valid_to, tx_from, tx_to) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)",
            (fid, entity, predicate, fact, source, confidence,
             valid_from or _now(), valid_to, _now()),
        )
        return fid

    # ── Read ──────────────────────────────────────────────────

    def as_of(self, entity, predicate=None, at=None) -> list:
        """Fetch the state of facts as of a given time.

        Filters by VALID time (fact must be valid at `at`) AND picks the
        latest TRANSACTION version recorded before/at `at` for each
        (entity, predicate). This is a true point-in-time (bitemporal) query.

        at: str ISO datetime or None (None → now).

        Return list of {entity, predicate, fact, source, confidence,
        valid_from, valid_to, tx_from}.
        """
        at = at or _now()
        sql = """
            SELECT DISTINCT ON (entity, predicate)
                   entity, predicate, fact, source, confidence,
                   valid_from, valid_to, tx_from
            FROM facts
            WHERE entity = %s
              AND tx_from <= %s
              AND (tx_to IS NULL OR tx_to > %s)
              AND valid_from <= %s
              AND (valid_to IS NULL OR valid_to >= %s)
            ORDER BY entity, predicate, tx_from DESC
        """
        params = [entity, at, at, at, at]
        if predicate:
            sql = sql.replace("WHERE entity = %s",
                              "WHERE entity = %s AND predicate = %s")
            params.insert(1, predicate)
        return self.db.fetchall(sql, tuple(params))

    def current(self, entity, predicate=None) -> list:
        """Active facts (tx_to IS NULL) — apa yang diketahui sekarang."""
        return self.as_of(entity, predicate)

    def history(self, entity, predicate=None) -> list:
        """Full audit · all transaction versions for an entity (newest first)."""
        sql = ("SELECT entity, predicate, fact, source, confidence, "
               "valid_from, valid_to, tx_from, tx_to "
               "FROM facts WHERE entity = %s ORDER BY tx_from DESC")
        params = [entity]
        if predicate:
            sql = sql.replace("WHERE entity = %s",
                              "WHERE entity = %s AND predicate = %s")
            params.append(predicate)
        return self.db.fetchall(sql, tuple(params))

    def entities(self) -> list:
        """All entities that have at least one recorded fact."""
        rows = self.db.fetchall(
            "SELECT DISTINCT entity, COUNT(*) AS n FROM facts "
            "WHERE tx_to IS NULL GROUP BY entity ORDER BY n DESC")
        return [{"entity": r.get("entity"), "facts": r.get("n", 0)} for r in rows]


# ── Singleton ────────────────────────────────────────────────
_store = None


def get_fact_store() -> FactStore:
    global _store
    if _store is None:
        _store = FactStore()
    return _store