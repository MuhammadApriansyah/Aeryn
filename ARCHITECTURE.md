# Aeryn — Architecture: Layers & Terminology

> Analisa keseluruhan Aeryn sebagai **Self-Hosted Personal AI System** —
> Personal AI Assistant + Autonomous Agents + Persistent Memory + Workflow
> Orchestration, dengan **kapabilitas SaaS-level** di dalam (bukan SaaS
> business model — lihat Aeryn_Identity.md, North Star). Dokumen ini adalah
> peta layer + terminologi resmi untuk roadmap pengembangan.

## Peta Layer (10 Layer)

```
┌──────────────────────────────────────────────────────────────┐
│ L9 OBSERVABILITY — tracer (Span/Trace), /traces, watchdog    │
│ L8 SAFETY — safety_engine, guardrails, sandbox, owasp, soc2  │
│ L7 ORCHESTRATION — 5 divisions, crew_orchestrator, workflow  │
│ L6 PLATFORM — MCP 15 tools, gateway, briefing, reminders,    │
│              profile_router, queue, ledger_tools             │
│ L5 AGENT — trust_layer, goal_store, agent_loop               │
│ L4 MEMORY — fact_store (bitemporal), vault (5 layer),        │
│            embedding, semantic, graph (nerve), decay         │
│ L3 REASONING — proactive, planner, long_horizon, reflection  │
│ L2 API — FastAPI :3010 (chat/ledger/briefing/cron/obs)       │
│ L1 ENGINE (Rust) — aeryn_native + aeryn_engine (.so)         │
│ L0 SERVICE (runit) — api/worker/gateway/watchdog + infra     │
└──────────────────────────────────────────────────────────────┘
```

### L0 — SERVICE (runit / runsvdir)
Kelompokan resmi (lihat `SERVICES.md`):
- **Aeryn Core (4)**: `aeryn-api` (FastAPI :3010), `aeryn-worker` (queue poll_due → execute), `aeryn-gateway` (Discord ws+READY → allowlist → AgentLoop), `aeryn-watchdog` (monitor interval 60s)
- **Infrastruktur (5)**: `postgres` (facts/goals/cron_jobs), `redis` (ZSET + cache), `sshd`, `ssh-agent`, `dbus` (termux-api)
- Pola: `exec sh -c '<cmd> | stdbuf -oL tee -a log'`; orphan pattern terdokumentasi

### L1 — ENGINE (Rust native — prioritas utama)
- **`aeryn_native.so`** (pyo3, dari crate terpisah): `PyUnifiedCognitiveSystem`, `AccountingLedgerEngine`, `TransactionEntry`, `CharacterProgression`, `MagicSystemEngine`
- **`aeryn_engine.so`** (pyo3 0.23, dari `aeryn-engine/`): ledger classes + C-API (`cosine_similarity`, `euclidean_distance`, `hash_text`, `word_count`, `truncate_text`, `find_top_k`, `free_string`)
- Terukir: ledger 1.000 entries = **0,7ms** (vs Python ~70x lebih lambat)

### L2 — API (Python FastAPI :3010)
Endpoint groups: `/v1/chat`, `/ledger/{balance,spend,report}`, `/briefing/{morning,preview,morning-deliver}`, `/cron/*`, `/traces`, `/goals`, `/health`

### L3 — REASONING (Python)
`proactive_engine`, `planner`, `long_horizon`, `reflection`, `emotional_intelligence`, `context_manager`, `constitutional_ai`

### L4 — MEMORY (Python driver + Rust ops)
- **fact_store**: bitemporal — VALID TIME (`valid_from/valid_to` = kapan benar di dunia) + TRANSACTION TIME (`tx_from/tx_to` = kapan tercatat). Versi aktif = `tx_to IS NULL`. Transaksi = EVENT nyata (entity unik per event, tidak ditimpa)
- **vault**: 5 layer — `Wiki`, `Projects`, `System`, `Daily`, `Skills`
- **embedding**: 384-dim all-MiniLM-L6-v2 via AlmaLinux proot (miss 82s / hit 9ms), cache sqlite
- **graph_memory** (nerve): adjacency + BFS/DFS/path — traverse 0,01s
- **decay + consolidation**: note>180d → valid_to, heartbeat>30d → delete, scheduler harian

### L5 — AGENT (Python)
- **trust_layer**: intent parser — note (`user_note`), reminder multi (jam N/weekday depan/besok → fact + ZSET per hint), finance (`pengeluaran/penghasilan` → ledger). `handle_promises` → what[]/failed[]
- **goal_store**: lifecycle `active → completed | cancelled`, progress 0-100
- **agent_loop**: chat → trust → recall → LM → respond

### L6 — PLATFORM (Python)
`mcp_server` (15 tools: web_search/read, memory_search, vault_read/write, social_memory_get/add, fs_read/write, set_reminder, task_create/list, safety_check, ...), `gateway_bot` (Discord), `morning_briefing` (jadwal+goals+keuangan+catatan), `reminder_delivery` (Discord DM + termux-notification), `profile_router` (multi-user sqlite), `redis_queue` (ZSET), `queue_worker`, `ledger_tools`, `watchdog`

### L7 — ORCHESTRATION (Python)
- **5 divisions**: `division_1_creative`, `division_2_psych`, `division_3_reasoning` (MCTS/FOL/Critique/Graph), `division_4_gov`, `division_5_infra`
- `crew_orchestrator`: AgentRole/Agent/Task — multi-agent role-based
- `phase_workflow`: fase multi-step

### L8 — SAFETY (Python)
`safety_engine` (24K LOC), `guardrails`, `enhanced_guardrails`, `enhanced_sandbox`, `sandbox`, `owasp_security`, `security_kernel`, `soc2_compliance`

### L9 — OBSERVABILITY (Python)
`tracer` (Span/Trace per request, middleware instrumented), `/traces` endpoint, `watchdog` (interval 60s), log file per service via tee

## Pencocokan Bahasa (Python vs Rust) — data terukur

| Bagian | Bahasa | Alasan (data) |
|--------|--------|---------------|
| Engine ledger + ops numerik (cosine/euclidean/hash/top-k) | **Rust** ✅ | 1.000 entries = 0,7ms; Python ~70x lambat |
| Scheduler daemon (cron loop) | **Rust** (roadmap) | Daemon jalan terus; Rust = overhead minimal + binary statis |
| Trust layer (intent parse per chat) | **Python** ✅ (cukup) | 1.000x = 29ms — bukan bottleneck |
| Memory driver (facts/recall/semantic/graph) | **Python** ✅ (driver) + **Rust** (ops) | recall 0,27s (gabungan 5 sumber — LM dominan); graph 0,01s |
| Embedding (proot) | **Python** (driver) — proot worker | miss 82s = torch load di proot (bukan bahasa, tapi infra); cache hit 9ms |
| API (FastAPI) | **Python** ✅ | health ~11ms; ekosistem FastAPI matang |
| Gateway (Discord ws) | **Python** ✅ (saat ini) | ws loop I/O-bound — bukan CPU-bound |
| MCP tools | **Python** ✅ | protocol layer, bukan hot path |
| Watchdog | **Python** ✅ (cukup) | interval 60s — I/O-bound trivial |

### Aturan pencocokan (roadmap)
1. **Rust** untuk: hot loop CPU-bound, daemon jalan terus, operasi numerik/kripto, binary statis (tokio async untuk MCP/CLI bila dipindah)
2. **Python** untuk: orchestration, driver I/O-bound, LLM/LM glue, ekosistem cepat
3. **Hybrid** (Rust core + Python binding) untuk: engine yang perlu eksplorasi (ledger, cognitive, game)

## Arah Pengembangan & Roadmap — selaras Aeryn_Identity.md (North Star)

> Aturan keputusan (Aeryn_Identity.md §13): *"Does this strengthen Aeryn as a
> Self-Hosted Personal AI System with autonomous capabilities, or does it push
> Aeryn toward becoming a different product?"*
> Tujuan (§3): bukan memaksimalkan jumlah fitur — tapi memaksimalkan
> **intelligence, agency, continuity, autonomy untuk SATU user**.

### Prinsip pengembangan (dari North Star)

1. **Personal scope** — satu user (Sen) + environment-nya; bukan multi-tenant
2. **Self-hosted & local-first** — Termux/Postgres/redis lokal; cloud = dependency, bukan identity
3. **User ownership** — data + infrastruktur milik user
4. **Autonomy user-governed** — permissions + approval gate di titik berisiko
5. **Capability may expand indefinitely; product identity must remain coherent**

### Roadmap capability growth (§15 — dampak terhadap agency satu user)

| # | Pengembangan | Menguatkan (axis §13) | Status |
|---|--------------|----------------------|--------|
| 1 | ✅ LEDGER Rust — keuangan pribadi | Personal Intelligence, Agency | selesai v62.19 |
| 2 | ✅ Subagent orchestration + supervisor + A2A + reflexion + cost | Autonomy, Agency, Learning | selesai v62.23 |
| 3 | ✅ Goal-derived workflow + /matter | Workflow Orchestration, Continuity | selesai v62.24 |
| 4 | **Scheduler daemon → Rust** — cron + decay digabung satu daemon ringan | Reliability, Self-Hosting, Autonomy | roadmap |
| 5 | **Embedding lokal Termux** — eliminasi proot 82s (miniLM GGUF / onnxruntime) | Self-Hosting, Privacy, Reliability | roadmap (goal tercatat via /matter) |
| 6 | **Tools sensor dunia** — location + weather + calendar_read | Environment Interaction, Personal Intelligence | roadmap |
| 7 | **Long-horizon planning wired** — planner.py + long_horizon.py → supervisor (multi-hari) | Autonomy, Reasoning, Continuity | roadmap |
| 8 | **Experience learning depth** — reflexion outcome → pitfalls + skill crystallization otomatis | Learning, Continuity | roadmap |
| 9 | **Multimodal input** — voice STT + gambar via gateway | Environment Interaction | roadmap |
| 10 | **Browser/computer interaction** — drive browser logged-in user (dengan permission) | Environment Interaction, Agency | roadmap |

### Arah yang TIDAK ditempuh (§11 — What Aeryn Is NOT)

Berikut BUKAN tujuan arsitektur Aeryn — tidak dikerjakan hanya karena umum
di platform komersial:
- ❌ SaaS sebagai business model (billing/langganan publik)
- ❌ Multi-tenant sebagai kebutuhan utama (banyak user/organisasi)
- ❌ Organization-centric / enterprise-first design
- ❌ Centralized cloud infrastructure wajib
- ❌ Marketplace-driven productization (menjual skill/agent ke pelanggan)
- ❌ Memaksimalkan jumlah external customers

Catatan: modul `billing/`, `plugin_marketplace/`, `auth/` multi-user yang ADA
di kode dipertahankan sebagai **kapabilitas internal** (bisa dipakai bila
situasi personal membutuhkan — mis. auth untuk secure remote access, §12) —
tapi tidak menentukan arah pengembangan dan tidak diprioritaskan.

### Hierarki North Star (§19 — saat ragu, pegang ini)

```
PERSONAL → AI SYSTEM → ASSISTANT → AGENCY → AGENTS → WORKFLOWS → TOOLS → ENVIRONMENT
```
