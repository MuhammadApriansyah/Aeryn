"""V61.1 — Skill Evolution: evaluate candidate skills & evolve them.

B2 (JiuwenSwarm) — mandiri/self-improvement.
Loop: candidate skill → skor sinyal nyata (deterministik, bukan tebakan LLM)
→ keputusan evolve (ACCEPT / REFINE / REJECT) → catat ke bitemporal fact
graph (B1) biar auditable & terlihat.

Sinyal yang digunakan:
  has_description/trigger  -> kelengkapan antarmuka skill
  expertise_len            -> panjang "cara kerjanya" (bukti fungsional)
  example_count            -> berapa banyak contoh/pemakaian nyata
  specyfik (bukan generic) -> hindari skill trivially-generik ('lakukan hal')'

Tidak bergantung LLM: skor dihitung dari properti skill yang dimasukkan.
"""
from __future__ import annotations

import uuid
from datetime import datetime

# Bobot sinyal (disengaja, eksplisit)
_W = {
    "has_description": 20.0,
    "has_trigger": 15.0,
    "expertise_len": 30.0,      # 0..30 (>=600 char → 30)
    "example_count": 20.0,      # 0..20 (>=3 contoh → 20)
    "specificity": 15.0,        # bukannya generic
}
_GENERIC = {"lakukan", "do", "help", "make", "buat", "bantu", "general", "pakai"}


def _len_score(n, cap, max_score):
    return max_score * min(1.0, n / cap)


class SkillCandidate:
    """Data struktur skill yang dievaluasi."""

    def __init__(self, name, description="", trigger="", expertise="",
                 examples=None, source=None):
        self.id = uuid.uuid4().hex[:12]
        self.name = name or ""
        self.description = description or ""
        self.trigger = trigger or ""
        self.expertise = expertise or ""
        self.examples = examples or []
        self.source = source or ""

    def signals(self) -> dict:
        spec = self.description or self.name
        too_generic = any(g in spec.lower() for g in _GENERIC)
        return {
            "has_description": bool(self.description.strip()),
            "has_trigger": bool(self.trigger.strip()),
            "expertise_len": len(self.expertise),
            "example_count": len(self.examples),
            "specific": not too_generic,
        }

    def score(self) -> float:
        s = self.signals()
        total = (
            (_W["has_description"] if s["has_description"] else 0.0)
            + (_W["has_trigger"] if s["has_trigger"] else 0.0)
            + _len_score(s["expertise_len"], 600, _W["expertise_len"])
            + _len_score(s["example_count"], 3, _W["example_count"])
            + (_W["specificity"] if s["specific"] else 0.0)
        )
        return round(total, 1)


def decide(candidate: SkillCandidate) -> dict:
    """Keputusan evolusi berdasarkan skor.

    - ACCEPT (>=70): skill cukup matang, boleh di-promote jadi skill terdaftar.
    - REFINE (40..69): butuh lebih banyak bukti/contoh/deskripsi.
    - REJECT (<40): terlalu tipis/generik/tanpa spesifik — tolak.
    """
    sig = candidate.signals()
    score = candidate.score()

    if score >= 70 and sig["has_description"] and sig["has_trigger"]:
        verdict = "ACCEPT"
        reason = "Matang: deskripsi+trigger ada, bukti & contoh cukup."
    elif score >= 40:
        verdict = "REFINE"
        missing = []
        if not sig["has_description"]:
            missing.append("deskripsi")
        if not sig["has_trigger"]:
            missing.append("trigger")
        if not sig["specific"]:
            missing.append("spesifisitas")
        if sig["expertise_len"] < 600:
            missing.append("ekspertis-lengkap")
        if sig["example_count"] < 3:
            missing.append("contoh")
        reason = "Butuh pengayaan: " + (", ".join(missing) or "sinyal umum")
    else:
        verdict = "REJECT"
        reason = "Terlalu tipis/generik tanpa bukti fungsional yang cukup."

    return {
        "skill_id": candidate.id,
        "name": candidate.name,
        "score": score,
        "verdict": verdict,
        "reason": reason,
        "signals": sig,
    }


def evolve(candidate: SkillCandidate, db=None, fact_store=None) -> dict:
    """Evaluate + record keputusan ke bitemporal graph (auditable)."""
    result = decide(candidate)

    # Catat keputusan ke B1 fact graph (audit trail / self-improvement visible).
    try:
        if fact_store is None:
            from aeryn_core.memory.fact_store import get_fact_store
            fact_store = get_fact_store()
        fact_store.record(
            entity="skill:" + (candidate.name or "?"),
            predicate="evolution",
            fact=result["verdict"],
            source="aeryn_core/adaptive/skill_evolution",
            confidence=max(0.1, result["score"] / 100.0),
        )
    except Exception:
        # Graph tidak wajib — eval tetap jalan meski fakt tidak tercatat.
        pass

    result["evolved_at"] = datetime.utcnow().isoformat()
    return result