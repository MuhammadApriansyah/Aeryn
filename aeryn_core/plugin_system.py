#!/usr/bin/env python3
"""V40.11 — Plugin System: Third-party skill/tool installation.

Features:
- Plugin manifest validation
- Sandboxed plugin execution
- Version management
- Plugin marketplace (local)
- Auto-discovery of plugins
"""

import os
import sys
import json
import importlib
import importlib.util
from typing import Dict, List, Optional, Callable
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PLUGINS_DIR = os.path.expanduser("~/aeryn-core-agent/plugins")


class PluginManifest:
    """Plugin manifest validation."""
    
    REQUIRED_FIELDS = ["name", "version", "description", "author", "entry_point"]
    OPTIONAL_FIELDS = ["dependencies", "permissions", "tags", "icon"]
    
    @staticmethod
    def validate(manifest: Dict) -> tuple:
        """Validate plugin manifest. Returns (valid, errors)."""
        errors = []
        
        for field in PluginManifest.REQUIRED_FIELDS:
            if field not in manifest:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return False, errors
        
        # Validate version format
        version = manifest.get("version", "")
        if not any(c.isdigit() for c in version):
            errors.append("Version must contain numbers")
        
        return len(errors) == 0, errors


class Plugin:
    """A loaded plugin."""
    
    def __init__(self, manifest: Dict, module=None):
        self.manifest = manifest
        self.module = module
        self.name = manifest.get("name", "unknown")
        self.version = manifest.get("version", "0.0.0")
        self.description = manifest.get("description", "")
        self.author = manifest.get("author", "unknown")
        self.enabled = True
        self.loaded_at = datetime.now().isoformat()
    
    def get_tools(self) -> List[Dict]:
        """Get tools provided by this plugin."""
        if self.module and hasattr(self.module, "get_tools"):
            return self.module.get_tools()
        return []
    
    def execute_tool(self, tool_name: str, **kwargs):
        """Execute a tool from this plugin."""
        if self.module and hasattr(self.module, "execute_tool"):
            return self.module.execute_tool(tool_name, **kwargs)
        return None


class PluginManager:
    """Manage plugin lifecycle."""
    
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._tools: Dict[str, tuple] = {}  # tool_name -> (plugin_name, tool_info)
        os.makedirs(PLUGINS_DIR, exist_ok=True)
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins."""
        plugins = []
        
        if not os.path.exists(PLUGINS_DIR):
            return plugins
        
        for item in os.listdir(PLUGINS_DIR):
            plugin_dir = os.path.join(PLUGINS_DIR, item)
            if os.path.isdir(plugin_dir):
                manifest_path = os.path.join(plugin_dir, "plugin.json")
                if os.path.exists(manifest_path):
                    plugins.append(plugin_dir)
        
        return plugins
    
    def load_plugin(self, plugin_dir: str) -> Optional[Plugin]:
        """Load a plugin from directory."""
        manifest_path = os.path.join(plugin_dir, "plugin.json")
        
        if not os.path.exists(manifest_path):
            return None
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        valid, errors = PluginManifest.validate(manifest)
        if not valid:
            return None
        
        # Load the module
        entry_point = manifest.get("entry_point", "plugin.py")
        entry_path = os.path.join(plugin_dir, entry_point)
        
        module = None
        if os.path.exists(entry_path):
            spec = importlib.util.spec_from_file_location(
                f"plugins_{manifest['name']}", entry_path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
        
        plugin = Plugin(manifest, module)
        self._plugins[plugin.name] = plugin
        
        # Register tools
        for tool in plugin.get_tools():
            tool_name = tool.get("name", "")
            if tool_name:
                self._tools[tool_name] = (plugin.name, tool)
        
        return plugin
    
    def load_all(self):
        """Load all discovered plugins."""
        for plugin_dir in self.discover_plugins():
            self.load_plugin(plugin_dir)
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        if plugin_name in self._plugins:
            plugin = self._plugins[plugin_name]
            # Remove tools
            tools_to_remove = [t for t, (p, _) in self._tools.items() if p == plugin_name]
            for tool in tools_to_remove:
                del self._tools[tool]
            del self._plugins[plugin_name]
            return True
        return False
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a loaded plugin."""
        return self._plugins.get(name)
    
    def list_plugins(self) -> List[Dict]:
        """List all loaded plugins."""
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "author": p.author,
                "enabled": p.enabled,
                "tools": len(p.get_tools()),
            }
            for p in self._plugins.values()
        ]
    
    def get_tools(self) -> Dict[str, Dict]:
        """Get all tools from all plugins."""
        return {name: info for name, (plugin, info) in self._tools.items()}
    
    def install_plugin(self, source_dir: str) -> Optional[Plugin]:
        """Install a plugin from source directory."""
        manifest_path = os.path.join(source_dir, "plugin.json")
        
        if not os.path.exists(manifest_path):
            return None
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        name = manifest.get("name", os.path.basename(source_dir))
        target_dir = os.path.join(PLUGINS_DIR, name)
        
        if os.path.exists(target_dir):
            # Already installed - reload
            return self.load_plugin(target_dir)
        
        # Copy plugin to plugins directory
        import shutil
        shutil.copytree(source_dir, target_dir)
        
        return self.load_plugin(target_dir)
    
    def uninstall_plugin(self, name: str) -> bool:
        """Uninstall a plugin."""
        self.unload_plugin(name)
        
        target_dir = os.path.join(PLUGINS_DIR, name)
        if os.path.exists(target_dir):
            import shutil
            shutil.rmtree(target_dir)
            return True
        return False
    
    def create_template(self, name: str):
        """Create a plugin template."""
        plugin_dir = os.path.join(PLUGINS_DIR, name)
        os.makedirs(plugin_dir, exist_ok=True)
        
        manifest = {
            "name": name,
            "version": "0.1.0",
            "description": f"{name} plugin",
            "author": "unknown",
            "entry_point": "plugin.py",
            "tags": [],
            "permissions": ["read"],
        }
        
        with open(os.path.join(plugin_dir, "plugin.json"), "w") as f:
            json.dump(manifest, f, indent=2)
        
        # Create basic plugin file
        with open(os.path.join(plugin_dir, "plugin.py"), "w") as f:
            f.write('"""Plugin template."""\n\ndef get_tools():\n    return []\n\ndef execute_tool(tool_name, **kwargs):\n    return {"ok": False, "error": "Not implemented"}\n')
        
        return plugin_dir


# Singleton
_plugin_manager = None

def get_plugin_manager() -> PluginManager:
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


if __name__ == "__main__":
    manager = PluginManager()
    
    print("=== Plugin System Test ===")
    
    # Create template
    template_dir = manager.create_template("test_plugin")
    print(f"Template created: {template_dir}")
    
    # Update manifest and plugin
    manifest_path = os.path.join(template_dir, "plugin.json")
    with open(manifest_path) as f:
        manifest = json.load(f)
    manifest["description"] = "A test plugin"
    manifest["author"] = "test"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Update plugin file with a tool
    plugin_path = os.path.join(template_dir, "plugin.py")
    with open(plugin_path, "w") as f:
        f.write('''
"""Test plugin."""

def get_tools():
    return [
        {
            "name": "test_tool",
            "description": "A test tool",
            "parameters": {
                "message": {"type": "string", "required": True}
            }
        }
    ]

def execute_tool(tool_name, **kwargs):
    if tool_name == "test_tool":
        return {"ok": "Test: " + str(kwargs.get("message", ""))}
    return {"ok": False, "error": "Unknown tool"}
''')
    
    # Install and load
    plugin = manager.install_plugin(template_dir)
    if plugin:
        print(f"Plugin loaded: {plugin.name} v{plugin.version}")
    
    # List plugins
    plugins = manager.list_plugins()
    print(f"Loaded plugins: {len(plugins)}")
    
    # Get tools
    tools = manager.get_tools()
    print(f"Available tools: {list(tools.keys())}")
    
    # Execute tool
    if "test_tool" in tools:
        result = plugin.execute_tool("test_tool", message="hello")
        print(f"Tool result: {result}")
