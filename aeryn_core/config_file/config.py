#!/usr/bin/env python3
"""Config File — .aerynrc for project defaults."""
import os
import json
from typing import Dict

class ConfigFile:
    """Manage .aerynrc configuration file."""
    
    def __init__(self, config_path=".aerynrc"):
        self._path = config_path
    
    def exists(self) -> bool:
        return os.path.exists(self._path)
    
    def load(self) -> Dict:
        if not self.exists():
            return {}
        
        try:
            with open(self._path) as f:
                return json.load(f)
        except:
            return {}
    
    def save(self, config: Dict):
        with open(self._path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get(self, key: str, default=None):
        config = self.load()
        return config.get(key, default)
    
    def set(self, key: str, value):
        config = self.load()
        config[key] = value
        self.save(config)
    
    def generate_default(self) -> str:
        default = {
            "version": "1.0",
            "defaults": {
                "template": "react",
                "database": "sqlite",
                "auth": True,
                "testing": True,
                "ci_cd": True,
            },
            "plugins": [],
            "environments": {
                "development": {"port": 3010},
                "staging": {"port": 3011},
                "production": {"port": 3012},
            },
        }
        
        self.save(default)
        return self._path

config_file = ConfigFile()
