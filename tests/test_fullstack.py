#!/usr/bin/env python3
"""Test Fullstack AI Engineer mode."""
import sys
sys.path.insert(0, '/home/sen/aeryn-core-agent')


def test_planner():
    from aeryn_core.fullstack.planner import ProjectPlanner
    
    planner = ProjectPlanner()
    plan = planner.create_plan("Task App", "A task management app with users and tasks", {})
    
    assert "name" in plan
    assert "database" in plan
    assert "api" in plan
    assert "frontend" in plan
    assert "backend" in plan
    
    db = plan["database"]
    assert len(db["models"]) >= 1
    
    print("✓ ProjectPlanner")


def test_frontend_generator():
    from aeryn_core.fullstack.frontend import FrontendGenerator
    
    gen = FrontendGenerator()
    result = gen.generate({
        "structure": ["src/App.tsx", "src/Home.tsx"],
        "dependencies": ["react"]
    })
    
    assert "files" in result
    assert "src/App.tsx" in result["files"]
    
    print("✓ FrontendGenerator")


def test_backend_generator():
    from aeryn_core.fullstack.backend import BackendGenerator
    
    gen = BackendGenerator()
    result = gen.generate({
        "structure": ["src/server.ts", "src/routes/index.ts"],
        "dependencies": ["fastify"]
    })
    
    assert "files" in result
    assert "src/server.ts" in result["files"]
    
    print("✓ BackendGenerator")


def test_database_designer():
    from aeryn_core.fullstack.database import DatabaseDesigner
    
    designer = DatabaseDesigner()
    result = designer.generate({
        "models": [{"name": "User", "fields": [{"name": "id", "type": "INTEGER", "primary": True}]}]
    })
    
    assert "schemas" in result
    assert len(result["schemas"]) == 1
    assert "user" in result["schemas"][0].lower()
    
    print("✓ DatabaseDesigner")


def test_api_generator():
    from aeryn_core.fullstack.api_gen import APIGenerator
    
    gen = APIGenerator()
    result = gen.generate({
        "endpoints": [{"method": "GET", "path": "/items", "description": "List items"}]
    })
    
    assert "routes" in result
    assert "openapi" in result
    
    print("✓ APIGenerator")


def test_test_generator():
    from aeryn_core.fullstack.test_gen import TestGenerator
    
    gen = TestGenerator()
    result = gen.generate({})
    
    assert "unit" in result
    assert "integration" in result
    assert "e2e" in result
    
    print("✓ TestGenerator")


def test_deploy_manager():
    from aeryn_core.fullstack.deploy import DeployManager
    
    deploy = DeployManager()
    result = deploy.generate({})
    
    assert "ecosystem" in result
    assert "dockerfile" in result
    assert "docker_compose" in result
    
    print("✓ DeployManager")


def test_fullstack_engine():
    from aeryn_core.fullstack.engine import FullstackEngine
    
    engine = FullstackEngine()
    
    # Create project
    project = engine.create_project("Task Manager", "A task management app with user auth", {
        "frontend": "React",
        "backend": "Fastify",
        "database": "SQLite",
    })
    
    assert project["name"] == "Task Manager"
    assert project["status"] == "planned"
    
    # Generate all
    results = engine.generate_all(project["id"])
    
    assert "database" in results
    assert "api" in results
    assert "frontend" in results
    assert "backend" in results
    
    # List projects
    projects = engine.list_projects()
    assert len(projects) >= 1
    
    print("✓ FullstackEngine")


if __name__ == "__main__":
    test_planner()
    test_frontend_generator()
    test_backend_generator()
    test_database_designer()
    test_api_generator()
    test_test_generator()
    test_deploy_manager()
    test_fullstack_engine()
    print("\n✅ All Fullstack AI Engineer tests passed!")
