#!/usr/bin/env python3
"""Fullstack AI Engineer — Main orchestration engine."""
import logging
from typing import Dict, List, Optional
from .planner import ProjectPlanner
from .frontend import FrontendGenerator
from .backend import BackendGenerator
from .database import DatabaseDesigner
from .api_gen import APIGenerator
from .test_gen import TestGenerator
from .deploy import DeployManager

logger = logging.getLogger(__name__)

class FullstackEngine:
    def __init__(self):
        self.planner = ProjectPlanner()
        self.frontend = FrontendGenerator()
        self.backend = BackendGenerator()
        self.database = DatabaseDesigner()
        self.api_gen = APIGenerator()
        self.test_gen = TestGenerator()
        self.deploy = DeployManager()
        self._projects = {}
    
    def create_project(self, name: str, description: str, tech_stack: Dict = None) -> Dict:
        project_id = name.lower().replace(" ", "-")
        plan = self.planner.create_plan(name, description, tech_stack)
        project = {
            "id": project_id, "name": name, "description": description,
            "tech_stack": tech_stack or {}, "plan": plan,
            "status": "planned", "phases": {},
        }
        self._projects[project_id] = project
        return project
    
    def generate_all(self, project_id: str) -> Dict:
        project = self._projects.get(project_id)
        if not project:
            return {"error": "Project not found"}
        plan = project["plan"]
        results = {}
        if "database" in plan:
            results["database"] = self.database.generate(plan["database"])
        if "api" in plan:
            results["api"] = self.api_gen.generate(plan["api"])
        if "backend" in plan:
            results["backend"] = self.backend.generate(plan["backend"])
        if "frontend" in plan:
            results["frontend"] = self.frontend.generate(plan["frontend"])
        if "tests" in plan:
            results["tests"] = self.test_gen.generate(plan["tests"])
        if "deploy" in plan:
            results["deploy"] = self.deploy.generate(plan["deploy"])
        project["phases"] = results
        project["status"] = "generated"
        return results
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        return self._projects.get(project_id)
    
    def list_projects(self) -> List[Dict]:
        return [{"id": p["id"], "name": p["name"], "status": p["status"]} for p in self._projects.values()]

fullstack_engine = FullstackEngine()
