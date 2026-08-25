"""V30.1 — MemoryConsolidation: episode lama diringkas jadi knowledge atoms.

Setiap N episode baru (CONSOLIDATE_EVERY), episode yang lebih lama dari
MIN_AGE_H diringkas jadi "knowledge atom": pola goal→hasil yang berulang,
pelajaran umum, tool track record. Atom disimpan terpisah (atoms.jsonl) dan
diinject ke system prompt sebagai pengetahuan inti — episode mentah boleh
diprune nanti tanpa kehilangan kebijaksanaan.

Heuristic-first: konsolidasi deterministik tanpa LLM (pola Counter atas
token/pelajaran/tool). LLM opsional untuk ringkasan naratif di masa depan.
"""
import json
import os
import time
from collections import Counter

EPISODE_DIR = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/Database/episodes")
ATOM_DIR = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/Database/atoms")

CONSOLIDATE_EVERY = 50   # jalankan tiap 50 episode baru
MIN_AGE_H = 24.0         # hanya episode > 24 jam yang boleh dikonsolidasi


class MemoryConsolidator:
    def __init__(self, episode_dir: str = None, atom_dir: str = None):
        self.ep_dir = episode_dir or EPISODE_DIR
        self.atom_dir = atom_dir or ATOM_DIR
        os.makedirs(self.atom_dir, exist_ok=True)
        self.atom_path = os.path.join(self.atom_dir, "atoms.jsonl")
        # cursor: jumlah episode yang sudah diproses
        self.cursor_path = os.path.join(self.atom_dir, "cursor.txt")

    # ---- io --------------------------------------------------------
    def _read_cursor(self) -> int:
        try:
            return int(open(self.cursor_path).read().strip())
        except (OSError, ValueError):
            return 0

    def _write_cursor(self, n: int):
        with open(self.cursor_path, "w") as f:
            f.write(str(n))

    def _load_episodes(self) -> list:
        eps = []
        try:
            with open(os.path.join(self.ep_dir, "episodes.jsonl"),
                      encoding="utf-8") as f:
                for line in f:
                    try:
                        eps.append(json.loads(line))
                    except ValueError:
                        continue
        except OSError:
            pass
        return eps

    def load_atoms(self, k: int = 10) -> list:
        """Knowledge atoms terakhir (untuk injeksi system prompt)."""
        if not os.path.exists(self.atom_path):
            return []
        atoms = []
        with open(self.atom_path, encoding="utf-8") as f:
            for line in f:
                try:
                    atoms.append(json.loads(line))
                except ValueError:
                    continue
        return atoms[-k:]

    # ---- consolidation ----------------------------------------------
    def should_consolidate(self) -> bool:
        total = len(self._load_episodes())
        return total - self._read_cursor() >= CONSOLIDATE_EVERY

    def consolidate(self, force: bool = False) -> dict:
        """Ringkas episode tua jadi atom. Return stats proses."""
        eps = self._load_episodes()
        cursor = self._read_cursor()
        if not force and len(eps) - cursor < CONSOLIDATE_EVERY:
            return {"consolidated": False,
                    "reason": f"hanya {len(eps)-cursor} episode baru "
                              f"(butuh {CONSOLIDATE_EVERY})"}
        now = time.time()
        old = [e for e in eps[:cursor + CONSOLIDATE_EVERY]
               if (now - e.get("ts", now)) / 3600 > MIN_AGE_H]
        if not old:
            self._write_cursor(min(len(eps), cursor + CONSOLIDATE_EVERY))
            return {"consolidated": False, "reason": "tidak ada episode cukup tua"}

        atom = {
            "ts": now,
            "window": {"from": old[0].get("ts"), "to": old[-1].get("ts")},
            "episodes_summarized": len(old),
            # pola paling sering
            "common_goals": self._top_goal_patterns(old),
            "tool_track": dict(Counter(
                t for e in old for t in e.get("tools", [])).most_common(5)),
            "success_rate": round(
                sum(1 for e in old if e.get("ok")) / max(len(old), 1), 2),
            "lessons": self._top_lessons(old),
            "failure_modes": self._failure_modes(old),
        }
        with open(self.atom_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(atom, ensure_ascii=False) + "\n")
        processed = min(len(eps), cursor + CONSOLIDATE_EVERY)
        self._write_cursor(processed)
        return {"consolidated": True, "atom_ts": now,
                "episodes_summarized": len(old), "cursor": processed}

    @staticmethod
    def _top_goal_patterns(eps: list, k: int = 3) -> list:
        """Kata paling sering muncul di goal — indikator domain kerja."""
        from aeryn_core.reflection import _tokens
        cnt = Counter(t for e in eps for t in _tokens(e.get("goal", "")))
        return [f"{w}×{c}" for w, c in cnt.most_common(k)]

    @staticmethod
    def _top_lessons(eps: list, k: int = 5) -> list:
        return [l for l, _ in Counter(
            lesson for e in eps for lesson in e.get("lessons", [])
        ).most_common(k)]

    @staticmethod
    def _failure_modes(eps: list) -> list:
        fails = [e for e in eps if not e.get("ok")]
        modes = Counter(
            (e.get("error") or "")[:60] for e in fails if e.get("error"))
        return [f"{m} ×{c}" for m, c in modes.most_common(3)]
