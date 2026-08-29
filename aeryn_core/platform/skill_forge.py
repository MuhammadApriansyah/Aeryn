"""V31.1 — SkillForge: distilasi episode sukses menjadi skill terstruktur.

Filosofi (meniru sistem skill Hermes): episode yang BERHASIL, EFISIEN, dan
BERULANG didistil jadi skill — resep {trigger, langkah, tool sequence,
jebakan} yang bisa dipakai planner tanpa LLM. Episode tunggal TIDAK cukup:
skill lahir dari pola ≥ MIN_OCCURRENCES episode serupa.

Skill disimpan di skills.jsonl (append-only). Struktur atom:
{
  "id": "fs_read_toml_versi",
  "trigger_tokens": [...],        # token pembeda goal
  "trigger_regex": "...",          # opsional pola kuat
  "steps": [{"desc","tool_hint"}],
  "tools": [...],
  "success_rate": 1.0,
  "occurrences": N,
  "pitfalls": [...],               # pelajaran dari episode gagal serupa
  "ts": ...
}
"""
import json
import os
import re
import time
from collections import Counter

EPISODE_DIR = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/Database/episodes")
SKILL_DIR = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/Database/skills")

MIN_OCCURRENCES = 3      # episode serupa minimum sebelum jadi skill
MIN_SUCCESS_RATE = 0.6   # rata-rata sukses kelompok


def _tokens(text: str) -> set:
    stop = frozenset(
        "yang untuk dengan dari ke di dan atau the a an of to in on for and or "
        "sebutkan jalankan kerjakan lakukan berurutan satu tool per giliran "
        "jawab ringkas hasilnya langkah coba".split())
    return {w for w in re.findall(r"[a-z0-9_.-]+", text.lower())
            if len(w) > 2 and w not in stop}


class SkillForge:
    def __init__(self, episode_dir: str = None, skill_dir: str = None):
        self.ep_dir = episode_dir or EPISODE_DIR
        self.skill_dir = skill_dir or SKILL_DIR
        os.makedirs(self.skill_dir, exist_ok=True)
        self.skill_path = os.path.join(self.skill_dir, "skills.jsonl")

    # ---- io ---------------------------------------------------------
    def load_skills(self) -> list:
        if not os.path.exists(self.skill_path):
            return []
        skills = []
        with open(self.skill_path, encoding="utf-8") as f:
            for line in f:
                try:
                    skills.append(json.loads(line))
                except ValueError:
                    continue
        return skills

    def _save_skill(self, skill: dict):
        with open(self.skill_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(skill, ensure_ascii=False) + "\n")

    def has_skill_for(self, key: str) -> bool:
        """key = fingerprint kelompok (mis. 'fs_read+versi')."""
        return any(s.get("fingerprint") == key for s in self.load_skills())

    # ---- clustering --------------------------------------------------
    @staticmethod
    def _fingerprint(ep: dict) -> str:
        """Kelompokkan episode by primary tool + kata benda dominan.
        Contoh: 'fs_read+versi', 'web_search+cari'."""
        tools = ep.get("tools") or ["none"]
        primary = tools[0] if tools else "none"
        toks = sorted(_tokens(ep.get("goal", "")))
        noun = next((t for t in reversed(toks)
                     if not t.startswith(("http", "/"))), "umum")
        return f"{primary}+{noun}"

    def _load_episodes(self) -> list:
        path = os.path.join(self.ep_dir, "episodes.jsonl")
        eps = []
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    try:
                        eps.append(json.loads(line))
                    except ValueError:
                        continue
        except OSError:
            from aeryn_core.utils.logger import log_exception
            log_exception(e, context=f"{__name__}")
            pass
        return eps

    # ---- forging ------------------------------------------------------
    def forge_from_episodes(self) -> list:
        """Pindai semua episode, kelompokkan per fingerprint, buat skill
        untuk kelompok yang layak. Return daftar skill baru."""
        eps = self._load_episodes()
        groups = {}
        for ep in eps:
            fp = self._fingerprint(ep)
            groups.setdefault(fp, []).append(ep)

        forged = []
        for fp, members in groups.items():
            if len(members) < MIN_OCCURRENCES or self.has_skill_for(fp):
                continue
            oks = [e for e in members if e.get("ok")]
            rate = len(oks) / len(members)
            if rate < MIN_SUCCESS_RATE:
                continue
            skill = self._distill(fp, members, oks, rate)
            if skill:
                self._save_skill(skill)
                forged.append(skill)
        return forged

    def _distill(self, fp: str, members: list, oks: list, rate: float) -> dict:
        """Ringkas kelompok episode → satu skill resep."""
        # langkah: urutan tool paling umum di episode SUKSES
        seq_counter = Counter(tuple(e.get("tools") or []) for e in oks)
        common_seq, _ = seq_counter.most_common(1)[0]
        steps = [{"step": i, "tool_hint": t, "done_when": "langkah selesai"}
                 for i, t in enumerate(common_seq)]
        # trigger: token yang muncul di ≥60% goal anggota
        tok_count = Counter(
            t for e in members for t in _tokens(e.get("goal", "")))
        threshold = max(len(members) * 0.6, 1)
        triggers = sorted(t for t, c in tok_count.items() if c >= threshold)
        # pitfalls: lessons dari yang GAGAL
        pitfalls = []
        for e in members:
            if not e.get("ok"):
                for l in e.get("lessons", []):
                    if l not in pitfalls:
                        pitfalls.append(l)
                if e.get("error") and len(pitfalls) < 4:
                    pitfalls.append(f"error umum: {e['error'][:80]}")
        sample_goal = oks[0].get("goal", "") if oks else ""
        return {
            "id": fp.replace("+", "_").replace("/", "_"),
            "fingerprint": fp,
            "trigger_tokens": triggers[:8],
            "steps": steps,
            "tools": list(common_seq),
            "success_rate": round(rate, 2),
            "occurrences": len(members),
            "sample_goal": sample_goal[:120],
            "pitfalls": pitfalls[:4],
            "ts": time.time(),
        }

    # ---- matching ------------------------------------------------------
    def match(self, goal: str, min_overlap: int = 2) -> dict | None:
        """Cocokkan goal dgn trigger skill. Return skill terbaik atau None.
        Deterministik, 0 LLM — dipanggil planner sebelum bikin plan baru."""
        gt = _tokens(goal)
        best, best_score = None, 0
        for s in self.load_skills():
            overlap = len(gt & set(s.get("trigger_tokens", [])))
            if overlap >= min_overlap and overlap > best_score:
                best, best_score = s, overlap
        return best

    @staticmethod
    def plan_from_skill(skill: dict) -> dict:
        """Bentuk plan siap-pakai dari skill (source='skill')."""
        subs = [{"step": st["step"], "desc": f"[skill] langkah {st['step']+1}",
                 "tool_hint": st["tool_hint"], "done_when": st["done_when"]}
                for st in skill.get("steps", [])]
        pitfall_note = ("; ".join(skill.get("pitfalls", [])[:2])
                        if skill.get("pitfalls") else "")
        return {"goal": skill.get("sample_goal", ""),
                "subgoals": subs,
                "status": ["pending"] * len(subs),
                "source": "skill",
                "skill_id": skill["id"],
                "pitfalls": pitfall_note}
