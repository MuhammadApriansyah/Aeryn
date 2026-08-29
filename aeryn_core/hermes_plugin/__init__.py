#!/usr/bin/env python3
"""
Hermes Plugin wrapper.
Dipanggil oleh Hermes saat Aeryn running sebagai plugin.
"""

import os

def on_load():
    os.environ["_HERMES_PLUGIN_"] = "1"
    from aeryn_core.hermes_bridge import MODE
    return {"name": "aeryn-core", "version": "41.0", "mode": MODE}

def on_message(message):
    from aeryn_core.hermes_bridge import get_memory
    memory = get_memory()
    return {"status": "ok", "message": message}
