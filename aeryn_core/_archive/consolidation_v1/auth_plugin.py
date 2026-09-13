#!/usr/bin/env python3
"""Sample authentication plugin."""
from aeryn_core.plugin_system.base import AerynPlugin

class AuthPlugin(AerynPlugin):
    name = "auth"
    version = "1.0.0"
    description = "Adds JWT authentication to generated projects"
    author = "Aeryn Team"
    
    def before_generate(self, plan):
        plan['auth_enabled'] = True
        return plan
    
    def after_generate(self, project_path, result):
        # Add auth middleware file
        result['files'] = result.get('files', {})
        return result
    
    def get_dependencies(self):
        return ["@fastify/jwt", "bcryptjs"]

# Register
from aeryn_core.plugin_system.registry import plugin_registry
plugin_registry.register(AuthPlugin)
