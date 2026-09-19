# Hermes↔Aeryn Parity Tracker

> Dibuat V35 (2026-08-25). Filosofi Sen: target diketahui + resource ada =
> tidak perlu menunggu. Aeryn mengikuti evolusi Hermes secara bertahap,
> setiap langkah diuji (test suite + parity probe + smoke live).

## 🧠 CORPUS CALLOSUM ROADMAP

Empat prioritas penghubung Hermes↔Aeryn (otak kanan lab → otak kiri
produksi). Semua status: **in-progress** per hari ini (2026-08-25).

| # | Prioritas | Isi | Status |
|---|---|---|---|
| 1 | **Refleks kontinuitas** | Aeryn mempertahankan konteks & niat lintas sesi/gangguan tanpa prompt eksplisit (core memory blocks + riwayat ber-budget sebagai fondasi). | in-progress |
| 2 | **Delegasi ask_hermes** | Channel delegasi Aeryn→Hermes untuk tugas di luar kemampuan lokalnya (web tools, browser), hasil balik masuk episode memory. | in-progress |
| 3 | **Nightly gabungan** | Digest malam menyatukan refleksi Aeryn + Hermes (satu laporan kesehatan & progres gabungan, bukan dua terpisah). | in-progress |
| 4 | **Backflow** | Aliran balik otak kanan→kiri: pola terbukti di lab diformalkan jadi skill Hermes + entry library (mis. tool-graduation-pattern, differential-testing-parity-probe). | in-progress |

## ✅ Sudah setara (diadopsi)

| Fitur | Pola dari | Versi Aeryn |
|---|---|---|
| Fallback chain multi-provider + rotasi 429/5xx | Hermes model chain | V28-V33 |
| Web search (Bing scrape, decode redirect) | Hermes web tools | V33 |
| Shared memory read (library/graph/pitfalls) | Hermes library RAG | V33 |
| Observability (/metrics, episode JSONL) | Hermes telemetry | V33-Fase2 |
| Nightly reflection deterministik | Hermes reflector cron | V33-Fase2 |
| Differential testing (parity_probe) | — (ide Sen) | V34 |
| Core memory blocks (agent-editable) | Letta/MemGPT | V34 |
| Temporal validity (supersede) | Graphiti/Zep | V34 |
| NOUS OAuth agent_key fresh dari auth.json | Hermes credential pool | V34 |
| **Riwayat multi-turn ber-budget** | Hermes context mgmt | **V35** |
| **Konsolidasi memori harian → core** | Hermes reflector→MEMORY.md | **V35** |
| **fs_write sandboxed** | Hermes file tools | **V35** |
| Self-inquiry classification | Hermes routing | **V35** |

## 🎯 Antrian berikutnya (urutan prioritas)

1. **Compaction LLM untuk sesi panjang** — ringkasan deterministik saat ini
   cukup; nanti pakai LLM ringkas turn lama saat budget terlampaui
   (ala session surgery Hermes).
2. **Event bus internal** (pola OpenHands) — /metrics sudah menandai arah;
   subscriber bisa dipakai critic otomatis & alert kesehatan.
3. **Credential health check** — probe berkala semua provider di chain,
   lapor status ke nightly digest.
4. **Skill/plugin format alignment** — kalau Hermes ubah format skill,
   Aeryn ikut; tracker ini pengingatnya.
5. **Multi-platform delivery parity** — gateway Discord Aeryn belum punya
   thread/topic handling seperti Hermes WA/Discord.

## ⏸ Ditahan (tanpa konsumen)

- Session tree/fork (Fase 3 lama) — tunggu ada pemakai nyata.
- MCP SDK — berat; Spark MCP "cukup teori" per Sen.
- Sandbox eksekusi kode tipe Docker — mustahil di proot ARM64.

## Ritual wajib tiap penambahan fitur

1. Test unit baru + regression full green
2. `parity_probe.py` → ALL PARITY (DIVERGENSI = bahan perbaikan)
3. Smoke live E2E via daemon
4. CHANGELOG + komit git + handoff ke library
5. Update tracker ini
