"""
Monkey-patch sqlite3.connect to use WAL mode + busy_timeout + foreign_keys.
This module should be imported ONCE at application startup.
All subsequent sqlite3.connect() calls will automatically use safe defaults.
"""
import sqlite3 as _sqlite3

_original_connect = _sqlite3.connect

def _safe_connect(*args, **kwargs):
    """Wrap sqlite3.connect with WAL + busy_timeout + foreign_keys defaults."""
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 5000
    conn = _original_connect(*args, **kwargs)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(f"PRAGMA busy_timeout={kwargs['timeout']}")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

_sqlite3.connect = _safe_connect
