#!/usr/bin/env python3
"""Aeryn Plugin wrapper"""
import os

def on_load():
    os.environ["_HERMES_PLUGIN_"] = "1"
    return {"name": "aeryn-core", "version": "41.0"}

def on_message(message):
    return {"status": "ok", "message": message}
