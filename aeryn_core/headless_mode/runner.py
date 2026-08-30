#!/usr/bin/env python3
"""Headless Mode — Fully automated, no prompts."""
import os
import json
from typing import Dict, List, Optional

class HeadlessRunner:
    """Run Aeryn in headless mode for CI/CD automation."""
    
    def __init__(self):
        self._silent = True
        self._exit_on_error = True
    
    def generate(self, config: Dict) -> Dict:
        """Generate project from config dict."""
        from aeryn_core.oneclick import oneclick_generator
        
        name = config.get("name", "app")
        template = config.get("template", "react")
        
        result = oneclick_generator.generate(name, template)
        
        if "error" in result and self._exit_on_error:
            return {"success": False, "error": result["error"]}
        
        # Apply plugins if specified
        plugins = config.get("plugins", [])
        if plugins:
            from aeryn_core.plugin_system import plugin_loader, plugin_registry
            plugin_loader.load_all()
            for plugin in plugins:
                p = plugin_loader.load_by_name(plugin)
                if p:
                    plugin_registry.register(p)
        
        # Run post-generate hooks
        if config.get("post_generate"):
            for hook in config["post_generate"]:
                if hook == "install_deps":
                    os.system(f"cd {result['path']}/api && npm install 2>/dev/null")
                    os.system(f"cd {result['path']}/web && npm install 2>/dev/null")
                elif hook == "run_tests":
                    os.system(f"cd {result['path']} && npm test 2>/dev/null")
        
        return {"success": True, "result": result}
    
    def batch_generate(self, configs: List[Dict]) -> List[Dict]:
        """Generate multiple projects."""
        results = []
        for config in configs:
            result = self.generate(config)
            results.append(result)
        return results

headless_runner = HeadlessRunner()
