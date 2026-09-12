"""V61.1 — Auto Harness Loop (B3): evaluate → feedback → tune harness.

Loop tertutup untuk tuning yang jujur & deterministik (bukan asumsi):
  1. Terima batch tugas (prompt, expected, actual[, category, judge]).
  2. Skor tiap tugas: PASS jika actual cocok expected (contains/equality/ganjaran
     judge_fn), else FAIL.
  3. Agregasi: pass_rate total + per-category.
  4. Feedback/TUNING: kategori dgn fail-rate tertinggi → rekomendasi tune
     (contoh lebih banyak, prompt lebih tegas, batas lebih ketat, dll)
     berdasarkan aturan deterministik.
  5. Catat ringkasan ke biemporal fact graph (B1) biar auditable.

Tidak memakai tebakan LLM untuk skor — perbandingan string eksplisit.
"""
from __future__ import annotations

import re
from datetime import datetime


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _judge(expected: str, actual: str, mode: str) -> bool:
    e, a = _normalize(expected), _normalize(actual)
    if mode == "eq":
        return a == e
    if mode == "contains":
        return bool(e) and e in a
    if mode == "any_kw":
        # pass jika semua kata kunci pada 'expected' ada di actual
        toks = [t for t in expected.split() if t]
        return bool(toks) and all(t in a for t in toks)
    return a == e  # default eq


def run_evals(tasks, categories=True) -> dict:
    """Skor batch tugas; return ringkasan + tuning feedback."""
    if not tasks:
        return {
            "total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0,
            "results": [], "feedback": [], "recorded": True,
        }

    results = []
    fails_by_cat = {}
    total_by_cat = {}

    def _cat(t):
        return (t.get("category") or "uncategorized").strip() or "uncategorized"

    for t in tasks:
        mode = t.get("judge", t.get("mode", "contains"))
        ok = _judge(t.get("expected", ""), t.get("actual", ""), mode)
        cat = _cat(t)
        total_by_cat[cat] = total_by_cat.get(cat, 0) + 1
        if not ok:
            fails_by_cat[cat] = fails_by_cat.get(cat, 0) + 1
        results.append({
            "prompt": t.get("prompt", ""),
            "category": cat,
            "mode": mode,
            "pass": ok,
            "expected": t.get("expected", ""),
            "actual": t.get("actual", "")[:200],
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    pass_rate = round(passed / total * 100, 1)

    # Tuning feedback (detail plus value where failed).
    feedback = []
    for cat, fails in fails_by_cat.items():
        ttl = total_by_cat[cat]
        rate = round(fails / ttl * 100, 1)
        if rate >= 50:
            action = "PERLU TUNING KERAS"
            detail = "Gagal mayoritas: tambah contoh, tegas kriterium, atau bedah kategori."
        elif rate >= 25:
            action = "TUNING SEDANG"
            detail = "Sebagian gagal: pertajam expected/actual atau split kategori."
        else:
            action = "OK"
            detail = "Failure minor — pantau."
        feedback.append({
            "category": cat, "failed": fails, "total": ttl,
            "fail_rate": rate, "action": action, "detail": detail,
        })

    # Urutkan feedback dari yang paling parah.
    feedback.sort(key=lambda f: f["fail_rate"], reverse=True)

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": pass_rate,
        "results": results,
        "feedback": feedback,
        "generated_at": datetime.utcnow().isoformat(),
    }


def run_and_record(tasks, fact_store=None) -> dict:
    """Jalankan eval + catat ringkasan ke fact graph (auditable)."""
    out = run_evals(tasks)
    try:
        if fact_store is None:
            from aeryn_core.memory.fact_store import get_fact_store
            fact_store = get_fact_store()
        fact_store.record(
            entity="harness:latest",
            predicate="pass_rate",
            fact=str(out["pass_rate"]),
            source="aeryn_core/adaptive/auto_harness",
            confidence=min(1.0, out["pass_rate"] / 100.0),
        )
        most = next((f for f in out["feedback"]), None)
        if most:
            fact_store.record(
                entity="harness:latest",
                predicate="tune_focus",
                fact=(most["category"] + ":" + most["action"]),
                source="aeryn_core/adaptive/auto_harness",
            )
        out["recorded"] = True
    except Exception:
        out["recorded"] = False
    return out