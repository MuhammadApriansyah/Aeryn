"""State Sharing — plumb the 4 state stores to Postgres (multi-instance).

Gap 3 (ROADMAP v2): multi-instance scalability. Sessions, tasks, approvals,
and traces must be shared across instances so a session created on instance A
is visible on instance B.

Approach: each store keeps its existing sqlite3-compatible API but connects
via a `shared_connect(name)` helper that routes to Postgres when DATABASE_URL
is reachable, else falls back to the local SQLite file (graceful degradation).

Rationale (vs global monkey-patch): selective and explicit — only the 4
state-sharing stores route to PG, everything else stays local SQLite, so no
surprise breakage from schema/migration mismatch on unrelated tables.
"""

import os
import sqlite3
from aeryn_core.utils.config import DATABASE_DIR

# Table name per store — same as store name for simplicity (namespaced tables)
STORE_TABLES = {
    "sessions": "sessions",
    "tasks": "tasks",
    "approvals": "approvals",
    "traces": "traces",
}


def _pg_available() -> bool:
    """Lazy check whether Postgres is reachable (cached at module level)."""
    url = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/sen")
    try:
        import psycopg2
        conn = psycopg2.connect(url, connect_timeout=2)
        conn.close()
        return True
    except Exception:
        return False


# Cache the availability decision once
_PG_OK = None


def use_postgres() -> bool:
    global _PG_OK
    if _PG_OK is None:
        _PG_OK = _pg_available()
    return _PG_OK


class SharedConn:
    """A connection facade that behaves like sqlite3.Connection for the tiny
    subset of operations the 4 stores actually use: cursor/execute/commit/
    close. Routes to PG when available, else SQLite."""

    def __init__(self, store_name: str):
        self.store_name = store_name
        self._pg_url = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/sen")
        self._sqlite_path = os.path.join(DATABASE_DIR, f"{store_name}.db")
        self._is_pg = use_postgres()

        if self._is_pg:
            import psycopg2
            import psycopg2.extras
            self._conn = psycopg2.connect(self._pg_url)
            self._conn.autocommit = False
        else:
            self._conn = sqlite3.connect(self._sqlite_path, timeout=5)

    @property
    def is_pg(self):
        return self._is_pg

    def cursor(self):
        if self._is_pg:
            return _PGCursor(self._conn)
        return _SQLiteCursor(self._conn)

    def execute(self, query, params=None):
        cur = self.cursor()
        cur.execute(query, params)
        return cur

    def _translate(self, query: str) -> str:
        """Translate SQLite DDL to Postgres where needed."""
        if not self._is_pg:
            return query
        q = query
        # sqlite AUTOINCREMENT -> PG SERIAL handled at table level; skip for now
        # translate ? placeholders handled in cursor.execute
        return q

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


class _SQLiteCursor:
    def __init__(self, conn):
        self._cur = conn.cursor()

    def execute(self, query, params=None):
        if params:
            return self._cur.execute(query, params)
        return self._cur.execute(query)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def close(self):
        self._cur.close()


class _PGCursor:
    def __init__(self, conn):
        self._cur = conn.cursor()

    def execute(self, query, params=None):
        # translate ? -> %s
        pg_query = query.replace("?", "%s")
        if params:
            return self._cur.execute(pg_query, params)
        return self._cur.execute(pg_query)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def close(self):
        self._cur.close()


def shared_connect(store_name: str) -> SharedConn:
    """Open a shared connection for a state store (PG if available, else SQLite)."""
    return SharedConn(store_name)


def ensure_shared_tables():
    """Ensure the 4 shared tables exist in Postgres (idempotent DDL)."""
    if not use_postgres():
        return
    import psycopg2
    url = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/sen")
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    schemas = {
        "sessions": """
            CREATE TABLE IF NOT EXISTS sessions (
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                messages TEXT DEFAULT '[]',
                title TEXT DEFAULT '',
                created_at DOUBLE PRECISION,
                updated_at DOUBLE PRECISION,
                PRIMARY KEY (user_id, session_id)
            )""",
        "tasks": """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                type TEXT,
                payload TEXT DEFAULT '{}',
                status TEXT DEFAULT 'pending',
                result TEXT DEFAULT '{}',
                error TEXT DEFAULT '',
                created_at DOUBLE PRECISION,
                started_at DOUBLE PRECISION,
                finished_at DOUBLE PRECISION,
                session_id TEXT DEFAULT ''
            )""",
        "approvals": """
            CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY,
                tool_name TEXT,
                args TEXT DEFAULT '{}',
                risk_level TEXT,
                irreversible INTEGER DEFAULT 0,
                affected_scope TEXT DEFAULT '',
                estimated_cost TEXT DEFAULT '',
                explanation TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                created_at DOUBLE PRECISION,
                resolved_at DOUBLE PRECISION,
                decided_by TEXT DEFAULT ''
            )""",
        "traces": """
            CREATE TABLE IF NOT EXISTS spans (
                id TEXT PRIMARY KEY,
                trace_id TEXT,
                parent_id TEXT,
                name TEXT,
                start_time DOUBLE PRECISION,
                end_time DOUBLE PRECISION,
                attributes TEXT DEFAULT '{}',
                status TEXT DEFAULT 'unset'
            )""",
    }
    for table, ddl in schemas.items():
        try:
            cur.execute(ddl)
        except Exception:
            # table may exist with different shape; skip
            pass
    conn.commit()
    cur.close()
    conn.close()