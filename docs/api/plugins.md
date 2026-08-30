# Plugin System Architecture

> **Purpose**: Document Aeryn's plugin system — how plugins work, how to create them, and how to publish.
> **Rule**: Real plugin system with SQLite-backed registry — no test doubles.

---

## 🏗️ Architecture Overview

```
User Request → Plugin Manager → Plugin Loader → Plugin Runtime → Result
                    ↓
            Plugin Registry (SQLite)
                    ↓
            Plugin Marketplace (Remote/Local)
```

### Key Components

| Component | File | Purpose |
|----------|------|---------|
| `PluginManager` | `aeryn_core/platform/plugin_system/` | Load, enable, disable, execute plugins |
| `PluginRegistry` | `aeryn_core/platform/plugin_system/registry.py` | Track installed plugins |
| `PluginLoader` | `aeryn_core/platform/plugin_system/loader.py` | Load plugin code from disk |
| `PluginMarketplace` | `aeryn_core/plugin_marketplace/` | Browse/publish community plugins |
| `PluginRuntime` | `aeryn_core/platform/tool_runtime.py` | Execute plugin with sandboxing |

---

## 📂 Plugin Directory Structure

```
plugins/
├── installed/
│   ├── code-review/
│   │   ├── manifest.json
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── config.json
│   └── research/
│       ├── manifest.json
│       ├── main.py
│       └── config.json
├── marketplace/
│   └── cache/                 # Cached plugin metadata
└── temp/                      # Temporary plugin downloads
```

### Plugin Manifest (`manifest.json`)

```json
{
  "name": "code-review",
  "version": "1.0.0",
  "description": "Review code for security and quality",
  "author": "Aeryn Core Team",
  "license": "MIT",
  "entry_point": "main.py",
  "permissions": ["read_files", "read_network"],
  "dependencies": [],
  "triggers": ["review code", "code review", "periksa kode"]
}
```

### Plugin Entry Point (`main.py`)

```python
class Plugin:
    def __init__(self, config):
        self.config = config
    
    def execute(self, input_data, context):
        # Real implementation
        result = self._process(input_data)
        return {"status": "ok", "result": result}
    
    def _process(self, input_data):
        # Actual processing logic
        return processed_data
```

---

## 🔧 Plugin Lifecycle

### 1. Discovery
```python
from aeryn_core.platform.plugin_system import get_plugin_manager

manager = get_plugin_manager()
plugins = manager.discover_plugins()  # Scans plugins/installed/
```

### 2. Load
```python
loaded = manager.load_plugin("code-review")
# Returns: Plugin instance or None
```

### 3. Enable
```python
manager.enable_plugin("code-review")
# Sets enabled=True in registry
```

### 4. Execute
```python
result = manager.execute_plugin("code-review", {
    "code": "print('hello world')",
    "language": "python"
})
# Returns: {"status": "ok", "result": [...], "plugins_used": ["code-review"]}
```

### 5. Disable/Uninstall
```python
manager.disable_plugin("code-review")
manager.uninstall_plugin("code-review")
```

---

## 🛒 Plugin Marketplace

### Browse Plugins

```python
from aeryn_core.plugin_marketplace import get_plugin_marketplace

market = get_plugin_marketplace()
results = market.search(query="security", limit=20)
# Returns: [{"id": "...", "name": "...", "description": "...", ...}]
```

### Get Plugin Details

```python
plugin = market.get("plugin_id")
# Returns: full plugin metadata
```

### Publish Plugin

```python
market.publish(
    user_id="user123",
    name="my-plugin",
    source_code="...",
    display_name="My Plugin",
    description="Does something useful",
    version="1.0.0",
    tags=["tag1", "tag2"],
    is_public=True
)
```

### Rate Plugin

```python
market.rate("plugin_id", user_id="user123", rating=5, review="Great!")
```

---

## 🎯 Built-in Plugins

| Plugin | Category | Permissions | Description |
|--------|----------|-------------|-------------|
| `code-review` | Development | read_files | Review code for security, performance, best practices |
| `research` | Knowledge | read_network | Deep research and investigation |
| `database` | Infrastructure | read_write_db | Manage SQLite databases |
| `deploy` | Infrastructure | execute_shell | Deploy applications |
| `analytics` | Monitoring | read_metrics | Track metrics and generate reports |
| `security` | Safety | read_scans | Scan for vulnerabilities |

---

## 🔌 Creating a Custom Plugin

### Step 1: Create Plugin Directory

```bash
mkdir -p plugins/installed/my-plugin
```

### Step 2: Create manifest.json

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "My custom plugin",
  "author": "Your Name",
  "license": "MIT",
  "entry_point": "main.py",
  "permissions": ["read_files"],
  "dependencies": []
}
```

### Step 3: Create main.py

```python
"""My custom Aeryn plugin."""

class Plugin:
    def __init__(self, config):
        self.config = config
        self.name = "my-plugin"
    
    def execute(self, input_data, context):
        """Execute plugin logic."""
        # Your real implementation here
        result = self._process_data(input_data)
        return {
            "status": "ok",
            "plugin": self.name,
            "result": result,
            "version": "1.0.0"
        }
    
    def _process_data(self, data):
        # Real processing logic
        return data
```

### Step 4: Install Plugin

```python
from aeryn_core.platform.plugin_system import get_plugin_manager

manager = get_plugin_manager()
plugin = manager.load_plugin("my-plugin")
manager.enable_plugin("my-plugin")
```

---

## 🧪 Testing Plugins

```bash
# Test plugin loading
python -m pytest tests/test_plugin_system.py -x -q

# Test plugin execution
python -m pytest tests/test_plugins.py -x -q

# Test marketplace
python -m pytest tests/test_plugin_marketplace.py -x -q
```

### Plugin Test Template

```python
import pytest
from aeryn_core.platform.plugin_system import get_plugin_manager

def test_my_plugin():
    manager = get_plugin_manager()
    result = manager.execute_plugin("my-plugin", {"data": "test"})
    assert result["status"] == "ok"
    assert result["result"] is not None
```

---

## 🔒 Security

### Permission System

Plugins declare required permissions in `manifest.json`:
- `read_files` — Read files from disk
- `write_files` — Write to disk
- `execute_shell` — Run shell commands
- `read_network` — Make HTTP requests
- `read_write_db` — Read/write databases

### Sandbox

All plugins execute within the 4-level security sandbox:
1. **Basic**: Input/output filtering
2. **Namespace**: Isolated filesystem
3. **Bubblewrap**: Process isolation
4. **Full**: Complete container isolation

### Review Process

All plugins published to marketplace undergo:
1. Code review (automated)
2. Security scan (OWASP)
3. Performance test
4. Permission verification

---

*Plugin system v59.0 — Updated 2026-08-30.*
