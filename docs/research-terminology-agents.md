# Aeryn — Riset: Layers & Terminologi AI Agent (sejenis Hermes)

> Riset atas terminologi AI Agent industri 2025–2026 untuk mempertimbangkan
> Aeryn sebagai **Personal AI Assistant + Autonomous AI Agent**.
> Sumber: arXiv 2603.05344 (Building AI Coding Agents for the Terminal),
> Digital Applied Glossary 2026 (60 terms), Elementum/Deloitte/Tyk orchestration
> guides, plus pemetaan ke arsitektur Aeryn aktual.

## 1. Terminologi industri (peta standar)

### Core primitives (dasar)
| Term | Definisi | Pemetaan Aeryn |
|------|----------|----------------|
| **Agent** | Entitas komputasional yang mempersepsikan lingkungan (sensors) dan bertindak (actuators) untuk mencapai goal (Russell & Norvig) | Aeryn keseluruhan: sensors = tools + gateway, actuators = reminder/ledger/notify |
| **Tool use** | LLM memanggil fungsi terstruktur untuk baca state / aksi nyata | MCP 15 tools + internal_tools (fs, memory, graph, battery) |
| **Function calling** | Nama OpenAI untuk tool use (JSON args dieksekusi host) | chat_agent → tool bridge |

### Protocols & SDKs (integrasi)
| Term | Definisi | Pemetaan Aeryn |
|------|----------|----------------|
| **MCP** (Model Context Protocol) | Protokol agent ↔ tool/data (BATALKAN "agent communication" — itu A2A) | `mcp_server.py` 15 tools |
| **A2A** (Agent-to-Agent) | Protokol agent ↔ agent (discovery + opaque komunikasi) | **BELUM ADA** — roadmap (5 divisions internal, belum ekspor A2A) |
| **AGENTS.md** | Konvensi file instruksi proyek untuk coding agent | Ada di repo (AGENTS.md) |

### Architectures & orchestration (pola)
| Term | Definisi | Pemetaan Aeryn |
|------|----------|----------------|
| **Orchestration layer** | Control plane: interpretasi goal → decompose → koordinasi eksekusi → quality | L7: 5 divisions + crew_orchestrator + phase_workflow |
| **Supervisor pattern** | 1 agent koordinator menugaskan worker spesialis, mengumpulkan hasil (topologi paling umum) | **BELUM EKSPLISIT** — divisions ada tapi tanpa supervisor loop formal |
| **Swarm pattern** | Peer agents saling handoff dinamis berdasar kebutuhan spesialis | Alternatif — roadmap |
| **Fan-out / fan-in** | Parallel sub-tasks → merge di synchronization barrier (MapReduce) | Crew orchestrator parallel execute |
| **Subagent** | Child agent dari parent — context window + tool budget sendiri (Claude Code: 1 level, tanpa spawn rekursif) | **BELUM ADA** — agent loop tunggal, tanpa spawn subagent |
| **ReAct** | Loop reason → act → observe (Yao et al. 2022) | agent_loop: trust → recall → LM (mendekati, tanpa observe eksplisit) |
| **Reflexion** | Agent kritik verbal trajectory sendiri sebelum re-attempt (Shinn et al. 2023) | reflection.py ada — belum wired ke loop |

### Memory & context
| Term | Definisi | Pemetaan Aeryn |
|------|----------|----------------|
| **Context engineering** | Manajemen state yang masuk ke model: system prompt, history, tools, retrieval | recall 5 sumber + hybrid search |
| **Bitemporal memory** | VALID TIME (kapan benar di dunia) + TRANSACTION TIME (kapan tercatat) — audit trail | **UNIK AERYN** — fact_store (tidak ada di Hermes/OpenClaw!) |
| **Hybrid retrieval** | Vector + keyword + graph | embedding (384-dim) + FTS + graph nerve |
| **Active forgetting / decay** | Hapus/arsip memori lewat aturan (FSRS-6 di industri) | decay: note>180d, heartbeat>30d (bitemporal valid_to) |

### Safety & governance
| Term | Definisi | Pemetaan Aeryn |
|------|----------|----------------|
| **Guardrails** | Validasi input/output, hallucination filter | safety_engine (24K), guardrails |
| **HITL** (human-in-the-loop) | Approval gate di titik berisiko | approvals.db (Ada!) |
| **Observability** | Trace per request, metrics, drift detection | tracer (Span/Trace), /traces, watchdog |

## 2. Pemetaan ke arsitektur Hermes-class (arXiv 2603.05344)

Paper itu mendokumentasikan arsitektur Hermes Agent (Velocity release) —
pemetaan langsung ke Aeryn:

| Layer Hermes (paper) | Hermes implementasi | Aeryn implementasi | Gap Aeryn |
|---------------------|---------------------|--------------------|-----------|
| **Agent Core Layer** | run_agent.py 76% refactor 14 modul | aeryn_core/agent/ (loop, trust, goal) | ✅ sejenis |
| **Concurrent sessions** | TUI session orchestrator multi-session | chat session per user (profile_router) | ⚠️ tanpa multi-session TUI |
| **Subagent orchestration** | Spawn isolated subagent (filtered tools, parallel) | **TIDAK ADA** | ❌ GAP UTAMA |
| **Typed workflows** | Execution/Thinking/Compaction | phase_workflow (ada, belum typed) | ⚠️ |
| **Memory** | session_search 4500x faster (FTS, no LLM) | recall 5 sumber + bitemporal + nerve | ✅ lebih kaya (bitemporal unik) |
| **Skills** | Skill bundles + crystallization | skill_crystallization + marketplace | ✅ sejenis |
| **Security** | Promptware defense 3 chokepoints | safety_engine + trust_layer + guardrails | ✅ sejenis |
| **Gateway** | Telegram/multi-platform | Discord gateway + termux-notification | ✅ sejenis (WA dilarang) |
| **Observability** | agenttrace, cost tracking | tracer (baru aktif), watchdog | ⚠️ tanpa cost tracking |

## 3. Kesimpulan: posisi Aeryn

**Aeryn = Personal AI Assistant + Autonomous AI Agent dengan keunggulan unik:**

1. ✅ **Lebih kaya dari Hermes-class di MEMORY** — bitemporal fact_store (valid/tx
   time) + graph nerve + decay: Hermes/OpenClaw tidak punya ini
2. ✅ **Personal ritual yang tidak ada di coding agent** — briefing pagi otomatis,
   multi-reminder, ledger keuangan (Rust native), termux-notification
3. ✅ **Daily/Weekly/Monthly loop tertutup** — bukan sekadar coding tool
4. ❌ **GAP UTAMA vs Hermes-class**: **Subagent orchestration** — Hermes/Claude
   Code spawn subagent isolated (parallel exploration); Aeryn masih agent loop
   tunggal. Ini roadmap terbesar untuk Autonomous AI Agent
5. ⚠️ **Gap sekunder**: A2A protocol (agent↔agent eksternal), typed workflows,
   cost tracking observability, multi-session TUI

## 4. Roadmap berbasis riset (dampak → rendah)

1. **Subagent orchestration** — spawn isolated subagent (context + tool budget
   sendiri) untuk parallel exploration → Aeryn jadi Autonomous AI Agent sejati
2. **Supervisor loop formal** — divisions jadi worker dengan supervisor koordinator
3. **A2A protocol** — ekspor AgentCard, agent↔agent discovery eksternal
4. **Reflexion wiring** — reflection.py → agent_loop (self-correcting)
5. **Cost tracking** — token usage + spend per session (tracer extend)
6. **Scheduler Rust + tools sensor** (roadmap lama, tetap valid)
