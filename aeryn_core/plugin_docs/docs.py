#!/usr/bin/env python3
"""Plugin API Documentation."""
from typing import Dict

class PluginDocumentation:
    def get_api_reference(self) -> str:
        return '''
# Plugin API Reference

## Creating a Plugin

```python
from aeryn_core.plugin_system.base import AerynPlugin

class MyPlugin(AerynPlugin):
    name = "my_plugin"
    version = "1.0.0"
    description = "My custom plugin"
    author = "Your Name"
    
    def setup(self, config):
        """Initialize plugin."""
        pass
    
    def before_generate(self, plan):
        """Modify plan before generation."""
        return plan
    
    def after_generate(self, project_path, result):
        """Modify result after generation."""
        return result
    
    def on_error(self, error):
        """Handle errors."""
        return str(error)
    
    def get_template_variables(self):
        """Return custom variables."""
        return {}
    
    def get_dependencies(self):
        """Return additional dependencies."""
        return []
```

## Hooks

- `setup(config)` - Initialize with config
- `before_generate(plan)` - Modify plan
- `after_generate(path, result)` - Post-process
- `on_error(error)` - Handle errors
- `get_template_variables()` - Custom variables
- `get_dependencies()` - Extra dependencies
'''
    
    def get_tutorial(self) -> str:
        return '''
# Plugin Tutorial

## Step 1: Create Plugin File

Create a new Python file in `~/.aeryn/plugins/`:

```python
# ~/.aeryn/plugins/hello_plugin.py
from aeryn_core.plugin_system.base import AerynPlugin

class HelloPlugin(AerynPlugin):
    name = "hello"
    version = "1.0.0"
    description = "Adds Hello World endpoint"
    author = "You"
    
    def after_generate(self, project_path, result):
        # Add hello endpoint
        return result
```

## Step 2: Register Plugin

```python
from aeryn_core.plugin_system.registry import plugin_registry
from hello_plugin import HelloPlugin

plugin_registry.register(HelloPlugin)
```

## Step 3: Use Plugin

```bash
aeryn new my-app --plugin hello
```
'''

plugin_docs = PluginDocumentation()
