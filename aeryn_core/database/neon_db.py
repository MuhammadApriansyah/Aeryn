#!/usr/bin/env python3
"""
V41.0 — Neon Database Layer.
Provides connection pooling and query execution for PostgreSQL.
"""

import os
import json
import re
import logging
from typing import Optional, Dict, List, Any
from contextlib import contextmanager

logger = logging.getLogger('aeryn')

# Neon connection string
NEON_URL = os.environ.get("NEON_DATABASE_URL", "")

class NeonDB:
    """PostgreSQL database layer for Aeryn."""
    
    def __init__(self, connection_url: str = None):
        self.connection_url = connection_url or NEON_URL
        self._available = None
    
    def is_available(self) -> bool:
        """Check if PostgreSQL is available."""
        if self._available is not None:
            return self._available
        
        try:
            import psycopg2
            conn = psycopg2.connect(self.connection_url)
            conn.close()
            self._available = True
            return True
        except Exception:
            self._available = False
            return False
    
    @contextmanager
    def get_connection(self):
        """Get a database connection as context manager."""
        import psycopg2
        conn = None
        try:
            conn = psycopg2.connect(self.connection_url)
            yield conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, commit: bool = True):
        """Get a cursor as context manager."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database query failed: {e}")
                raise
            finally:
                cursor.close()
    
    def execute(self, query: str, params: tuple = None) -> None:
        """Execute a single query."""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
    
    def fetchone(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Execute query and return single result."""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            row = cursor.fetchone()
            if row:
                return dict(zip(columns, row))
            return None
    
    def fetchall(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query and return all results."""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    
    def _sanitize_table_name(self, table: str) -> None:
        """Validate table name format — raise if invalid."""
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', table):
            raise ValueError(f"Invalid table name: {table!r}")

    def create_table(self, table_name: str, schema: str) -> None:
        """Create a table if not exists."""
        self._sanitize_table_name(table_name)
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
        self.execute(query)

    def drop_table(self, table_name: str) -> None:
        """Drop a table if exists."""
        self._sanitize_table_name(table_name)
        query = f"DROP TABLE IF EXISTS {table_name} CASCADE"
        self.execute(query)

    def insert(self, table: str, data: Dict[str, Any]) -> None:
        """Insert a row into table."""
        self._sanitize_table_name(table)
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = "INSERT INTO {} ({}) VALUES ({})".format(self._sanitize_table_name(table), columns, placeholders)
        self.execute(query, tuple(data.values()))

    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple = None) -> None:
        """Update rows in table."""
        self._sanitize_table_name(table)
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        query = "UPDATE {} SET {} WHERE {}".format(self._sanitize_table_name(table), set_clause, where)
        params = tuple(data.values()) + (where_params or ())
        self.execute(query, params)

    def delete(self, table: str, where: str, where_params: tuple = None) -> None:
        """Delete rows from table."""
        self._sanitize_table_name(table)
        query = "DELETE FROM {} WHERE {}".format(self._sanitize_table_name(table), where)
        self.execute(query, where_params)

    def select(self, table: str, where: str = None, params: tuple = None, 
               order_by: str = None, limit: int = None) -> List[Dict]:
        """Select rows from table."""
        self._sanitize_table_name(table)
        query = "SELECT * FROM {}".format(self._sanitize_table_name(table))
        if where:
            query += f" WHERE {where}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
        return self.fetchall(query, params)


# Singleton
_neon_db = None

def get_neon() -> NeonDB:
    """Get or create NeonDB singleton."""
    global _neon_db
    if _neon_db is None:
        _neon_db = NeonDB()
    return _neon_db
