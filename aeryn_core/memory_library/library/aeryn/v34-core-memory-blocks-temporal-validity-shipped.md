---
id: v34-core-memory-blocks-temporal-validity-shipped
topic: aeryn
tags: [aeryn,v34,core-memory,letta,graphiti,temporal]
signal: high
created: 2026-08-25
updated: 2026-08-25
summary: v34: core memory blocks + temporal validity shipped
---

# v34: core memory blocks + temporal validity shipped

V34 COMPLETE (pola dari riset Letta/MemGPT + Graphiti). AERYN SIDE: (1) aeryn_core/core_memory.py - blok human/context char-limited selalu di-inject ke system prompt (RAM analogy), tool core_memory_edit utk self-management (replace/append), seed profil Sen+proyek. (2) Endpoint /agent/remember AKHIRNYA ADA - sebelumnya dipanggil discord_gateway tapi 404 diam-diam tertelan try/except. (3) Klasifikasi baru: perintah 'ingat ini:/catat:' bukan social query - bug ketemu di smoke live. Live E2E: Aeryn ingat fakta lintas sesi DAN menambah fakta baru mandiri via core_memory_edit. HERMES SIDE: memory_library.py supersede <old> <new> - entry lama dapat superseded_by frontmatter, signal low, score x0.25, tanda SUDAH DIGANTIKAN di hasil search; entry aeryn-core lama sudah ditandai digantikan v30-plus. Tests 213->221 green. Fase 3 event-bus tetap ditunda.
