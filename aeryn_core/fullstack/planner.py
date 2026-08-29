#!/usr/bin/env python3
"""Project Planner — Generate project plans and architecture."""
from typing import Dict, List, Optional

class ProjectPlanner:
    """Create project plans based on requirements."""
    
    def create_plan(self, name: str, description: str, tech_stack: Dict = None) -> Dict:
        """Create comprehensive project plan."""
        tech = tech_stack or {}
        
        plan = {
            "name": name,
            "description": description,
            "tech_stack": {
                "frontend": tech.get("frontend", "React"),
                "backend": tech.get("backend", "Fastify"),
                "database": tech.get("database", "SQLite"),
                "orm": tech.get("orm", "Prisma"),
                "auth": tech.get("auth", "JWT"),
            },
            "database": self._plan_database(description),
            "api": self._plan_api(description),
            "backend": self._plan_backend(description),
            "frontend": self._plan_frontend(description),
            "tests": self._plan_tests(),
            "deploy": self._plan_deploy(),
        }
        return plan
    
    def _plan_database(self, description: str) -> Dict:
        """Generate database schema plan."""
        desc_lower = description.lower()
        models = []
        
        if "user" in desc_lower or "auth" in desc_lower:
            models.append({
                "name": "User",
                "fields": [
                    {"name": "id", "type": "INTEGER", "primary": True},
                    {"name": "email", "type": "TEXT", "unique": True},
                    {"name": "password", "type": "TEXT"},
                    {"name": "created_at", "type": "DATETIME"},
                ]
            })
        
        if "task" in desc_lower or "todo" in desc_lower:
            models.append({
                "name": "Task",
                "fields": [
                    {"name": "id", "type": "INTEGER", "primary": True},
                    {"name": "title", "type": "TEXT"},
                    {"name": "description", "type": "TEXT"},
                    {"name": "completed", "type": "BOOLEAN"},
                    {"name": "user_id", "type": "INTEGER", "foreign": "User.id"},
                ]
            })
        
        if not models:
            models.append({
                "name": "Item",
                "fields": [
                    {"name": "id", "type": "INTEGER", "primary": True},
                    {"name": "name", "type": "TEXT"},
                    {"name": "created_at", "type": "DATETIME"},
                ]
            })
        
        return {"models": models}
    
    def _plan_api(self, description: str) -> Dict:
        """Generate API endpoints plan."""
        desc_lower = description.lower()
        endpoints = []
        
        if "user" in desc_lower or "auth" in desc_lower:
            endpoints.extend([
                {"method": "POST", "path": "/auth/register", "description": "Register user"},
                {"method": "POST", "path": "/auth/login", "description": "Login user"},
                {"method": "GET", "path": "/auth/me", "description": "Get current user"},
            ])
        
        if "task" in desc_lower or "todo" in desc_lower:
            endpoints.extend([
                {"method": "GET", "path": "/tasks", "description": "List tasks"},
                {"method": "POST", "path": "/tasks", "description": "Create task"},
                {"method": "PUT", "path": "/tasks/:id", "description": "Update task"},
                {"method": "DELETE", "path": "/tasks/:id", "description": "Delete task"},
            ])
        
        if not endpoints:
            endpoints.extend([
                {"method": "GET", "path": "/items", "description": "List items"},
                {"method": "POST", "path": "/items", "description": "Create item"},
            ])
        
        return {"endpoints": endpoints}
    
    def _plan_backend(self, description: str) -> Dict:
        """Generate backend structure plan."""
        return {
            "structure": [
                "src/server.ts",
                "src/routes/index.ts",
                "src/controllers/index.ts",
                "src/services/index.ts",
                "src/middleware/auth.ts",
                "src/utils/logger.ts",
            ],
            "dependencies": ["fastify", "@fastify/cors", "@fastify/jwt", "zod"]
        }
    
    def _plan_frontend(self, description: str) -> Dict:
        """Generate frontend structure plan."""
        return {
            "structure": [
                "src/App.tsx",
                "src/main.tsx",
                "src/pages/Home.tsx",
                "src/components/Layout.tsx",
                "src/hooks/useApi.ts",
                "src/utils/api.ts",
            ],
            "dependencies": ["react", "react-dom", "react-router-dom", "@tanstack/react-query"]
        }
    
    def _plan_tests(self) -> Dict:
        """Generate test plan."""
        return {
            "unit": ["tests/unit/*.test.ts"],
            "integration": ["tests/integration/*.test.ts"],
            "e2e": ["tests/e2e/*.spec.ts"],
        }
    
    def _plan_deploy(self) -> Dict:
        """Generate deployment plan."""
        return {
            "targets": ["pm2", "docker", "vercel"],
            "config": ["ecosystem.config.js", "Dockerfile", "docker-compose.yml"],
        }
