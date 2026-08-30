#!/usr/bin/env python3
"""Template Editor."""
import os, json
from typing import Dict

class TemplateEditor:
    def __init__(self, templates_dir="~/.aeryn_templates"):
        self._templates_dir = os.path.expanduser(templates_dir)
        os.makedirs(self._templates_dir, exist_ok=True)
    
    def create_template(self, name: str, description: str, structure: Dict) -> Dict:
        template = {
            "name": name,
            "description": description,
            "structure": structure,
            "created_at": __import__('time').time(),
        }
        
        template_path = os.path.join(self._templates_dir, f"{name}.json")
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        return template
    
    def load_template(self, name: str) -> Dict:
        template_path = os.path.join(self._templates_dir, f"{name}.json")
        if not os.path.exists(template_path):
            return {}
        with open(template_path) as f:
            return json.load(f)
    
    def list_templates(self):
        return [f.replace('.json', '') for f in os.listdir(self._templates_dir) if f.endswith('.json')]
    
    def delete_template(self, name: str):
        template_path = os.path.join(self._templates_dir, f"{name}.json")
        if os.path.exists(template_path):
            os.remove(template_path)
            return True
        return False

template_editor = TemplateEditor()
