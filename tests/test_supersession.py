#!/usr/bin/env python3
"""Test for supersession module."""
import sys, os, uuid
sys.path.insert(0, '/home/sen/aeryn-core-agent')

from aeryn_core.supersession import SupersessionManager, get_supersession_manager

def test_supersede():
    smgr = SupersessionManager()
    sid = f"ss_{uuid.uuid4().hex[:6]}"
    smgr.supersede(f"{sid}_old", f"{sid}_new", "test")
    return smgr.is_deprecated(f"{sid}_old")

def test_get_current_version():
    smgr = SupersessionManager()
    sid = f"ss_{uuid.uuid4().hex[:6]}"
    smgr.supersede(f"{sid}_old", f"{sid}_new", "test")
    return smgr.get_current_version(f"{sid}_old") == f"{sid}_new"

def test_flag_deprecated():
    smgr = SupersessionManager()
    sid = f"ss_{uuid.uuid4().hex[:6]}"
    smgr.supersede(f"{sid}_old", f"{sid}_new", "test")
    flagged = smgr.flag_if_deprecated([{"memory_id": f"{sid}_old", "title": "test"}])
    return flagged[0].get("is_deprecated") == True

if __name__ == "__main__":
    tests = [test_supersede, test_get_current_version, test_flag_deprecated]
    passed = sum(1 for t in tests if t())
    print(f"supersession: {passed}/{len(tests)}")
    sys.exit(0 if passed == len(tests) else 1)
