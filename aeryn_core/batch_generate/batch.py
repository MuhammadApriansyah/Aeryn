#!/usr/bin/env python3
"""Batch Generate — Generate multiple projects."""
import os
import json
from typing import Dict, List

class BatchGenerator:
    def __init__(self):
        pass
    
    def generate_from_file(self, batch_config_path: str) -> List[Dict]:
        """Generate projects from a JSON config file."""
        if not os.path.exists(batch_config_path):
            return [{"error": f"Config not found: {batch_config_path}"}]
        
        with open(batch_config_path) as f:
            batch_config = json.load(f)
        
        projects = batch_config.get("projects", [])
        results = []
        
        for project in projects:
            result = self._generate_one(project)
            results.append(result)
        
        return results
    
    def generate_from_list(self, projects: List[Dict]) -> List[Dict]:
        """Generate projects from a list of configs."""
        results = []
        for project in projects:
            result = self._generate_one(project)
            results.append(result)
        return results
    
    def _generate_one(self, config: Dict) -> Dict:
        from aeryn_core.oneclick import oneclick_generator
        
        name = config.get("name", "app")
        template = config.get("template", "react")
        
        try:
            result = oneclick_generator.generate(name, template)
            return {"success": True, "name": name, "result": result}
        except Exception as e:
            return {"success": False, "name": name, "error": str(e)}

batch_generator = BatchGenerator()
