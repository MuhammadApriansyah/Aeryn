#!/usr/bin/env python3
"""Action registry for Workflow DSL."""
import os
import shutil
from typing import Dict

def action_generate_project(params: Dict, context: Dict):
    """Generate a project."""
    from aeryn_core.oneclick import oneclick_generator
    name = params.get("name", "app")
    template = params.get("template", "react")
    result = oneclick_generator.generate(name, template)
    return result

def action_install_deps(params: Dict, context: Dict):
    """Install dependencies."""
    project_path = params.get("path", context.get("generate_project", {}).get("path", "."))
    os.system(f"cd {project_path} && npm install 2>/dev/null")
    return {"installed": True, "path": project_path}

def action_run_tests(params: Dict, context: Dict):
    """Run tests."""
    project_path = params.get("path", ".")
    result = os.system(f"cd {project_path} && npm test 2>/dev/null")
    return {"tests_passed": result == 0}

def action_deploy(params: Dict, context: Dict):
    """Deploy project."""
    target = params.get("target", "pm2")
    project_path = params.get("path", ".")
    os.system(f"cd {project_path} && pm2 start ecosystem.config.js 2>/dev/null")
    return {"deployed": True, "target": target}

def action_custom(params: Dict, context: Dict):
    """Run custom command."""
    command = params.get("command", "")
    result = os.system(f"{command} 2>/dev/null")
    return {"exit_code": result}

ACTION_MAP = {
    "generate": action_generate_project,
    "install_deps": action_install_deps,
    "run_tests": action_run_tests,
    "deploy": action_deploy,
    "custom": action_custom,
}
