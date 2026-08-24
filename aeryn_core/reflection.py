"""V27.5 — PostRunReflection: refleksi pasca-run dari data yang sudah ada.

Menganalisis trace + plan + episode untuk menghasilkan:
1. Analisis langkah: mana efisien, mana buang waktu
2. Rekomendasi tool (naik/turun status, perlu mentor review)
3. Pelajaran struktural → disimpan terpisah dari episode mentah

Heuristic-first: semua analisis deterministik tanpa LLM. LLM opsional
nanti untuk pola lintas-episode yang lebih halus.
"""
import json
import os
import re
import time
from collections import Counter

REFLECTION_DIR = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/Database/reflections")


class PostRunReflection:
    def __init__(self, registry=None, ledger=None, reflection_dir: str = None):
        self.registry = registry      # ToolGraduationRegistry (opsional)
        self.ledger = ledger          # ParityLedger (opsional)
        self.dir = reflection_dir or REFLECTION_DIR
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, "reflections.jsonl")

    def reflect(self, goal: str, plan: dict, trace: list,
                answer: str = None, error: str = None,
                timed_out: bool = False) -> dict:
        """Analisis satu run → catatan refleksi terstruktur."""
        findings = []
        recommendations = []

        tool_steps = [t for t in trace if t.get("type") == "tool"]
        error_steps = [t for t in trace if t.get("type") == "error"]

        # 1. Efisiensi plan vs eksekusi
        n_subgoals = len((plan or {}).get("subgoals", []))
        n_tool_steps = len(tool_steps)
        if n_subgoals and n_tool_steps > n_subgoals * 2:
            findings.append(
                f"boros: {n_tool_steps} panggilan tool utk {n_subgoals} subgoal "
                f"(rasio {n_tool_steps / n_subgoals:.1f}x)")
        multi_call_rejects = sum(
            1 for t in tool_steps if "MULTI-CALL" in t.get("result_digest", ""))
        if multi_call_rejects:
            findings.append(
                f"{multi_call_rejects} panggilan ditolak guard multi-call — "
                f"model masih menembak serempak")
            recommendations.append(
                "pertimbangkan prompt anti-multi-call lebih agresif di system prompt")

        # 2. Tool bermasalah?
        fails_by_tool = Counter()
        for t in tool_steps:
            digest = t.get("result_digest", "")
            if "'error'" in digest or "governance denied" in digest:
                fails_by_tool[t.get("name", "?")] += 1
        for name, n in fails_by_tool.items():
            if n >= 2:
                findings.append(f"tool '{name}' gagal {n}x dalam satu run")
                rec = self._tool_recommendation(name)
                if rec:
                    recommendations.append(rec)

        # 3. Kegagalan global run
        if timed_out:
            findings.append("run kena wall-budget — goal terlalu besar atau "
                            "provider terlalu lambat")
            recommendations.append("pecah goal atau naikkan max_wall_seconds")
        if error and "HTTP 429" in error:
            recommendations.append("rate-limit provider: rotasi model sudah "
                                   "jalan, pertimbangkan provider tambahan")

        # 4. Run sukses tanpa tool padahal plan minta tool
        if answer and not tool_steps and n_subgoals:
            findings.append("plan meminta tool tapi model jawab langsung — "
                            "kemungkinan halusinasi atau goal terlalu mudah")

        reflection = {
            "ts": time.time(), "goal": goal[:200],
            "ok": answer is not None,
            "findings": findings, "recommendations": recommendations,
            "stats": {"subgoals": n_subgoals, "tool_calls": n_tool_steps,
                      "errors": len(error_steps)},
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(reflection, ensure_ascii=False) + "\n")
        return reflection

    def _tool_recommendation(self, name: str) -> str:
        """Rekomendasi status tool berdasarkan track record registry."""
        if not self.registry or name not in self.registry.tools:
            return ""
        t = self.registry.tools[name]
        total = t["success"] + t["fail"]
        if total < 5:
            return ""
        ratio = t["success"] / total
        if ratio < 0.5 and t["status"] != "bridged":
            return f"tool '{name}' ratio {ratio:.0%} — pertimbangkan turunkan ke bridged"
        if ratio > 0.9 and t["status"] == "shadowing":
            s = self.ledger.summary().get(name, {}) if self.ledger else {}
            if not s.get("graduation_ready"):
                return (f"tool '{name}' ratio {ratio:.0%}: paritas belum 5x "
                        f"beruntun — butuh lebih banyak shadow run")
        return ""

    def digest(self, last_n: int = 20) -> dict:
        """Ringkasan N refleksi terakhir — bahan meta-review V27.3."""
        try:
            with open(self.path, encoding="utf-8") as f:
                lines = f.readlines()[-last_n:]
        except OSError:
            return {"runs": 0}
        refs = [json.loads(l) for l in lines if l.strip()]
        ok = sum(1 for r in refs if r["ok"])
        all_findings = Counter(f for r in refs for f in r["findings"])
        all_recs = Counter(r for r in refs for r in r["recommendations"])
        return {
            "runs": len(refs), "success_rate": round(ok / max(1, len(refs)), 2),
            "top_findings": all_findings.most_common(5),
            "top_recommendations": all_recs.most_common(5),
        }
