#!/usr/bin/env python3
"""Database Designer."""
from typing import Dict, List

class DatabaseDesigner:
    def generate(self, plan: Dict) -> Dict:
        models = plan.get("models", [])
        schemas = []
        
        for model in models:
            schema = self._generate_schema(model)
            schemas.append(schema)
        
        return {
            "schemas": schemas,
            "migrations": self._generate_migrations(schemas),
            "seeders": self._generate_seeders(schemas),
        }
    
    def _generate_schema(self, model: Dict) -> str:
        name = model["name"]
        fields = model.get("fields", [])
        
        lines = [f"CREATE TABLE {name.lower()} ("]
        field_defs = []
        
        for field in fields:
            field_def = f"  {field['name']} {field['type']}"
            if field.get("primary"):
                field_def += " PRIMARY KEY"
            if field.get("unique"):
                field_def += " UNIQUE"
            if field.get("foreign"):
                field_def += f" REFERENCES {field['foreign']}"
            field_defs.append(field_def)
        
        lines.extend(",\n".join(field_defs))
        lines.append(");")
        
        return "\n".join(lines)
    
    def _generate_migrations(self, schemas: List[str]) -> List[str]:
        return [
            "-- Migration: initial schema\n" + "\n".join(schemas),
        ]
    
    def _generate_seeders(self, schemas: List[str]) -> List[str]:
        return [
            "-- Seeder: initial data\nINSERT INTO user (email, password) VALUES ('admin@example.com', 'hashed_password');",
        ]
