#!/usr/bin/env python3
"""Test for supersession module."""
import sys, os, uuid
sys.path.insert(0, '/home/sen/aeryn-core-agent')

from aeryn_core.supersession import SupersessionManager, get_supersession_manager

def test_supersede():
    smgr = SupersessionManager()
    sid = f"ss_{uuid.uuid4().hex[:6]}"
    smgr.supersede(f"{sid}_old", f"{sid}_new", "test")
    assert smgr.is_deprecated(f"{sid}_old")

def test_get_current_version():
    smgr = SupersessionManager()
    sid = f"ss_{uuid.uuid4().hex[:6]}"
    smgr.supersede(f"{sid}_old", f"{sid}_new", "test")
    assert smgr.get_current_version(f"{sid}_old") == f"{sid}_new"

def test_flag_deprecated():
    smgr = SupersessionManager()
    sid = f"ss_{uuid.uuid4().hex[:6]}"
    smgr.supersede(f"{sid}_old", f"{sid}_new", "test")
    flagged = smgr.flag_if_deprecated([{"memory_id": f"{sid}_old", "title": "test"}])
    assert flagged[0].get("is_deprecated") == True