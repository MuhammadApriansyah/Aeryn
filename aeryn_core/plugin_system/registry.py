#!/usr/bin/env python3
"""Plugin Registry — Manage all loaded plugins."""
from typing import Dict, List, Type
from .base import AerynPlugin

class PluginRegistry:
    def __init__(self):
        self._plugins: Dict[str, AerynPlugin] = {}
        self._hooks = {
            'before_generate': [],
            'after_generate': [],
            'on_error': [],
        }
    
    def register(self, plugin_class: Type[AerynPlugin]) -> bool:
        instance = plugin_class()
        name = instance.name
        
        if name in self._plugins:
            return False
        
        if not instance.validate():
            return False
        
        self._plugins[name] = instance
        
        # Register hooks
        self._hooks['before_generate'].append(instance.before_generate)
        self._hooks['after_generate'].append(instance.after_generate)
        self._hooks['on_error'].append(instance.on_error)
        
        return True
    
    def unregister(self, name: str) -> bool:
        if name not in self._plugins:
            return False
        
        instance = self._plugins.pop(name)
        
        self._hooks['before_generate'].remove(instance.before_generate)
        self._hooks['after_generate'].remove(instance.after_generate)
        self._hooks['on_error'].remove(instance.on_error)
        
        return True
    
    def get(self, name: str) -> AerynPlugin | None:
        return self._plugins.get(name)
    
    def get_all(self) -> List[AerynPlugin]:
        return list(self._plugins.values())
    
    def execute_before_generate(self, plan: Dict) -> Dict:
        for hook in self._hooks['before_generate']:
            plan = hook(plan)
        return plan
    
    def execute_after_generate(self, project_path: str, result: Dict) -> Dict:
        for hook in self._hooks['after_generate']:
            result = hook(project_path, result)
        return result
    
    def execute_on_error(self, error: Exception) -> List[str]:
        messages = []
        for hook in self._hooks['on_error']:
            msg = hook(error)
            if msg:
                messages.append(msg)
        return messages

plugin_registry = PluginRegistry()
