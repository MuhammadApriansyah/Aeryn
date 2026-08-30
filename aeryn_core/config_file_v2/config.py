#!/usr/bin/env python3
"""Config File — .aerynrc for project defaults."""
import os, json
from typing import Dict

class ConfigFile:
    def __init__(self, path=".aerynrc"):
        self._path = path
    
    def exists(self):
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
        # Support dot notation: "defaults.template" -> config["defaults"]["template"]
        keys = key.split(".")
        val = config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val
    
    def set(self, key: str, value):
        config = self.load()
        keys = key.split(".")
        d = config
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        self.save(config)
    
    def generate_default(self):
        default = {"version": "1.0", "defaults": {"template": "react", "database": "sqlite", "auth": True}}
        self.save(default)
        return self._path

config_file = ConfigFile()
