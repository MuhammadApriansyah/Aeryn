"""Experience Learning Depth (RM8) — reflexion outcome → pitfalls + skill
crystallization otomatis.

Alur (Aeryn_Identity.md §15 — Experience Learning):
    Reflexion/tool outcome (gagal atau sukses berulang)
    → pitfalls.add (gagal: signature + symptom + root cause + fix)
    → PatternDetector.record_action (sukses berulang: pattern frequency)
    → get_frequent_patterns (min_frequency) → SkillCrystallizer.crystallize
    → skill baru (otomatis dari pengalaman)

Dipanggil dari: agent_loop REFLEXION (tool gagal) + native scheduler daily
tick (konsolidasi pengalaman). Real API only — no test doubles.
"""

from typing import Dict, Any, List


def learn_from_failure(tool_name: str, error: str, context: str = "") -> Dict[str, Any]:
    """Tool gagal → pitfall tersimpan (self-healing library).

    Signature: tool + error-prefix (dedup — pitfall sama tidak duplikat row).
    """
    try:
        from aeryn_core.memory_library import pitfalls
        signature = f"{tool_name}:{error[:40]}".replace(" ", "_").replace('"', "")
        r = pitfalls.add(signature,
                         symptom=f"{tool_name} gagal: {error[:120]}",
                         root_cause=context[:200] or "dari reflexion agent loop",
                         fix="lihat pitfall search — hindari pola yang sama",
                         source="reflexion")
        return {"ok": True, "signature": signature[:80], "result": str(r)[:100]}
    except Exception as e:
        return {"ok": False, "error": f"pitfall add gagal: {str(e)[:150]}"}


def learn_from_success(user_id: str, action_type: str,
                       action_data: Dict) -> Dict[str, Any]:
    """Aksi sukses → pattern tercatat (frequency — kandidat skill)."""
    try:
        from aeryn_core.platform.skill_crystallization import get_skill_crystallizer
        sc = get_skill_crystallizer()
        sc.detector.record_action(user_id, action_type, action_data)
        return {"ok": True, "action_type": action_type}
    except Exception as e:
        return {"ok": False, "error": f"pattern record gagal: {str(e)[:150]}"}


def consolidate_experience(user_id: str = "sen",
                           min_frequency: int = 3,
                           max_crystallize: int = 2) -> Dict[str, Any]:
    """Konsolidasi pengalaman: pattern frekuensi tinggi → skill baru (otomatis).

    Dipanggil native scheduler daily tick — pengalaman tumbuh jadi skill
    tanpa perawatan manual (Aeryn_Identity.md §15).
    """
    try:
        from aeryn_core.platform.skill_crystallization import get_skill_crystallizer
        sc = get_skill_crystallizer()
        patterns = sc.detector.get_frequent_patterns(user_id, min_frequency=min_frequency)
        if not patterns:
            return {"ok": True, "patterns": 0, "crystallized": [],
                    "note": f"belum ada pattern >= {min_frequency}x"}
        crystallized = []
        for p in patterns[:max_crystallize]:
            # Nama skill dari signature (dedup — pattern sama → skill sama)
            skill_name = f"auto_{p['type']}_{abs(hash(p['signature'])) % 10000}"
            try:
                r = sc.crystallize(user_id, p["id"], skill_name,
                                   skill_description=f"otomatis dari pengalaman: {p['signature'][:100]} (frekuensi {p['frequency']}x)")
                crystallized.append({"pattern": p["signature"][:60],
                                     "skill": skill_name,
                                     "frequency": p["frequency"],
                                     "ok": r is not None,
                                     "note": "pattern < min crystallize (2)" if r is None else ""})
            except Exception as e:
                # crystallize gagal (mis. sudah ada) — lanjut pattern berikut
                crystallized.append({"pattern": p["signature"][:60],
                                     "skill": skill_name,
                                     "error": str(e)[:120]})
        return {"ok": True, "patterns": len(patterns),
                "crystallized": crystallized}
    except Exception as e:
        return {"ok": False, "error": f"consolidate gagal: {str(e)[:150]}"}
