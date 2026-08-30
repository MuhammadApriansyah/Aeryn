#!/usr/bin/env python3
"""
V1.0 — SQLite-to-PostgreSQL compatibility adapter.

Drop-in replacement for sqlite3 that routes to PostgreSQL when available,
with automatic fallback to SQLite.

Usage:
    from aeryn_core.database.db_adapter import get_db
    
    # Compatible with sqlite3 patterns:
    conn = get_db('shared.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM workflow_runs WHERE status = ?", ('pending',))
    rows = cursor.fetchall()  # Returns list of tuples
    row = cursor.fetchone()   # Returns tuple
    conn.commit()
    conn.close()
"""

import os
import sqlite3
import logging
import threading
from contextlib import contextmanager

logger = logging.getLogger('aeryn')

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/sen')
DATABASE_DIR = os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database")

# Module-level state
_adapter = None
_adapter_lock = threading.Lock()


class PGCursorWrapper:
    """Wraps a psycopg2 cursor to provide sqlite3-compatible tuple-based API."""
    
    def __init__(self, pg_cursor):
        self._cursor = pg_cursor
        self._description = None
    
    def execute(self, query, params=None):
        """Execute a query, converting ? placeholders to %s."""
        pg_query = query.replace('?', '%s')
        if params:
            self._cursor.execute(pg_query, params)
        else:
            self._cursor.execute(pg_query)
        self._description = getattr(self._cursor, 'description', None)
    
    def executemany(self, query, params_list):
        pg_query = query.replace('?', '%s')
        self._cursor.executemany(pg_query, params_list)
    
    def fetchone(self):
        """Return next row as tuple (sqlite3 compatible)."""
        return self._cursor.fetchone()
    
    def fetchall(self):
        """Return all rows as list of tuples (sqlite3 compatible)."""
        return self._cursor.fetchall()
    
    def fetchmany(self, size=None):
        if size:
            return self._cursor.fetchmany(size)
        return self._cursor.fetchmany()
    
    @property
    def rowcount(self):
        return self._cursor.rowcount
    
    @property
    def lastrowid(self):
        # For PostgreSQL with SERIAL, we need a different approach
        # Return None - callers should use RETURNING clause
        return None
    
    @property
    def description(self):
        return self._description
    
    def close(self):
        self._cursor.close()
    
    def __iter__(self):
        return self._cursor.__iter__()


class PGConnectionWrapper:
    """Wraps a psycopg2 connection to provide sqlite3-compatible API."""
    
    def __init__(self, pg_connection):
        self._conn = pg_connection
        self.row_factory = None  # Compatibility attribute
    
    def cursor(self):
        return PGCursorWrapper(self._conn.cursor())
    
    def execute(self, query, params=None):
        cursor = self.cursor()
        cursor.execute(query, params)
        return cursor
    
    def executemany(self, query, params_list):
        cursor = self.cursor()
        cursor.executemany(query, params_list)
        return cursor
    
    def commit(self):
        self._conn.commit()
    
    def rollback(self):
        self._conn.rollback()
    
    def close(self):
        self._conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    @property
    def autocommit(self):
        return self._conn.autocommit


class DBSessionAdapter:
    """
    Database adapter that routes to PostgreSQL when available,
    falls back to SQLite.
    """
    
    def __init__(self, pg_url=None, sqlite_dir=None):
        self.pg_url = pg_url or DATABASE_URL
        self.sqlite_dir = sqlite_dir or DATABASE_DIR
        self._pg_available = None
    
    def is_pg_available(self):
        """Check if PostgreSQL is reachable."""
        if self._pg_available is not None:
            return self._pg_available
        if not self.pg_url:
            self._pg_available = False
            return False
        try:
            import psycopg2
            conn = psycopg2.connect(self.pg_url)
            conn.close()
            self._pg_available = True
            logger.info("PostgreSQL available")
            return True
        except Exception as e:
            logger.debug(f"PostgreSQL unavailable, using SQLite: {e}")
            self._pg_available = False
            return False
    
    def connect(self, db_name_or_path=None, **kwargs):
        """Get a database connection."""
        if self.is_pg_available():
            return self._connect_pg()
        return self._connect_sqlite(db_name_or_path, **kwargs)
    
    def _connect_pg(self):
        import psycopg2
        conn = psycopg2.connect(self.pg_url)
        conn.autocommit = False
        return PGConnectionWrapper(conn)
    
    def _connect_sqlite(self, db_name_or_path, **kwargs):
        if db_name_or_path is None:
            db_name_or_path = os.path.join(self.sqlite_dir, 'shared.db')
        elif not os.path.isabs(db_name_or_path):
            db_name_or_path = os.path.join(self.sqlite_dir, db_name_or_path)
        
        os.makedirs(os.path.dirname(db_name_or_path), exist_ok=True)
        
        kwargs.setdefault('timeout', 5)
        conn = sqlite3.connect(db_name_or_path, **kwargs)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"PRAGMA busy_timeout={kwargs['timeout'] * 1000}")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn


def get_adapter():
    """Get or create the global adapter singleton."""
    global _adapter
    if _adapter is None:
        with _adapter_lock:
            if _adapter is None:
                _adapter = DBSessionAdapter()
    return _adapter


def get_db(db_name_or_path=None, **kwargs):
    """
    Get a database connection (PG or SQLite fallback).
    
    Usage:
        conn = get_db('shared.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM x WHERE id = ?", (id,))
        rows = cursor.fetchall()
        conn.close()
    """
    return get_adapter().connect(db_name_or_path, **kwargs)


@contextmanager
def db_cursor(db_name=None, commit=True):
    """Context manager yielding a cursor."""
    conn = get_db(db_name)
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def db_execute(query, params=None, db_name=None):
    """Execute a query, return affected rows."""
    conn = get_db(db_name)
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        rc = cursor.rowcount
        cursor.close()
        return rc
    finally:
        conn.close()


def db_fetchone(query, params=None, db_name=None):
    """Execute and return first row as tuple."""
    conn = get_db(db_name)
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        return result
    finally:
        conn.close()


def db_fetchall(query, params=None, db_name=None):
    """Execute and return all rows as list of tuples."""
    conn = get_db(db_name)
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        cursor.close()
        return result
    finally:
        conn.close()


def ensure_pg_tables():
    """Ensure all required PostgreSQL tables exist."""
    if not get_adapter().is_pg_available():
        logger.debug("PostgreSQL not available, skipping table creation")
        return
    
    conn = get_adapter()._connect_pg()
    try:
        # Use raw psycopg2 cursor for DDL
        cursor = conn._conn.cursor()
        
        schemas = [
            """CREATE TABLE IF NOT EXISTS workflow_runs (
                id TEXT PRIMARY KEY,
                workflow_name TEXT NOT NULL,
                trigger_type TEXT DEFAULT 'manual',
                status TEXT DEFAULT 'running',
                started_at REAL,
                completed_at REAL,
                input_data TEXT DEFAULT '{}',
                output_data TEXT DEFAULT '{}',
                error TEXT,
                duration_ms INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS reminders (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                due_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                source TEXT DEFAULT 'aeryn',
                target TEXT DEFAULT 'all',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                sent_at TEXT,
                metadata TEXT DEFAULT '{}'
            )""",
            """CREATE TABLE IF NOT EXISTS task_queue (
                id TEXT PRIMARY KEY,
                parent_id TEXT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 5,
                progress REAL DEFAULT 0.0,
                result TEXT,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                channel TEXT DEFAULT 'log',
                target TEXT DEFAULT 'all',
                message TEXT NOT NULL,
                level TEXT DEFAULT 'info',
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                sent_at TEXT,
                error TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS daily_log (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL UNIQUE,
                reflection TEXT DEFAULT '',
                interactions INTEGER DEFAULT 0,
                reminders_sent INTEGER DEFAULT 0,
                tasks_completed INTEGER DEFAULT 0,
                system_health TEXT DEFAULT 'unknown',
                notes TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                permissions TEXT DEFAULT '["read"]',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_used TEXT,
                request_count INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS user_notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                scheduled_for TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                channel TEXT DEFAULT 'all',
                metadata TEXT DEFAULT '{}',
                is_sent INTEGER DEFAULT 0,
                sent_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS notification_history (
                id TEXT PRIMARY KEY,
                notification_id TEXT NOT NULL,
                status TEXT NOT NULL,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS quiet_hours (
                user_id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                timezone TEXT DEFAULT 'UTC',
                enabled INTEGER DEFAULT 1
            )""",
            """CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT,
                interaction_type TEXT NOT NULL,
                input_text TEXT,
                output_text TEXT,
                rating INTEGER,
                feedback_text TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS behavior_adjustments (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                adjustment_type TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                reason TEXT,
                confidence REAL DEFAULT 0.5,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS prompt_optimizations (
                id TEXT PRIMARY KEY,
                prompt_name TEXT NOT NULL,
                original_prompt TEXT NOT NULL,
                optimized_prompt TEXT NOT NULL,
                improvement_score REAL,
                applied INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS performance_metrics (
                id TEXT PRIMARY KEY,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                context TEXT,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                timestamp REAL,
                user_id TEXT,
                action TEXT,
                resource TEXT,
                details TEXT,
                ip TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS workspaces (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at REAL,
                updated_at REAL
            )""",
            """CREATE TABLE IF NOT EXISTS workspace_members (
                id SERIAL PRIMARY KEY,
                workspace_id INTEGER,
                user_id TEXT,
                role TEXT,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )""",
            """CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                workspace_id INTEGER,
                name TEXT,
                path TEXT,
                FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
            )""",
        ]
        
        for schema in schemas:
            try:
                cursor.execute(schema)
            except Exception as e:
                logger.error(f"Error creating table: {e}")
        conn._conn.commit()
        cursor.close()
        logger.info("All PostgreSQL tables ensured")
    except Exception as e:
        logger.error(f"Failed to ensure PG tables: {e}")


def patch_sqlite3():
    """
    Monkey-patch sqlite3.connect to route to PostgreSQL when available.
    Must be called once at application startup.
    """
    sqlite3.connect = lambda *args, **kwargs: get_db(args[0] if args else None, **kwargs)  # type: ignore[assignment]
    logger.info("sqlite3.connect patched to use PostgreSQL adapter")

# Auto-patch if DATABASE_URL is set
if os.environ.get('DATABASE_URL'):
    try:
        patch_sqlite3()
    except Exception as e:
        logger.warning(f"Auto-patch failed: {e}")