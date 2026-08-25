"""V30.2 — MultiAgentRunner: goal kompleks → subgoal dieksekusi paralel.

Goal dengan plan multi-subgoal dipecah: tiap subgoal jadi run mandiri
dengan session_id unik (lock per-session V28 mencegah race). Hasil
dikumpulkan, dirangkum, dan digabung jadi jawaban final oleh model utama.

Desain:
- Worker = fungsi murni yang memanggil _run_steps-equivalent ringkas
  (satu LLM call + tool loop kecil per subgoal) — TIDAK rekursif.
- Paralel via ThreadPoolExecutor (max_workers ≤ 4 — hemat kuota Groq).
- Fail-soft: satu worker gagal tidak menjatuhkan gabungan.
"""
import json
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 4


class MultiAgentRunner:
    def __init__(self, model_client, tools_registry, gate, shadow,
                 max_workers: int = MAX_WORKERS):
        self.model = model_client
        self.tools = tools_registry
        self.gate = gate
        self.shadow = shadow
        self.max_workers = min(max_workers, MAX_WORKERS)

    def run_subgoal(self, session_id: str, subgoal_desc: str,
                    tool_hint: str, max_iterations: int = 3) -> dict:
        """Satu worker: selesaikan satu subgoal secara independen."""
        system = (
            "Kamu worker Aeryn. Selesaikan SATU subgoal ini secara mandiri.\n"
            f"Subgoal: {subgoal_desc}\n"
            f"Tool disarankan: {tool_hint}. Satu tool-call per giliran.\n"
            "Setelah selesai, rangkum hasilnya singkat.")
        messages = [{"role": "system", "content": system},
                    {"role": "user", "content": subgoal_desc}]
        trace = []
        for i in range(max_iterations):
            try:
                resp = self.model.chat(messages, tools=self.tools.schemas())
            except (urllib.error.HTTPError, urllib.error.URLError,
                    RuntimeError, TimeoutError) as e:
                return {"subgoal": subgoal_desc, "ok": False,
                        "error": f"LLM: {e}"[:120], "trace": trace}
            msg = resp["choices"][0]["message"]
            calls = msg.get("tool_calls") or []
            if not calls:
                return {"subgoal": subgoal_desc, "ok": True,
                        "answer": msg.get("content"), "trace": trace}
            messages.append(msg)
            call = calls[0]                     # guard single-call
            fn = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
            except ValueError:
                args = {}
            entry = self.tools.tools.get(fn)
            if entry is None:
                result = {"error": f"unknown tool: {fn}"}
            else:
                gv = self.gate.evaluate(fn, entry["tier"], entry["status"],
                                        entry["success"], entry["fail"], args)
                if not gv["allowed"]:
                    result = {"error": f"governance denied: {gv['reason']}"}
                else:
                    try:
                        result = self.shadow.run_with_shadow(fn, args)
                    except Exception as te:
                        result = {"error": f"{type(te).__name__}: {te}"}
            trace.append({"step": i, "name": fn,
                          "digest": str(result)[:150]})
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": json.dumps(result, ensure_ascii=False)[:4000]})
        return {"subgoal": subgoal_desc, "ok": False,
                "error": "max iterations habis", "trace": trace}

    def run_parallel(self, plan: dict, base_session_id: str,
                     max_wall_s: float = 180.0) -> dict:
        """Eksekusi semua subgoal plan secara paralel; kembalikan gabungan."""
        subgoals = [sg for sg in plan.get("subgoals", [])
                    if sg.get("desc")]
        if len(subgoals) < 2:
            return {"parallel": False,
                    "reason": "butuh ≥ 2 subgoal untuk paralel"}
        t0 = time.time()
        results = [None] * len(subgoals)
        with ThreadPoolExecutor(self.max_workers) as ex:
            futs = {ex.submit(self.run_subgoal,
                              f"{base_session_id}_w{i}",
                              sg["desc"][:300], sg.get("tool_hint", "none")): i
                    for i, sg in enumerate(subgoals)}
            for fut in as_completed(futs, timeout=max_wall_s):
                idx = futs[fut]
                try:
                    results[idx] = fut.result()
                except Exception as e:
                    results[idx] = {"subgoal": subgoals[idx]["desc"][:100],
                                    "ok": False, "error": str(e)[:120]}
        wall = time.time() - t0
        oks = sum(1 for r in results if r and r.get("ok"))
        return {"parallel": True, "wall_s": round(wall, 1),
                "workers": len(subgoals), "success": oks,
                "results": results}

    @staticmethod
    def merge_for_final(parallel_out: dict) -> str:
        """Gabungkan hasil worker jadi blok teks untuk model utama merangkum."""
        if not parallel_out.get("parallel"):
            return ""
        lines = ["## Hasil paralel worker"]
        for r in parallel_out.get("results", []):
            if r and r.get("ok"):
                lines.append(f"✅ {r['subgoal'][:80]}: "
                             f"{str(r.get('answer', ''))[:300]}")
            else:
                lines.append(f"❌ {r['subgoal'][:80]}: "
                             f"error {r.get('error', '?')}")
        lines.append(f"(wall {parallel_out.get('wall_s')}s, "
                     f"{parallel_out.get('success')}/{parallel_out.get('workers')} sukses)")
        return "\n".join(lines)
