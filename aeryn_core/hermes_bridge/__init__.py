#!/usr/bin/env python3
"""
Hermes Bridge — Adapter layer untuk integrasi dengan Hermes.
"""

import os
import sys
import logging

from .loader import load_skills, load_scripts, get_skill, get_script, list_all_skills, list_all_scripts

logger = logging.getLogger(__name__)

HERMES_HOME = os.path.expanduser("~/.hermes")
HERMES_AVAILABLE = os.path.exists(HERMES_HOME)

def _detect_mode():
    if os.environ.get("_HERMES_PLUGIN_") == "1":
        return "plugin"
    elif HERMES_AVAILABLE:
        return "standalone-with-hermes"
    else:
        return "standalone"

MODE = _detect_mode()

def is_plugin():
    return MODE == "plugin"

def has_hermes():
    return MODE != "standalone"

def get_memory():
    if has_hermes():
        try:
            sys.path.insert(0, f"{HERMES_HOME}/scripts")
            from memory_library import MemoryLibrary
            return MemoryLibrary()
        except ImportError:
            pass
    from aeryn_core.memory.core_memory import CoreMemory
    return CoreMemory()

__all__ = [
    'MODE', 'is_plugin', 'has_hermes', 'get_memory',
    'load_skills', 'load_scripts', 'get_skill', 'get_script',
    'list_all_skills', 'list_all_scripts',
]
