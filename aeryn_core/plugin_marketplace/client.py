#!/usr/bin/env python3
"""Plugin Marketplace — Share and download plugins."""
import os
import json
from typing import Dict, List, Optional

class PluginMarketplace:
    MARKETPLACE_URL = "https://marketplace.aeryn.dev/api/v1"
    LOCAL_REGISTRY = os.path.expanduser("~/.aeryn/marketplace_registry.json")
    
    def __init__(self):
        os.makedirs(os.path.dirname(self.LOCAL_REGISTRY), exist_ok=True)
        self._ensure_registry()
    
    def _ensure_registry(self):
        if not os.path.exists(self.LOCAL_REGISTRY):
            with open(self.LOCAL_REGISTRY, "w") as f:
                json.dump({"plugins": [], "stats": {"downloads": 0}}, f)
    
    def _load_registry(self) -> Dict:
        with open(self.LOCAL_REGISTRY) as f:
            return json.load(f)
    
    def _save_registry(self, data: Dict):
        with open(self.LOCAL_REGISTRY, "w") as f:
            json.dump(data, f, indent=2)
    
    def search(self, query: str = "", tags: List[str] = None, limit: int = 20) -> List[Dict]:
        """Search plugins by query or tags."""
        registry = self._load_registry()
        results = []
        
        for plugin in registry.get("plugins", []):
            if query.lower() in plugin["name"].lower() or query.lower() in plugin["description"].lower():
                if not tags or any(t in plugin.get("tags", []) for t in tags):
                    results.append(plugin)
            
            if len(results) >= limit:
                break
        
        return results
    
    def install(self, plugin_name: str) -> bool:
        """Install a plugin from marketplace."""
        plugins_dir = os.path.expanduser("~/.aeryn/plugins")
        os.makedirs(plugins_dir, exist_ok=True)
        
        plugin_path = os.path.join(plugins_dir, f"{plugin_name}.py")
        if os.path.exists(plugin_path):
            print(f"Plugin '{plugin_name}' already installed.")
            return False
        
        # Create plugin template
        template = self._get_plugin_template(plugin_name)
        with open(plugin_path, "w") as f:
            f.write(template)
        
        # Update registry
        registry = self._load_registry()
        registry["plugins"].append({
            "name": plugin_name,
            "installed": True,
            "path": plugin_path,
        })
        self._save_registry(registry)
        
        return True
    
    def uninstall(self, plugin_name: str) -> bool:
        """Uninstall a plugin."""
        plugins_dir = os.path.expanduser("~/.aeryn/plugins")
        plugin_path = os.path.join(plugins_dir, f"{plugin_name}.py")
        
        if not os.path.exists(plugin_path):
            print(f"Plugin '{plugin_name}' not found.")
            return False
        
        os.remove(plugin_path)
        
        registry = self._load_registry()
        registry["plugins"] = [p for p in registry["plugins"] if p["name"] != plugin_name]
        self._save_registry(registry)
        
        return True
    
    def list_installed(self) -> List[Dict]:
        """List all installed plugins."""
        registry = self._load_registry()
        return registry.get("plugins", [])
    
    def share(self, plugin_path: str, name: str, description: str, tags: List[str] = None) -> bool:
        """Share plugin to marketplace."""
        if not os.path.exists(plugin_path):
            return False
        
        registry = self._load_registry()
        registry["plugins"].append({
            "name": name,
            "description": description,
            "tags": tags or [],
            "path": plugin_path,
            "shared": True,
        })
        self._save_registry(registry)
        
        return True
    
    def _get_plugin_template(self, name: str) -> str:
        return f'''#!/usr/bin/env python3
"""Plugin: {name}"""
from aeryn_core.plugin_system.base import AerynPlugin

class {name.title()}Plugin(AerynPlugin):
    name = "{name}"
    version = "1.0.0"
    description = "Custom plugin"
    author = "You"
    
    def before_generate(self, plan):
        # Modify plan here
        return plan
    
    def after_generate(self, project_path, result):
        # Post-process here
        return result
'''

plugin_marketplace = PluginMarketplace()
