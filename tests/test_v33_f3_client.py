"""Test V33-F3 — ModelClient per-key cache.

Request dengan provider/model spesifik TIDAK boleh menimpa client default;
dua kombinasi berbeda → dua instance terpisah; kombinasi sama → instance sama.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import aeryn_daemon
from aeryn_core.model_client import ModelClient


@pytest.fixture(autouse=True)
def _fresh_cache():
    aeryn_daemon._CLIENTS.clear()
    yield
    aeryn_daemon._CLIENTS.clear()


def test_default_then_specific_then_default():
    """Simulasi bug V32: request gemini-specific di tengah request default."""
    c1 = aeryn_daemon._get_client(None, None)          # default
    c2 = aeryn_daemon._get_client("gemini", "gemini-2.5-pro")  # spesifik
    c3 = aeryn_daemon._get_client(None, None)          # default lagi

    assert c1 is c3, "default client tertimpa request spesifik (leak!)"
    assert c1 is not c2, "client spesifik harus instance terpisah"


def test_same_key_same_instance():
    a = aeryn_daemon._get_client("openrouter", None)
    b = aeryn_daemon._get_client("openrouter", None)
    assert a is b, "cache gagal — kombinasi sama harus instance sama"


def test_cache_isolation():
    a = aeryn_daemon._get_client("gemini", "gemini-2.5-pro")
    b = aeryn_daemon._get_client("nous", None)
    assert a is not b
    # dan state provider tidak saling bocor
    assert (a.provider or "").startswith("gemini") or a.provider == "gemini"
