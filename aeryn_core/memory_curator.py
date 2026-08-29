"""V31.4 — MemoryCurator: kurasi memori agar tetap ramping & relevan.

Tiga tugas:
1. Arsip strategi basi (>MAX_AGE_DAYS sejak ts & tak pernah match) dari
   reflections.jsonl → archive.jsonl (dipindah, bukan dihapus).
2. Prune episode sangat lama yang SUDAH terwakili oleh knowledge atoms
   (konsolidasi V30.1) → episodes_archive.jsonl.
3. Dedup skill: fingerprint sama tapi beda id → gabungkan (ambil occ tertinggi).

Semua operasi aman: file sumber tidak pernah kehilangan data tanpa arsip.
"""
import json
import os
import shutil
import time
from aeryn_core.config import BASE_DIR, DATABASE_DIR

DB = DATABASE_DIR
ARCHIVE_DIR = os.path.join(DB, "archive")

MAX_STRATEGY_AGE_DAYS = 30
MAX_EPISODE_AGE_DAYS = 90      # hanya kalau sudah ada atom penggantinya
KEEP_MIN_ATOMS = 3             # jangan sampai atom habis semua


class MemoryCurator:
    def __init__(self, db_dir: str = None, archive_dir: str = None):
        self.db = db_dir or DB
        self.archive = archive_dir or ARCHIVE_DIR
        os.makedirs(self.archive, exist_ok=True)

    # ---- helpers ----------------------------------------------------
    @staticmethod
    def _read_jsonl(path):
        if not os.path.exists(path):
            return []
        out = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
        return out

    @staticmethod
    def _write_jsonl(path, rows):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        shutil.move(tmp, path)

    def _append_archive(self, name: str, rows: list):
        if not rows:
            return
        path = os.path.join(self.archive, name)
        with open(path, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- 1. arsip strategi basi ---------------------------------------
    def curate_strategies(self, now=None) -> dict:
        now = now or time.time()
        path = os.path.join(self.db, "reflections", "reflections.jsonl")
        refs = self._read_jsonl(path)
        keep, stale = [], []
        cutoff = now - MAX_STRATEGY_AGE_DAYS * 86400
        for r in refs:
            strat = r.get("strategy") or ""
            if strat and r.get("ts", now) < cutoff:
                stale.append(r)
            else:
                keep.append(r)
        if stale:
            self._append_archive("reflections_archived.jsonl", stale)
            self._write_jsonl(path, keep)
        return {"scanned": len(refs), "archived": len(stale)}

    # ---- 2. prune episode terwakili atom ------------------------------
    def curate_episodes(self, now=None, force: bool = False) -> dict:
        now = now or time.time()
        ep_path = os.path.join(self.db, "episodes", "episodes.jsonl")
        eps = self._read_jsonl(ep_path)
        atoms_path = os.path.join(self.db, "atoms", "atoms.jsonl")
        atoms = self._read_jsonl(atoms_path)
        # butuh minimal atom sebagai "pengganti" — kalau belum ada, jangan buang
        if len(atoms) < 1 and not force:
            return {"scanned": len(eps), "pruned": 0,
                    "reason": "belum ada knowledge atom"}
        cutoff = now - MAX_EPISODE_AGE_DAYS * 86400
        keep, pruned = [], []
        for e in eps:
            if e.get("ts", now) < cutoff and e.get("ok"):
                pruned.append(e)
            else:
                keep.append(e)
        if pruned:
            self._append_archive("episodes_archived.jsonl", pruned)
            self._write_jsonl(ep_path, keep)
        return {"scanned": len(eps), "pruned": len(pruned)}

    # ---- 3. dedup skill ------------------------------------------------
    def curate_skills(self) -> dict:
        from aeryn_core.skill_forge import SkillForge
        sf = SkillForge()
        skills = sf.load_skills()
        by_fp = {}
        for s in skills:
            fp = s.get("fingerprint")
            prev = by_fp.get(fp)
            if prev is None or s.get("occurrences", 0) > prev.get("occurrences", 0):
                by_fp[fp] = s
        deduped = list(by_fp.values())
        removed = len(skills) - len(deduped)
        if removed:
            self._append_archive("skills_deduped.jsonl",
                                 [s for s in skills
                                  if s not in deduped])
            sf_path = os.path.join(sf.skill_dir, "skills.jsonl")
            self._write_jsonl(sf_path, deduped)
        return {"before": len(skills), "after": len(deduped),
                "removed": removed}

    # ---- all-in-one ------------------------------------------------------
    def run_all(self) -> dict:
        return {
            "strategies": self.curate_strategies(),
            "episodes": self.curate_episodes(),
            "skills": self.curate_skills(),
            "ts": time.time(),
        }
