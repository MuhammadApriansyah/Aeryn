"""Test V39.4 — fine-tuning putaran metodologi penuh (gen-2).

M17 DoS: math_calc bigint hang → operand/depth guard.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.basic_tools import math_calc


def test_dos_pow_rejected_fast():
    t0 = time.time()
    r = math_calc("9**9**9")
    dt = time.time() - t0
    assert not r["ok"]
    assert "terlalu besar" in r["error"]
    assert dt < 1.0, f"harus ditolak cepat, ternyata {dt:.1f}s"


def test_normal_math_still_works():
    assert math_calc("2**10")["result"] == 1024
    assert math_calc("(10-4)/3")["result"] == 2.0


def test_huge_constant_rejected():
    r = math_calc("99999999999999999999999 * 5")
    assert not r["ok"]


def test_deep_nesting_rejected():
    r = math_calc("(" * 300 + "1" + ")" * 300)
    assert not r["ok"]
