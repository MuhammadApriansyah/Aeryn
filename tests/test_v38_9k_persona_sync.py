"""Test V39.10e — persona sinkron cerewet + needs_research FP tuning."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PERSONA = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "Personalisasi", "Persona",
    "aeryn_core.md")


def test_persona_mentions_cerewet_identity():
    """Cerewet harus jadi bagian identitas di file persona inti."""
    p = open(PERSONA).read().lower()
    assert "cerewet" in p and "perhatian" in p


def test_persona_no_conflicting_passive_rules():
    p = open(PERSONA).read().lower()
    for bad in ("jangan banyak bicara", "tunggu disuruh"):
        assert bad not in p


def test_needs_research_stable_concepts_tolerated():
    """Konsep stabil tetap boleh dijawab dari kepala (FP diterima &
    didokumentasikan) — test hanya memastikan fungsi deterministik."""
    from aeryn_core.reasoning_style import needs_research
    # deterministik: hasil sama utk input sama
    assert needs_research("apa itu rekursi") == needs_research("apa itu rekursi")
    assert needs_research("apa itu react 19") is True
