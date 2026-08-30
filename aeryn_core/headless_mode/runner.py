#!/usr/bin/env python3
"""Headless Mode — Fully automated, no prompts."""
import os, json, tempfile, shutil
from typing import Dict, List

class HeadlessRunner:
    def __init__(self):
        self._silent = True
    
    def generate(self, config: Dict) -> Dict:
        from aeryn_core.oneclick import oneclick_generator
        name = config.get("name", "app")
        template = config.get("template", "react")
        result = oneclick_generator.generate(name, template)
        if "error" in result:
            return {"success": False, "error": result["error"]}
        
        if config.get("post_generate"):
            for hook in config["post_generate"]:
                if hook == "install_deps":
                    os.system(f"cd {result['path']}/api && npm install 2>/dev/null")
                    os.system(f"cd {result['path']}/web && npm install 2>/dev/null")
                elif hook == "run_tests":
                    os.system(f"cd {result['path']} && npm test 2>/dev/null")
        return {"success": True, "result": result}
    
    def batch_generate(self, configs: List[Dict]) -> List[Dict]:
        return [self.generate(c) for c in configs]

headless_runner = HeadlessRunner()
