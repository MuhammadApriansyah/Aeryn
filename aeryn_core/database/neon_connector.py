#!/usr/bin/env python3
"""
V41.0 — Neon PostgreSQL Connector.
Connects to Neon PostgreSQL with pgvector support.
"""

import os
import json
import urllib.request
from typing import Optional, Dict, List, Any

# Neon connection string
NEON_URL = os.environ.get("NEON_DATABASE_URL", "")

# Parse connection string
def parse_connection_string(url: str) -> Dict[str, str]:
    """Parse PostgreSQL connection string into components."""
    # Remove protocol
    without_protocol = url.replace("postgresql://", "")
    
    # Split user:pass@host/db?params
    user_pass, rest = without_protocol.split("@", 1)
    user, password = user_pass.split(":", 1)
    
    host_port_db, params = rest.split("?", 1) if "?" in rest else (rest, "")
    host_port, database = host_port_db.split("/", 1)
    
    # Parse host:port
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host = host_port
        port = "5432"
    
    return {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "database": database,
        "params": params,
    }

# Check if psycopg2 available
def check_psycopg2():
    """Check if psycopg2 is installed."""
    try:
        import psycopg2
        return True
    except ImportError:
        return False

# Check if psycopg2-binary available
def check_psycopg2_binary():
    """Check if psycopg2-binary is installed."""
    try:
        import psycopg2
        from psycopg2 import sql
        return True
    except ImportError:
        return False

# Install psycopg2-binary
def install_psycopg2_binary():
    """Install psycopg2-binary via pip."""
    import subprocess
    result = subprocess.run(
        ["pip", "install", "psycopg2-binary", "pgvector"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

# Test connection
def test_connection(url: str) -> bool:
    """Test connection to Neon PostgreSQL."""
    try:
        import psycopg2
        conn = psycopg2.connect(url)
        conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
