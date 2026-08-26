"""Test V38.9l_social_sanitize — sanitasi leak + dedup + key validation."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aeryn_core.social_memory import SocialMemory

DISCORD_KEY = "1541581954439454850"


def _tmp_mem():
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    f.write(json.dumps({"people": {}, "channels": {}}))
    f.close()
    return SocialMemory(f.name), f.name


def test_leak_fragment_blocked():
    """Fragment leak (hasil concat bug) harus ditolak."""
    mem, _ = _tmp_mem()
    assert mem.add_fact(DISCORD_KEY, "Discord user: siaisenmtvsky") is False
    assert mem.add_fact(DISCORD_KEY, "probe-parity-test marker") is False
    assert mem.add_fact(DISCORD_KEY, "memreflex data") is False


def test_real_username_allowed():
    """Username real tidak mengandung fragment leak → boleh."""
    mem, _ = _tmp_mem()
    assert mem.add_fact(DISCORD_KEY, "Discord user: paisenmtvsky") is True
    assert "Discord user: paisenmtvsky" in mem.get_facts(DISCORD_KEY)


def test_dedup_canonical():
    """Fakta duplikat (beda casing/punctuation) → dedup."""
    mem, _ = _tmp_mem()
    mem.add_fact(DISCORD_KEY, "suka UI rapi.")
    assert mem.add_fact(DISCORD_KEY, "SUKA UI RAPi") is False
    assert mem.add_fact(DISCORD_KEY, "suka UI rapi") is False


def test_traversal_key_blocked():
    """Key traversal path injection harus ditolak TOTAL."""
    mem, _ = _tmp_mem()
    assert mem.add_fact("../../etc/passwd", "test") is False
    assert mem.touch_person("../../bad/path") is None
    assert mem.set_relation("../../../evil", "admin") is False


def test_test_marker_key_blocked():
    """Transient session keys jangan jadi kenangan permanen."""
    mem, _ = _tmp_mem()
    assert mem.add_fact("chaos-test", "test") is False
    assert mem.add_fact("fbtest", "test") is False
    assert mem.add_fact("1", "dummy key") is False  # digit pendek


def test_preference_getter():
    """get_preference() untuk social_generator / cerewet."""
    mem, _ = _tmp_mem()
    mem.set_preference(DISCORD_KEY, "nama", "Sen")
    mem.set_preference(DISCORD_KEY, "panggilan", "Sen")
    mem.set_preference(DISCORD_KEY, "bahasa", "id")
    assert mem.get_preference(DISCORD_KEY, "panggilan") == "Sen"
    assert mem.get_preference(DISCORD_KEY, "bahasa") == "id"
    assert mem.get_preference(DISCORD_KEY, "x", default="fb") == "fb"


def test_sanitize_database():
    """sanitize_database harus bersihin traversal/test artifacts."""
    _, tmp_path = _tmp_mem()
    with open(tmp_path, "w") as f:
        json.dump({
            "people": {
                "775664201640706058": {"nama": "Sen",
                                       "fakta": ["Discord user: paisenmtvsky"],
                                       "relasi": "", "preferensi": {}, "last_seen": 0},
                "../../etc/evil": {"nama": "evil", "fakta": [],
                                   "relasi": "", "preferensi": {}},
                "chaos-12345": {"nama": "chaos", "fakta": [],
                                "relasi": "", "preferensi": {}},
                "fbtest": {"nama": "fb", "fakta": [],
                           "relasi": "", "preferensi": {}},
            },
            "channels": {
                "5465": {"nama": "test", "peran": "", "topik_terakhir": "", "last_seen": 0},
                "../etc/channels": {"nama": "evil", "peran": "", "topik_terakhir": "", "last_seen": 0},
            }
        }, f)
    mem = SocialMemory(tmp_path)
    removed = mem.sanitize_database()
    assert "../../etc/evil" not in mem._data["people"]
    assert "chaos-12345" not in mem._data["people"]
    assert "fbtest" not in mem._data["people"]
    assert "../etc/channels" not in mem._data["channels"]
    assert "775664201640706058" in mem._data["people"]
    assert len(removed) >= 3
    facts = mem.get_facts("775664201640706058")
    assert "Discord user: paisenmtvsky" in facts
