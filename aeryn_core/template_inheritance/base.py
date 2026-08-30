#!/usr/bin/env python3
"""Template Inheritance — Extend templates."""
from typing import Dict

class TemplateBase:
    def __init__(self):
        self._templates = {}
    
    def register(self, name: str, template: Dict):
        self._templates[name] = template
    
    def extend(self, child_name: str, parent_name: str, overrides: Dict) -> Dict:
        parent = self._templates.get(parent_name, {})
        child = {**parent, **overrides, "name": child_name, "extends": parent_name}
        self._templates[child_name] = child
        return child
    
    def get(self, name: str) -> Dict:
        return self._templates.get(name, {})

template_base = TemplateBase()
