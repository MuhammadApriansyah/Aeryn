#!/usr/bin/env python3
"""Auto Rollback Migration."""
from typing import Dict, List
import os

class AutoRollback:
    """Auto-generate rollback scripts for migrations."""
    
    def __init__(self):
        self._rollback_dir = "migrations/rollback"
    
    def generate_rollback(self, migration_name: str, forward_sql: str) -> str:
        """Generate rollback SQL from forward migration."""
        rollback_statements = []
        
        # Parse CREATE TABLE -> DROP TABLE
        if "CREATE TABLE" in forward_sql.upper():
            table_name = self._extract_table_name(forward_sql)
            rollback_statements.append(f"DROP TABLE IF EXISTS {table_name};")
        
        # Parse ADD COLUMN -> DROP COLUMN
        if "ADD COLUMN" in forward_sql.upper():
            table_name = self._extract_table_name(forward_sql)
            column_name = self._extract_column_name(forward_sql)
            rollback_statements.append(f"-- Note: SQLite doesn't support DROP COLUMN directly")
            rollback_statements.append(f"-- Manual rollback required for {table_name}.{column_name}")
        
        # Parse CREATE INDEX -> DROP INDEX
        if "CREATE INDEX" in forward_sql.upper():
            index_name = self._extract_index_name(forward_sql)
            rollback_statements.append(f"DROP INDEX IF EXISTS {index_name};")
        
        return "\n".join(rollback_statements) if rollback_statements else "-- No automatic rollback available"
    
    def _extract_table_name(self, sql: str) -> str:
        import re
        match = re.search(r"CREATE TABLE\s+(\w+)", sql, re.IGNORECASE)
        return match.group(1) if match else "unknown"
    
    def _extract_column_name(self, sql: str) -> str:
        import re
        match = re.search(r"ADD COLUMN\s+(\w+)", sql, re.IGNORECASE)
        return match.group(1) if match else "unknown"
    
    def _extract_index_name(self, sql: str) -> str:
        import re
        match = re.search(r"CREATE INDEX\s+(\w+)", sql, re.IGNORECASE)
        return match.group(1) if match else "unknown"
    
    def create_rollback_file(self, migration_name: str, forward_sql: str, migrations_dir: str = "migrations"):
        """Create rollback file for a migration."""
        rollback_sql = self.generate_rollback(migration_name, forward_sql)
        
        rollback_dir = os.path.join(migrations_dir, "rollback")
        os.makedirs(rollback_dir, exist_ok=True)
        
        rollback_path = os.path.join(rollback_dir, f"{migration_name}.rollback.sql")
        with open(rollback_path, "w") as f:
            f.write(f"-- Rollback for {migration_name}\n")
            f.write(f"-- Generated automatically\n\n")
            f.write(rollback_sql)
        
        return rollback_path

auto_rollback = AutoRollback()
