#!/usr/bin/env python3
"""Test V52 features."""
import sys
import os
sys.path.insert(0, '/home/sen/aeryn-core-agent')


def test_plugin_docs():
    from aeryn_core.plugin_docs import plugin_docs
    docs = plugin_docs.get_api_reference()
    assert "Plugin API Reference" in docs
    print("✓ PluginDocumentation")


def test_auto_rollback():
    from aeryn_core.auto_rollback import auto_rollback
    rollback = auto_rollback.generate_rollback("test", "CREATE TABLE users (id INTEGER PRIMARY KEY)")
    assert "DROP TABLE" in rollback
    print("✓ AutoRollback")


def test_env_management():
    from aeryn_core.env_management import env_manager
    files = env_manager.generate_env_files()
    assert ".env.development" in files
    assert ".env.production" in files
    print("✓ EnvironmentManager")


def test_websocket_template():
    from aeryn_core.websocket_template import websocket_template
    ws = websocket_template.generate_websocket_server()
    assert "websocket" in ws.lower()
    print("✓ WebSocketTemplate")


def test_api_versioning():
    from aeryn_core.api_versioning import api_versioning
    v1 = api_versioning.generate_v1_routes()
    assert "/api/v1/" in v1
    print("✓ APIVersioning")


if __name__ == "__main__":
    test_plugin_docs()
    test_auto_rollback()
    test_env_management()
    test_websocket_template()
    test_api_versioning()
    print("\n✅ All V52 feature tests passed!")
