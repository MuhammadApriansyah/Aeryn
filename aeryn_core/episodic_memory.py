"""V27.4 — EpisodicMemory: jurnal pengalaman lintas-sesi untuk Aeryn.

Setiap run agentic menghasilkan episode: goal, plan, trace ringkas, hasil,
pelajaran. Sebelum run baru, episode relevan diambil by keyword overlap dan
diinject ke system prompt — Aeryn "ingat" pernah gagal/berhasil di goal serupa.

Persist: JSONL append-only di Personalisasi/Database/episodes/
(mengikuti pola persist lain aeryn-core; tanpa dependensi eksternal).
"""
import json
import os
import re
import time

EPISODE_DIR = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/Database/episodes")
MAX_INJECT = 3          # berapa episode lama diinject per run
STOPWORDS = frozenset(
    "yang untuk dengan dari ke di dan atau the a an of to in on for and or "
    "sebutkan jalankan kerjakan lakukan berurutan satu tool per giliran "
    "jawab ringkas hasilnya langkah coba".split())


def _tokens(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9_.-]+", text.lower())
            if len(w) > 2 and w not in STOPWORDS}


class EpisodicMemory:
    def __init__(self, episode_dir: str = None):
        self.dir = episode_dir or EPISODE_DIR
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, "episodes.jsonl")

    def record(self, session_id: str, goal: str, plan_source: str,
               trace: list, answer: str = None, error: str = None,
               timed_out: bool = False) -> dict:
        """Simpan episode setelah run selesai (sukses maupun gagal)."""
        tools_used = [t.get("name") for t in trace if t.get("type") == "tool"]
        errors = [t for t in trace if t.get("type") == "error"]
        # Pelajaran heuristic — murah, deterministik
        lessons = []
        if error:
            lessons.append(f"run gagal: {error[:120]}")
        if timed_out:
            lessons.append("wall-budget habis: pecah goal jadi lebih kecil")
        if any("MULTI-CALL" in str(t.get("result_digest", ""))
               for t in trace):
            lessons.append("model cenderung multi-call: ingatkan satu tool "
                           "per giliran lebih tegas")
        if not tools_used and not error:
            lessons.append("goal terjawab tanpa tool")
        ep = {
            "ts": time.time(), "session_id": session_id,
            "goal": goal[:300], "goal_tokens": sorted(_tokens(goal)),
            "plan_source": plan_source, "tools": tools_used,
            "ok": answer is not None, "error": (error or "")[:200],
            "lessons": lessons,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(ep, ensure_ascii=False) + "\n")
        return ep

    def recall(self, goal: str, k: int = MAX_INJECT) -> list:
        """Ambil k episode paling relevan (keyword overlap + recency)."""
        if not os.path.exists(self.path):
            return []
        want = _tokens(goal)
        scored = []
        now = time.time()
        try:
            with open(self.path, encoding="utf-8") as f:
                for line in f:
                    try:
                        ep = json.loads(line)
                    except ValueError:
                        continue
                    overlap = len(want & set(ep.get("goal_tokens", [])))
                    if overlap == 0:
                        continue
                    age_h = (now - ep.get("ts", now)) / 3600
                    score = overlap / (1 + age_h / 24)  # decay harian lembut
                    scored.append((score, ep))
        except OSError:
            return []
        scored.sort(key=lambda x: -x[0])
        return [ep for _, ep in scored[:k]]

    @staticmethod
    def prompt_block(episodes: list) -> str:
        """Bentuk blok injeksi system-prompt dari episode lama."""
        if not episodes:
            return ""
        lines = ["\n## Pengalaman relevan dari sesi sebelumnya"]
        for ep in episodes:
            status = "berhasil" if ep.get("ok") else "GAGAL"
            line = f"- Goal mirip: \"{ep['goal'][:90]}\" → {status}"
            if ep.get("lessons"):
                line += f" | pelajaran: {'; '.join(ep['lessons'][:2])}"
            lines.append(line)
        lines.append("Gunakan pengalaman ini agar tidak mengulang kesalahan.")
        return "\n".join(lines)
