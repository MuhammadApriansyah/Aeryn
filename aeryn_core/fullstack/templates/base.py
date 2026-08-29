#!/usr/bin/env python3
"""Base template for full-stack projects."""
from typing import Dict, List
import os

class BaseTemplate:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.frontend = "React"
        self.backend = "Fastify"
        self.database = "SQLite"
    
    def generate(self) -> Dict:
        return {
            "database": self.generate_database(),
            "api": self.generate_api(),
            "backend": self.generate_backend(),
            "frontend": self.generate_frontend(),
            "tests": self.generate_tests(),
            "deploy": self.generate_deploy(),
        }
    
    def generate_database(self) -> Dict:
        return {
            "models": [
                {
                    "name": "User",
                    "fields": [
                        {"name": "id", "type": "INTEGER", "primary": True},
                        {"name": "email", "type": "TEXT", "unique": True},
                        {"name": "password_hash", "type": "TEXT"},
                        {"name": "created_at", "type": "DATETIME"},
                    ]
                }
            ],
            "schemas": [],
            "migrations": [],
            "seeders": []
        }
    
    def generate_api(self) -> Dict:
        return {"endpoints": [], "openapi": {}}
    
    def generate_backend(self) -> Dict:
        return {"files": {}, "dependencies": []}
    
    def generate_frontend(self) -> Dict:
        return {"files": {}, "dependencies": []}
    
    def generate_tests(self) -> Dict:
        return {"unit": "", "integration": "", "e2e": ""}
    
    def generate_deploy(self) -> Dict:
        return {"ecosystem": "", "dockerfile": "", "docker_compose": ""}
