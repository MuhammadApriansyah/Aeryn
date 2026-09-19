---
id: v34-1-parity-probe-ritual-root-cause-flaky-routi
topic: aeryn
tags: [aeryn,v34,parity-probe,differential-testing,groq]
signal: high
created: 2026-08-25
updated: 2026-08-25
summary: v34.1: parity probe ritual + root cause flaky routing
---

# v34.1: parity probe ritual + root cause flaky routing

IDE SEN diimplementasi: differential testing Hermes<->Aeryn jadi ritual permanen. scripts/parity_probe.py - 3 lapisan (direct tool layer, classification agreement, daemon E2E) + verdict DIVERGENSI/INCONCLUSIVE/ALL PARITY. Provider error (429/5xx) = INCONCLUSIVE bukan divergensi. PROBE LANGSUNG BUKTIKAN NILAI: run pertama ketemu divergensi nyata - 'ingat ini:' kadang dirouting ke memory_search/pitfall_search/web_search secara acak. ROOT CAUSE: PM2 env cuma punya GROQ_API_KEY (bukan NOUS) -> chain jatuh ke model kecil gpt-oss-20b yang kerap abaikan instruksi prompt. FIX: memory-write enforcement DI KODE (tool lain ditolak dengan retry message saat perintah ingat-ini), pola sama dgn single-call guard. Hasil: 3x berturut ALL PARITY. Tests 221 green.
