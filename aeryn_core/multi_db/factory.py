#!/usr/bin/env python3
"""Database Factory — Support multiple databases."""
from typing import Dict

class DatabaseFactory:
    def __init__(self):
        self._drivers = {
            "sqlite": {
                "package": "better-sqlite3",
                "connection": "new Database('{database}')",
                "pragmas": ["journal_mode = WAL", "foreign_keys = ON"],
            },
            "postgres": {
                "package": "pg",
                "connection": "new Pool({{ connectionString: process.env.DATABASE_URL }})",
                "pragmas": [],
            },
            "mysql": {
                "package": "mysql2",
                "connection": "createPool({{ host: process.env.DB_HOST, user: process.env.DB_USER, password: process.env.DB_PASSWORD, database: process.env.DB_NAME }})",
                "pragmas": [],
            },
        }
    
    def get_driver(self, db_type: str) -> Dict:
        return self._drivers.get(db_type, self._drivers["sqlite"])
    
    def list_drivers(self):
        return list(self._drivers.keys())
    
    def generate_connection(self, db_type: str, db_name: str = "app.db") -> str:
        driver = self.get_driver(db_type)
        
        if db_type == "sqlite":
            return f'''import Database from '{driver["package"]}';
const db = new Database('{db_name}');
db.pragma('{driver["pragmas"][0]}');
db.pragma('{driver["pragmas"][1]}');
export {{ db }};
'''
        elif db_type == "postgres":
            return f'''import {{ Pool }} from '{driver["package"]}';
{driver["connection"]}
export {{ Pool }};
'''
        elif db_type == "mysql":
            return f'''import {{ createPool }} from '{driver["package"]}';
{driver["connection"]}
export {{ createPool }};
'''
        return ""

database_factory = DatabaseFactory()
