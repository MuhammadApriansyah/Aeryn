"""Plugin System — dynamic tool loading from plugins."""

import os
import json
import importlib
import importlib.util
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path


class PluginManifest:
    """Represents a plugin manifest."""
    
    def __init__(self, name: str, version: str, description: str, tools: List[Dict[str, Any]] = None):
        self.name = name
        self.version = version
        self.description = description
        self.tools = tools or []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        return cls(
            name=data.get("name", ""),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            tools=data.get("tools", []),
        )


class Plugin:
    """Represents a loaded plugin."""
    
    def __init__(self, manifest: PluginManifest, path: str):
        self.manifest = manifest
        self.path = path
        self.tools: Dict[str, Any] = {}
        self.loaded = False
    
    def load(self, registry=None):
        """Load plugin tools into registry."""
        if self.loaded:
            return True
        
        # Load the plugin module
        plugin_dir = self.path
        main_file = os.path.join(plugin_dir, "main.py")
        
        if not os.path.exists(main_file):
            return False
        
        try:
            # Add plugin dir to path
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)
            
            # Import plugin module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{self.manifest.name}", main_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Register tools
            if registry and hasattr(module, "register_tools"):
                module.register_tools(registry)
            
            # Store tools from manifest
            for tool in self.manifest.tools:
                tool_name = tool.get("name", "")
                tool_handler = getattr(module, tool.get("handler", ""), None)
                if tool_name and tool_handler:
                    registry.register(
                        tool_name,
                        tool.get("description", ""),
                        tool.get("parameters", {}),
                        tool_handler,
                        is_async=tool.get("is_async", False),
                    )
            
            self.loaded = True
            return True
        except Exception as e:
            return False


class PluginLoader:
    """Discover and load plugins from directory."""
    
    def __init__(self, plugin_dir: str = None):
        self.plugin_dir = plugin_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "plugins"
        )
        self.plugins: Dict[str, Plugin] = {}
    
    def discover(self) -> List[Dict[str, Any]]:
        """Discover all plugins in plugin directory."""
        discovered = []
        
        if not os.path.exists(self.plugin_dir):
            return discovered
        
        for entry in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, entry)
            manifest_path = os.path.join(plugin_path, "manifest.json")
            
            if os.path.isdir(plugin_path) and os.path.exists(manifest_path):
                try:
                    with open(manifest_path, encoding="utf-8") as f:
                        manifest_data = json.load(f)
                    
                    manifest = PluginManifest.from_dict(manifest_data)
                    discovered.append({
                        "name": manifest.name,
                        "version": manifest.version,
                        "description": manifest.description,
                        "tools_count": len(manifest.tools),
                        "path": plugin_path,
                    })
                except:
                    continue
        
        return discovered
    
    def load_all(self, registry=None) -> Dict[str, Plugin]:
        """Load all plugins."""
        self.plugins = {}
        
        if not os.path.exists(self.plugin_dir):
            return self.plugins
        
        for entry in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, entry)
            manifest_path = os.path.join(plugin_path, "manifest.json")
            
            if os.path.isdir(plugin_path) and os.path.exists(manifest_path):
                try:
                    with open(manifest_path, encoding="utf-8") as f:
                        manifest_data = json.load(f)
                    
                    manifest = PluginManifest.from_dict(manifest_data)
                    plugin = Plugin(manifest, plugin_path)
                    plugin.load(registry)
                    self.plugins[manifest.name] = plugin
                except:
                    continue
        
        return self.plugins
    
    def load_plugin(self, name: str, registry=None) -> Optional[Plugin]:
        """Load a specific plugin."""
        plugin_path = os.path.join(self.plugin_dir, name)
        manifest_path = os.path.join(plugin_path, "manifest.json")
        
        if not os.path.exists(manifest_path):
            return None
        
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest_data = json.load(f)
            
            manifest = PluginManifest.from_dict(manifest_data)
            plugin = Plugin(manifest, plugin_path)
            plugin.load(registry)
            self.plugins[name] = plugin
            return plugin
        except:
            return None


# Global instance
_loader = None

def get_plugin_loader() -> PluginLoader:
    """Get global plugin loader."""
    global _loader
    if _loader is None:
        _loader = PluginLoader()
    return _loader