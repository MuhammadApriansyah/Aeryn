#!/usr/bin/env python3
"""V39.64 — Hermes Plugin: register Aeryn as Hermes plugin."""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Hermes plugin manifest
PLUGIN_MANIFEST = {
    "name": "aeryn",
    "version": "39.64",
    "description": "Aeryn AI Agent — safety, memory, reasoning",
    "author": "Sen",
    "entry": "apps/hermes_bridge/hermes_bridge.py",
    "api_entry": "apps/api/aeryn_api.py",
    "capabilities": [
        "safety_check",
        "memory_search",
        "adapter_selection",
        "goal_execution",
        "vault_management",
        "social_memory",
    ],
    "config": {
        "AERYN_PORT": 3001,
        "AERYN_HOST": "127.0.0.1",
        "HERMES_URL": "ws://127.0.0.1:3000",
    },
}

def register():
    """Register plugin with Hermes gateway."""
    manifest_path = os.path.expanduser("~/.hermes/plugins/aeryn.json")
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(PLUGIN_MANIFEST, f, indent=2)
    print(f"Plugin registered at: {manifest_path}")

if __name__ == "__main__":
    register()
