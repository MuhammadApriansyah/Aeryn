"""Test V39.10d — research signals diperluas + drift di nightly."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeryn_core.reasoning_style import needs_research


def test_howto_variants_need_research():
    for g in ("gimana caranya bikin bot discord",
              "bagaimana cara setup vps",
              "cara bikin web portfolio",
              "buat bot telegram gampang gak"):
        assert needs_research(g), g


def test_smalltalk_still_no_research():
    for g in ("kamu lagi ngapain?", "ceritain joke dong", "halo"):
        assert not needs_research(g), g


def test_nightly_runs_drift_guard():
    src = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))),
        "scripts", "nightly_reflection.py")).read()
    assert "drift_guard.py" in src and "hermes_drift" in src
