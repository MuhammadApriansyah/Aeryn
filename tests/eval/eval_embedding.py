#!/usr/bin/env python3
"""Gap 2 evaluasi — hit rate + MRR: dense (hash embedder) vs keyword baseline.

Mengukur apakah dense embedding search lebih presisi daripada keyword search
untuk query parafrase (makna sama, kata beda).
"""

import sys
sys.path.insert(0, '/home/sen/aeryn-core-agent')

from aeryn_core.memory.embedding import get_embedding_index, _HashEmbedder
from aeryn_core.memory.recall import get_memory_recall

# Gold memory set: facts keyed by content
GOLD_FACTS = [
    ("kopi", "Sen suka kopi hitam tanpa gula"),
    ("proyek", "Aeryn adalah proyek personal AI assistant"),
    ("lokasi", "Sen tinggal di Jakarta"),
    ("makanan", "Sen suka makan nasi goreng"),
    ("teknologi", "Aeryn dibangun dengan Rust dan Python"),
    ("musik", "Sen suka musik jazz"),
]

# Query -> expected fact key (paraphrase, bukan keyword persis)
QUERIES = [
    ("minuman kesukaan apa sih", "kopi"),
    ("dia kerja di project apa", "proyek"),
    ("di mana alamat rumahnya", "lokasi"),
    ("makanan favorit", "makanan"),
    ("stack dari software itu", "teknologi"),
    ("genre lagu yang disuka", "musik"),
]


def build_index():
    """Index gold facts into embedding index."""
    idx = get_embedding_index()
    for i, (key, content) in enumerate(GOLD_FACTS):
        idx.add(f"gold_{i}", content, source="gold")
    return idx


def evaluate_dense(index):
    """Evaluate dense search hit rate + MRR."""
    hits = 0
    rr_sum = 0.0
    for query, expected_key in QUERIES:
        results = index.search(query, k=5)
        found = False
        for rank, r in enumerate(results, 1):
            # check if any result content matches expected fact
            if expected_key in r["content"].lower() or any(
                expected_key == k for k, c in GOLD_FACTS if c == r["content"]
            ):
                hits += 1
                rr_sum += 1.0 / rank
                found = True
                break
        if not found:
            # check if top-1 content is the right one by key
            pass
    mrr = rr_sum / len(QUERIES)
    hit_rate = hits / len(QUERIES)
    return hit_rate, mrr


def evaluate_keyword():
    """Evaluate keyword search (baseline) hit rate + MRR."""
    # Simulate: keyword matching = does any GOLD fact share a token with query?
    hits = 0
    rr_sum = 0.0
    for query, expected_key in QUERIES:
        # keyword approach: token overlap between query and fact content
        query_tokens = set(query.lower().split())
        ranked = []
        for key, content in GOLD_FACTS:
            content_tokens = set(content.lower().split())
            overlap = len(query_tokens & content_tokens)
            ranked.append((overlap, key, content))
        ranked.sort(key=lambda x: -x[0])
        # hit if expected at rank 1
        if ranked[0][1] == expected_key:
            hits += 1
        for rank, (score, key, content) in enumerate(ranked, 1):
            if key == expected_key:
                rr_sum += 1.0 / rank
                break
    return hits / len(QUERIES), rr_sum / len(QUERIES)


def main():
    print("=" * 70)
    print("GAP 2 EVALUATION — dense vs keyword recall")
    print("=" * 70)
    print()

    # Build index
    index = build_index()
    print(f"Index: {index.stats()}")
    print()

    dense_hr, dense_mrr = evaluate_dense(index)
    kw_hr, kw_mrr = evaluate_keyword()

    print(f"{'Metric':30} {'Dense (hash)':>15} {'Keyword':>15}")
    print("-" * 60)
    print(f"{'Hit rate@5':30} {dense_hr*100:>14.1f}% {kw_hr*100:>14.1f}%")
    print(f"{'MRR':30} {dense_mrr:>15.3f} {kw_mrr:>15.3f}")
    print()

    # Show per-query dense ranking
    print("Per-query dense ranking (top-3):")
    for query, expected_key in QUERIES:
        results = index.search(query, k=3)
        top = [r["content"][:35] for r in results]
        print(f"  '{query}' -> expected '{expected_key}'")
        for r in results:
            mark = "✓" if expected_key in r["content"].lower() else " "
            print(f"    {mark} {r['score']:.3f} {r['content'][:40]}")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()