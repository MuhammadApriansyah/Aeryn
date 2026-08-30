#!/usr/bin/env python3
"""
V2.0 — SQLite-to-PostgreSQL compatibility patch.

Monkey-patches sqlite3.connect to route to PostgreSQL when available,
with automatic fallback to SQLite when PG is not reachable.

Must be imported ONCE at application startup (before any sqlite3.connect call).
"""

import sqlite3 as _sqlite3
import os
import logging

logger = logging.getLogger('aeryn')

# Import the adapter
from aeryn_core.database.db_adapter import get_adapter, ensure_pg_tables

_original_connect = _sqlite3.connect


def _patched_connect(*args, **kwargs):
    """
    Replacement for sqlite3.connect that routes to PostgreSQL when available.
    
    When DATABASE_URL is set and PostgreSQL is reachable, returns a PG connection.
    Otherwise, falls back to original SQLite behavior.
    """
    adapter = get_adapter()
    
    if adapter.is_pg_available():
        # Return PostgreSQL connection (ignores SQLite-specific args)
        return adapter._connect_pg()
    else:
        # Fall back to SQLite with safe defaults
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 5
        conn = _original_connect(*args, **kwargs)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(f"PRAGMA busy_timeout={kwargs['timeout'] * 1000}")
            conn.execute("PRAGMA foreign_keys=ON")
        except Exception:
            pass  # Some SQLite files may not support these
        return conn


def install():
    """Install the monkey-patch."""
    _sqlite3.connect = _patched_connect
    # Also patch the module-level reference
    import sys
    if 'sqlite3' in sys.modules:
        sys.modules['sqlite3'].connect = _patched_connect  # type: ignore[attr-defined]
    logger.info("sqlite3.connect patched for PostgreSQL compatibility")


# Auto-install on import
if os.environ.get('DATABASE_URL', ''):
    try:
        install()
        ensure_pg_tables()
    except Exception as e:
        logger.warning(f"Could not install PG patch: {e}")