# Aeryn — Arah Pengembangan dari JiuwenSwarm & Utopia (Roadmap v3)

> Disusun: 2026-09-05
> Status: desain/roadmap (belum implementasi)
> Sumber: `openJiuwen-ai/jiuwenswarm`, `deeplethe/utopia` (dipelajari & dianalisa)

---

## Ringkasan

Dua repo ini bukan sekadar "skill" — keduanya adalah **arsitektur yang mengisi gap
nyata di Aeryn**. Disepakati: tulis sebagai ROADMAP desain dulu, bukan langsung kode.

| Repo | Gap Aeryn yang diisi | Arah |
|------|---------------------|------|
| **Utopia** (Rust+Postgres) | Memory layer masih flat SQLite + hash embed | **Bitemporal knowledge graph + ontology + conflict detection** |
| **JiuwenSwarm** (Python) | Multi-agent masih supervisor+handoff sederhana | **Swarmflow + skill self-evolution + auto harness** |

---

## Bagian 1 — Utopia → Memory Layer Aeryn

### Konsep inti yang layak diadopsi

Utopia = "enterprise world model" di satu binary Rust + satu Postgres. Bukan
vector store biasa, tapi **bitemporal knowledge graph** dengan ontology di lapisan
dasar. Konsep yang relevan untuk `aeryn_core/memory/`:

1. **Bitemporal fact** — setiap fakta menyimpan **2 timeline**:
   - *valid time*: kapan fakta itu benar di dunia nyata
   - *tx time*: kapan sistem mulai percaya fakta itu
   Mengoreksi fakta = menutup versi lama + link ke versi baru (bukan overwrite).
   → Aeryn sekarang `memories.db` flat, tidak punya sejarah perubahan pengetahuan.

2. **Ontology-driven reasoning** — aksioma ontology dikompilasi jadi aturan
   (transitivity, symmetry, inverse, hierarchy) → derivasi fakta baru via
   forward chaining. Derived fact ditandai & menyimpan provenance.
   → Aeryn reasoning punya `graph_memory.py` tapi belum ontology.

3. **Conflict detection 3 jenis** — (a) fakta baru clash fakta lama, (b) data
   yang melanggar aksioma (self-loop, cycle, cardinality), (c) ontology sendiri
   kontradiktif. Masing-masing punya pilihan resolusi eksplisit.
   → Aeryn belum punya deteksi konflik pengetahuan.

4. **Entity resolution 3 stage** — exact name/alias → embedding similarity →
   model call untuk pasangan ragu. Setiap merge bisa di-undo.
   → Aeryn `entity_resolution.py` sudah ada, tapi belum 3-stage berjenjang.

5. **Decision ledger append-only** — setiap konfirmasi/reject/merge/rebuild
   dicatat (who/when/what). Record outlives objeknya.
   → Aeryn `audit_trail.db` ada, tapi belum append-only penuh.

### Desain target untuk Aeryn

```
aeryn_core/memory/
├── bitemporal_graph.py    (NEW)  — valid_time + tx_time per fakta
├── ontology.py            (NEW)  — aksioma → rule → forward chaining
├── conflict_detector.py   (NEW)  — 3 jenis konflik + resolusi
├── entity_resolution.py   (UPGRADE) — 3-stage berjenjang + undo
└── decision_ledger.py     (NEW)  — append-only, outlive objek
```

Backend: Rust engine `aeryn-engine` (performance) + Postgres (sudah PG-backed
di Gap 3). Vektor di pgvector kalau tersedia; fallback hash embedder (sudah ada).

### Peta implementasi

1. **Bitemporal fact store** — schema Postgres `facts(valid_from, valid_to,
   tx_from, tx_to, fact, source)`. Ini pondasi.
2. **Ontology + reasoning** — subclass tipe entitas (Person/Place/Thing),
   relasi (isa, partOf), aturan transitivity.
3. **Conflict detection** — hook di write path.
4. **Entity resolution upgrade** — tambah stage embedding + model.

---

## Bagian 2 — JiuwenSwarm → Orchestration & Self-improvement

### Konsep inti yang layak diadopsi

JiuwenSwarm = sistem multi-agent swarm yang "benar-benar bekerja". Relevan untuk
`aeryn_core/multi_agent/` dan `aeryn_core/adaptive/`:

1. **Swarmflow** — deterministic multi-stage workflow via Python script: Leader
   dekomposisi task → hand-off antar stage agent. Dukungan **HITL** (`human` /
   `human_session`), **team token budget**, monitoring run-tree.
   → Aeryn `multi_agent.py` masih supervisi + handoff sederhana, belum stage workflow.

2. **Skill Self-Evolution** — deteksi sinyal error & ketidakpuasan user → optimasi
   definisi skill secara otomatis. (`symphony/evolution/`: aggregate, models,
   session_consumer, store).
   → Aeryn `skill_crystallization.py` ada, tapi belum loop evolusi otomatis.

3. **Auto Harness** — evaluation drive optimasi harness itu sendiri secara
   end-to-end, belajar dari praktik tanpa training model weight.
   → Aeryn `evaluation/harness.py` (Fase 6) mengukur, tapi belum menutup loop
   untuk *memperbaiki* harness.

4. **Leader/Teammate assembly declarative** — kemampuan anggota = kumpulan spec
   deklaratif (`RailSpec`/`ToolSpec`/`SubAgentSpec`) di-resolve lewat provider
   factory, bukan hardcoded. Manifest serializable untuk restore/distributed.
   → Aeryn 5 divisi masih hardcoded; belum declarative assembly + seed rebuild.

5. **Tool permission & whitelist** — setiap langkah butuh approval, file access
   via whitelist, operasi sensitif di-intercept.
   → Aeryn sudah punya guardrail (Fase 5.1) — ini konfirmasi arah yang benar.

### Desain target untuk Aeryn

```
aeryn_core/multi_agent/
├── swarmflow.py            (NEW)  — stage workflow + HITL + token budget
├── declarative_assembly.py (NEW)  — TeamSpec/RailSpec/ToolSpec → provider factory
└── orchestrator.py         (UPGRADE) — Leader dekomposisi + dynamic team

aeryn_core/adaptive/
├── skill_evolution.py      (NEW)  — error signal → optimize skill definition
├── harness_loop.py         (NEW)  — evaluation feedback → improve harness
└── __init__.py             (UPGRADE) — wire loop

aeryn_core/evaluation/
└── harness.py              (UPGRADE) — close the loop (measure → improve)
```

### Peta implementasi

1. **Swarmflow** — stage workflow deterministic + HITL + token budget.
2. **Skill evolution** — detect error/user dissatisfaction → patch skill.
3. **Auto harness** — evaluation feedback loop untuk tune harness.
4. **Declarative assembly** — ganti 5 divisi hardcoded jadi spec-driven.

---

## Prioritas (urut berdampak)

1. **Bitemporal graph** (Utopia #1) — paling fundamental, upgrade memory paling dalam.
2. **Swarmflow** (JiuwenSwarm #1) — orchestration langsung lebih kuat.
3. **Skill evolution** (JiuwenSwarm #2) — self-improvement nyata.
4. **Conflict detection + entity resolution** (Utopia #3-4).
5. **Auto harness** (JiuwenSwarm #3).

---

## Catatan penting

- **Utopia** pakai Rust+Postgres = cocok dengan arsitektur Aeryn (Rust engine +
  PG sudah terpasang). Tapi butuh pgvector + Tantivy untuk full-text/vektor; di
  proot saat ini terbatas (lihat STRESS_REPORT.md — spawn & GPU issues).
- **JiuwenSwarm** bergantung ke framework `openjiuwen` (bukan dependency ringan).
  Yang diadopsi adalah **pola/desainnya**, bukan dependensi-nya.
- Ini ROADMAP — **belum implementasi**. Menunggu keputusan kamu untuk mulai
  eksekusi fase pertama (disarankan: Bitemporal graph).

---

## Status keseluruhan

| Lapisan | Sekarang | Target (roadmap ini) |
|---------|----------|---------------------|
| Memory | flat SQLite + hash embed | bitemporal graph + ontology + conflict |
| Multi-agent | supervisor + handoff | swarmflow + HITL + token budget |
| Self-upgrade | skill_crystallization statis | skill evolution + auto harness |
| Knowledge integrity | audit_trail DB | decision ledger append-only |