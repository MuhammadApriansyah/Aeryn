"""V29.1 — SemanticRecall: recall episodik berbasis embedding lokal.

Mengganti/melengkapi keyword-match EpisodicMemory.recall dengan skor
kemiripan semantik TF-IDF cosine — murni stdlib, tanpa dependensi eksternal,
tapi memahami kesamaan makna lewat distribusi kata lintas episode.

Fallback otomatis: kalau korpus terlalu kecil (< MIN_CORPUS), perilaku
keyword-overlap lama tetap dipakai. Hybrid: skor akhir = gabungan keduanya.
"""
import json
import math
import os
import re
import time

EPISODE_DIR = os.path.expanduser(
    "~/aeryn-core-agent/Personalisasi/Database/episodes")
MIN_CORPUS = 5          # di bawah ini pakai keyword-match saja
STOPWORDS = frozenset(
    "yang untuk dengan dari ke di dan atau the a an of to in on for and or "
    "sebutkan jalankan kerjakan lakukan berurutan satu tool per giliran "
    "jawab ringkas hasilnya langkah coba".split())


def _tokens(text: str) -> list:
    return [w for w in re.findall(r"[a-z0-9_.-]+", text.lower())
            if len(w) > 2 and w not in STOPWORDS]


class SemanticRecall:
    """TF-IDF + cosine over episode goals. Rebuild index dari JSONL on-demand
    (korpus kecil → rebuild murah; threshold EPISODE_REBUILD_IF > baris)."""

    def __init__(self, episode_path: str):
        self.path = episode_path
        self._index_size = -1
        self._tfidf = {}       # token -> {ep_idx: tf}
        self._idf = {}
        self._goals_tokens = []  # list[list[token]]
        self._episodes = []

    # ---- indexing -------------------------------------------------
    def _maybe_rebuild(self):
        try:
            n_lines = sum(1 for _ in open(self.path, encoding="utf-8"))
        except OSError:
            return False
        if n_lines == self._index_size:
            return bool(self._episodes)
        eps, docs = [], []
        try:
            with open(self.path, encoding="utf-8") as f:
                for line in f:
                    try:
                        ep = json.loads(line)
                    except ValueError:
                        continue
                    eps.append(ep)
                    docs.append(_tokens(ep.get("goal", "")))
        except OSError:
            return False
        # df per token
        df = {}
        for toks in docs:
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        n_docs = max(len(docs), 1)
        idf = {t: math.log((n_docs + 1) / (c + 1)) + 1.0
               for t, c in df.items()}
        tfidf_docs = []
        for toks in docs:
            vec = {}
            for t in toks:
                vec[t] = vec.get(t, 0) + idf.get(t, 1.0)
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            tfidf_docs.append({t: v / norm for t, v in vec.items()})
        self._episodes, self._goals_tokens = eps, docs
        self._idf, self._tfidf = idf, tfidf_docs
        self._index_size = n_lines
        return True

    def _query_vec(self, goal: str) -> dict:
        toks = _tokens(goal)
        vec = {}
        for t in toks:
            if t in self._idf:
                vec[t] = vec.get(t, 0) + self._idf[t]
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    @staticmethod
    def _cosine(a: dict, b: dict) -> float:
        if len(a) > len(b):
            a, b = b, a
        return sum(v * b.get(t, 0.0) for t, v in a.items())

    def score_all(self, goal: str, now: float | None = None):
        """Return [(score_hybrid, episode)] untuk semua episode relevan."""
        now = now or time.time()
        indexed = self._maybe_rebuild()
        want_set = set(_tokens(goal))
        scored = []
        qv = self._query_vec(goal) if indexed and \
            len(self._episodes) >= MIN_CORPUS else None
        for i, ep in enumerate(self._episodes):
            overlap = len(want_set & set(ep.get("goal_tokens", [])))
            age_h = (now - ep.get("ts", now)) / 3600
            decay = 1 / (1 + age_h / 24)
            kw_score = overlap * decay
            if qv is not None:
                sem = self._cosine(qv, self._tfidf[i]) * decay
                # hybrid: semantic dominan, keyword sebagai booster
                score = 0.7 * sem + 0.3 * (kw_score / (1 + kw_score))
                if sem <= 0 and overlap == 0:
                    continue
            else:
                score = kw_score
                if overlap == 0:
                    continue
            scored.append((score, ep))
        scored.sort(key=lambda x: -x[0])
        return scored

    def recall(self, goal: str, k: int = 3) -> list:
        return [ep for _, ep in self.score_all(goal)[:k]]
