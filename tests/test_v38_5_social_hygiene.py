"""Test V38.5 — social memory anti-pollution (lengkap).

Session test/smoke/sub-agent tidak boleh masuk kenalan permanen;
hanya Discord ID nyata + chan_ + nama biasa yang tersimpan.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.social_memory import SocialMemory


def test_discord_ids_are_persistent():
    assert SocialMemory.is_persistent_person_key("1541581954439454850")
    assert SocialMemory.is_persistent_person_key("chan_1541581954439454850")


def test_test_keys_not_persistent():
    for k in ("smoke-v33", "parity-probe", "wrtest2", "sub_214611_0",
              "soptest3", "digestcheck", "e2e-hist", "test_tool",
              "subagent-live", "v36smoke"):
        assert not SocialMemory.is_persistent_person_key(k), k


def test_normal_names_allowed():
    assert SocialMemory.is_persistent_person_key("sen")
    assert SocialMemory.is_persistent_person_key("budi")


def test_remember_guard_uses_same_classifier(monkeypatch):
    """Guard /agent/remember memakai is_persistent_person_key — pastikan
    keputusan konsisten utk contoh nyata."""
    from scripts.aeryn_daemon import SOCIAL
    assert not SOCIAL.is_persistent_person_key("wrtest999")
    assert SOCIAL.is_persistent_person_key("1541584201386696769")
