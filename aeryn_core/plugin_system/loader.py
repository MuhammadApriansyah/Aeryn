#!/usr/bin/env python3
"""Plugin Loader — Load plugins from various sources."""
import os
import sys
import importlib
import importlib.util
from typing import List, Type, Dict
from .base import AerynPlugin

class PluginLoader:
    """Load plugins from directories and modules."""
    
    def __init__(self):
        self._search_paths = [
            os.path.expanduser("~/.aeryn/plugins"),
            os.path.join(os.getcwd(), ".aeryn", "plugins"),
            os.path.join(os.path.dirname(__file__), "builtin"),
        ]
    
    def add_search_path(self, path: str):
        """Add a directory to search for plugins."""
        if os.path.isdir(path):
            self._search_paths.append(path)
    
    def load_all(self) -> List[AerynPlugin]:
        """Load all plugins from search paths."""
        loaded = []
        
        for search_path in self._search_paths:
            if not os.path.exists(search_path):
                continue
            
            for filename in os.listdir(search_path):
                if filename.endswith('.py') and not filename.startswith('_'):
                    plugin_path = os.path.join(search_path, filename)
                    plugin = self._load_from_file(plugin_path)
                    if plugin:
                        loaded.append(plugin)
        
        return loaded
    
    def load_by_name(self, name: str) -> AerynPlugin | None:
        """Load a specific plugin by name."""
        for search_path in self._search_paths:
            if not os.path.exists(search_path):
                continue
            
            for filename in os.listdir(search_path):
                if filename.endswith('.py') and not filename.startswith('_'):
                    plugin_path = os.path.join(search_path, filename)
                    module_name = filename[:-3]
                    
                    if module_name == name:
                        return self._load_from_file(plugin_path)
        
        return None
    
    def _load_from_file(self, filepath: str) -> Type[AerynPlugin] | None:
        """Load plugin class from a Python file."""
        try:
            module_name = os.path.basename(filepath)[:-3]
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find AerynPlugin subclass in module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, AerynPlugin) and 
                    attr is not AerynPlugin):
                    return attr
            
            return None
        except Exception:
            return None
    
    def get_search_paths(self) -> List[str]:
        """Return current search paths."""
        return self._search_paths

plugin_loader = PluginLoader()
