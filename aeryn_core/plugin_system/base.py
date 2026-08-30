#!/usr/bin/env python3
"""Base class for Aeryn plugins."""
from typing import Dict, List, Optional, Any

class AerynPlugin:
    """Base class that all plugins must inherit."""
    
    name: str = "unnamed"
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    
    def __init__(self):
        self.enabled = True
        self.config: Dict = {}
    
    def setup(self, config: Dict = None):
        """Initialize plugin with config."""
        if config:
            self.config = config
    
    def before_generate(self, plan: Dict) -> Dict:
        """Hook: Modify plan before generation."""
        return plan
    
    def after_generate(self, project_path: str, result: Dict) -> Dict:
        """Hook: Modify result after generation."""
        return result
    
    def on_error(self, error: Exception) -> Optional[str]:
        """Hook: Handle errors. Return error message or None to suppress."""
        return str(error)
    
    def get_template_variables(self) -> Dict:
        """Return custom template variables."""
        return {}
    
    def get_dependencies(self) -> List[str]:
        """Return additional dependencies."""
        return []
    
    def validate(self) -> bool:
        """Validate plugin configuration."""
        return True
    
    def info(self) -> Dict:
        """Return plugin information."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "enabled": self.enabled,
        }
