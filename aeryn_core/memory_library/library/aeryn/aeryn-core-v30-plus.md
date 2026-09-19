---
id: aeryn-core-v30-plus
topic: aeryn
tags: [aeryn, v30, v32, daemon, heuristic, social-detection, nous, navbar]
signal: high
created: 2026-08-25
updated: 2026-08-25
summary: Aeryn-Core V30-V32 (session 20260824_111023_6c0f07): schema dinamis V30.3 (hint path/URL dari goal), deteksi social vs knowledge query via heuristic bersih (V32), NOUS model paling natural untuk sapaan (4/5).
---

## Status V30+ (per 2026-08-25 pagi)
- Core: `aeryn-v28` binary, gate_mode 3, daemon port 3010 (PM2)
- **V30.3**: schema dinamis — hint path/URL diekstrak dari goal user
- **V32**: deteksi social/knowledge disederhanakan pakai heuristic bersih
  (pattern list panjang diganti) — tujuannya: pertanyaan sosial ("halo",
  "kamu siapa") TIDAK memicu tool calls; knowledge umum juga tanpa tools
- Model: NOUS paling natural buat sapaan (test 4/5); masalah tersisa:
  false-positive tool calls untuk pengetahuan umum

## Pelajaran lintas-sesi
1. **429 fallback pattern** (terbukti di entity_extractor.py):
   rotate model → terakhir regex/heuristic fallback → JANGAN raise.
   Sub-agen redesign kemarin mati di tengah karena raise langsung.
2. Session search keyword-match sering mengangkat snapshot LAMA (V26);
   ambil konteks terkini selalu via state.db ORDER BY timestamp DESC.
