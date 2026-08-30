#!/usr/bin/env python3
"""Environment Management — Switch between dev/staging/prod."""
import os
import json
from typing import Dict

class EnvironmentManager:
    def __init__(self):
        self._environments = ["development", "staging", "production"]
        self._current = "development"
    
    def get_env_file(self, environment: str) -> str:
        env_vars = {
            "development": {
                "NODE_ENV": "development",
                "PORT": "3010",
                "DATABASE_URL": "sqlite://./dev.db",
                "JWT_SECRET": "dev-secret-key",
                "LOG_LEVEL": "debug",
            },
            "staging": {
                "NODE_ENV": "staging",
                "PORT": "3010",
                "DATABASE_URL": "sqlite://./staging.db",
                "JWT_SECRET": "staging-secret-key",
                "LOG_LEVEL": "info",
            },
            "production": {
                "NODE_ENV": "production",
                "PORT": "3010",
                "DATABASE_URL": "${DATABASE_URL}",
                "JWT_SECRET": "${JWT_SECRET}",
                "LOG_LEVEL": "warn",
            },
        }
        return env_vars.get(environment, env_vars["development"])
    
    def generate_env_files(self) -> Dict:
        files = {}
        for env in self._environments:
            vars = self.get_env_file(env)
            lines = [f"{k}={v}" for k, v in vars.items()]
            files[f".env.{env}"] = "\n".join(lines) + "\n"
        
        # Default .env points to development
        files[".env"] = "# Default environment: development\n# Override with: aeryn env production\n"
        files[".env"] += "\n".join([f"{k}={v}" for k, v in self.get_env_file("development").items()])
        
        return files
    
    def switch_environment(self, target: str) -> bool:
        if target not in self._environments:
            return False
        
        self._current = target
        return True

env_manager = EnvironmentManager()
