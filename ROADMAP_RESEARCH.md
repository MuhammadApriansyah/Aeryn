# Aeryn — Arah Pengembangan Selanjutnya (Berdasarkan Riset)

> Dokumen ini adalah hasil riset dari sumber-sumber terpercaya & tervalidasi tentang
> apa yang dibutuhkan sebuah **agent framework produksi** agar jadi utuh.
> Disusun: 2026-09-03

---

## 0. Sumber Terpercaya (Divalidasi)

| # | Sumber | Jenis | Poin Kunci |
|---|--------|-------|-----------|
| 1 | **MAESTRO** (arXiv 2601.00481) | Paper akademik | Gap: 75% tim produksi MAS evaluasi TANPA benchmark; kurangnya telemetry terpadu; "silent information consumption" |
| 2 | **LangGraph/OpenTelemetry GenAI SIG** (Zylos Research, 2026) | Artikel teknis | Industri konvergen ke OpenTelemetry; span types `chat`/`invoke_agent`/`execute_tool`; Datadog/Honeycomb/New Relic sudah support |
| 3 | **OpenTelemetry GenAI Semantic Conventions** (MLflow/CNCF) | Standar resmi | Skema atribut `gen_ai.*` untuk LLM call, token, model, agent |
| 4 | **Deploying Agentic AI to Production** (AWS/Azure Playbook, Pramod, 2026) | Panduan industri | **"8 production requirements"** — checklist yang memisahkan demo vs sistem terdeploy |
| 5 | **Evaluation and Benchmarking of LLM Agents: A Survey** (arXiv 2507.21504) | Paper akademik | Metrik: success rate, stepwise progress, tool selection accuracy, parameter accuracy, efficacy |
| 6 | **Evaluating LLM-based Agents** (Samira Ghodratnama, Google) | Artikel praktisi | Metrik multi-agent: coordination efficiency, communication overhead, plan quality |
| 7 | **Reframing LLM Agent Security as AHI** (arXiv 2605.24309) | Paper akademik | 21/21 sistem produksi pakai human-in-the-loop; NOL yang percaya LLM saja untuk keamanan |
| 8 | **12 Guardrails Every AI Agent Needs** (Contro1) | Artikel industri | Guardrail = 4 lapis: policy, tool permission, runtime validation, human approval |
| 9 | **Top 5 AI Agent Frameworks 2025** (LangGraph, CrewAI, OpenAI, LlamaIndex, AutoGen) | Analisis industri | Kriteria evaluasi framework produksi |

---

## 1. Kekurangan Aeryn Saat Ini → Konfirmasi Riset

Berikut pemetaan kekurangan yang sudah kusampaikan, kini **dikonfirmasi & dilengkapi** oleh riset:

### 1.1 Execution Runtime (Async/Background) — KONFIRMASI KRITIS
- **Sumber #4**: "Standar HTTP endpoint timeout 30 detik. Agent customer-support bisa jalan 20 menit, research agent 4 jam."
- **Dampak Aeryn**: `/v1/chat` sekarang sinkron → akan timeout untuk task panjang.
- **Yang terlewat dari analisis awal**: butuh **task queue** (bukan cuma "async" — tapi durable queue yang survive restart, scale to zero, support long-running sessions).

### 1.2 Session State & Memory Isolation — KONFIRMASI
- **Sumber #4**: "checkpointer lokal dengan InMemorySaver tidak cukup. Perlu checkpointer yang survive process restart, scale across instances, ISOLATE state antar user."
- **Dampak Aeryn**: session `get_or_create_session()` in-memory → hilang saat restart, dan **tidak ada isolasi antar user** (semua user share satu namespace).
- **Yang terlewat**: multi-instance scaling + isolasi state antar user adalah requirement terpisah dari sekadar "simpan history".

### 1.3 Tool Access & Security (Policy Enforcement) — KONFIRMASI KRITIS & BESAR
- **Sumber #7 (paper)**: "No deployed system trusts an LLM alone to determine whether an action is safe." — 21/21 sistem produksi pakai human-in-the-loop.
- **Sumber #8**: "The tool itself is the gate. Wrap destructive tools with an approval call before the body runs — bukan cuma prompt rule."
- **Dampak Aeryn**: `bash_tool` kita cuma punya `blocklist` string — **INI BUKAN GUARDRAIL YANG BENAR**. Riset tegas: prompt/blocklist tidak cukup, perlu **policy enforcement di lapisan tool invocation** + **human approval gate**.
- **Yang terlewat besar**: Aeryn belum punya lapisan approval/human-in-the-loop sama sekali.

### 1.4 Identity & Authentication — TERLEWAT dari analisis awal tapi KRITIS
- **Sumber #4**: "Who is the agent acting as? shared service account (dangerous) vs impersonate user vs managed identity."
- **Dampak Aeryn**: agent bertindak tanpa identitas terkelola — berbahaya untuk tool yang menulis/menghapus.

### 1.5 Observability/Tracing — KONFIRMASI, dengan standar konkret
- **Sumber #1 (MAESTRO)**: "kurangnya telemetry terpadu → silent information consumption."
- **Sumber #2/#3**: standar = **OpenTelemetry GenAI Semantic Conventions**. Span types: `chat` (LLM call), `invoke_agent` (agent), `execute_tool` (tool). Atribut `gen_ai.*` untuk token, model, latency.
- **Dampak Aeryn**: tracing kita cuma dict `reasoning` polos, **tidak OTel-compliant**, tidak bisa lihat token-per-span, latency, decision tree.
- **Yang terlewat**: perlu **token accounting per-span** (lihat loop yang memakan 50k token) + **session-level metrics**.

### 1.6 Continuous Evaluation — KONFIRMASI & METRIK JELAS
- **Sumber #1**: 75% tim produksi MAS evaluasi tanpa benchmark.
- **Sumber #5**: metrik = **success rate**, **stepwise progress rate**, **tool selection accuracy**, **parameter accuracy**, **efficacy**.
- **Sumber #6 (multi-agent)**: **coordination efficiency** (success per komunikasi), **communication overhead**, **plan quality**, **failure attribution**.
- **Dampak Aeryn**: belum ada evaluasi otomatis sama sekali, apalagi benchmark.
- **Yang terlewat**: evaluasi bukan cuma "benar/salah", tapi **diagnostic tools** (trace balik tiap failure ke agent/step yang salah).

### 1.7 Multi-Agent Orchestration — KONFIRMASI, dengan metrik khusus
- **Sumber #6**: multi-agent punya dimanesi evaluasi terpisah yang tidak bisa ditangkap single-agent metric: koordinasi, komunikasi, rencana grup, fairness.
- **Sumber #9**: pola topologi = centralized (supervisor), hierarchical, peer-to-peer, shared memory. LangGraph = graph state machine.
- **Dampak Aeryn**: 5 divisi jalan TERPISAH, belum ada topologi kolaborasi.

### 1.8 True Streaming — KONFIRMASI (terlewat dari sumber eksplisit, tapi implisit)
- **Sumber #4**: "long-running sessions" → user perlu lihat progress real-time, bukan tunggu selesai.
- **Dampak Aeryn**: streaming sekarang fake (kumpul semua → kirim), bukan token-by-token.

### 1.9 Error Recovery — KONFIRMASI implisit
- **Sumber #2**: failure modes agen = "stuck tool loops, runaway token costs, context propagation failures."
- **Dampak Aeryn**: kalau tool crash, loop cuma "max iterations", tanpa auto-retry/fallback.

### 1.10 Observability of Evaluation (yang baru kusadari dari riset)
- **Sumber #2**: evaluasi BUKAN bagian GenAI semantic conventions — "they do not cover output evaluation, safety scoring, or content quality."
- **Implikasi**: Aeryn perlu **lapisan evaluasi terpisah** di atas tracing.

---

## 2. Framework Evaluasi Diri — Seberapa Jauh Aeryn?

| Requirement Produksi (Sumber #4) | Aeryn Sekarang | Gap |
|----------------------------------|----------------|-----|
| 1. Execution Runtime (long-running) | ❌ Sinkron, timeout | BESAR |
| 2. Session State + Memory (persistent, isolated) | ⚠️ In-memory, no isolation | SEDANG |
| 3. Tool Access + Security (policy) | ⚠️ Blocklist string saja | BESAR |
| 4. Identity + Auth | ❌ Tidak ada | BESAR |
| 5. Observability (OTel GenAI) | ⚠️ Dict polos | SEDANG |
| 6. Guardrails (4 lapis) | ⚠️ Prompt + blocklist | BESAR |
| 7. Scalability (multi-instance) | ❌ Single process | BESAR |
| 8. Continuous Evaluation | ❌ Tidak ada | BESAR |

**Kesimpulan:** Aeryn sudah punya "agent core" yang berfungsi (LLM loop, tools, memory, divisi, plugin), tapi **belum punya lapisan produksi** (runtime, guardrail, observability, evaluasi, auth).

---

## 3. Arah Pengembangan Aeryn — Prioritas Berbasis Dampak

Berdasarkan riset, urutan prioritas berikut (dampak tinggi + dikonfirmasi banyak sumber):

### FASE 5 (PRODUCTION HARDENING) — Prioritas Tertinggi

**5.1 Guardrails & Human-in-the-Loop** (Sumber #7, #8 — paling dikonfirmasi)
- Policy enforcement di lapisan tool invocation (bukan prompt/blocklist)
- Approval gate untuk destructive tool (delete, write ke production, send)
- Payload approval yang kaya: nama tool, argumen persis, jumlah record terpengaruh, irreversible flag, estimasi biaya
- Approval bisa edit/reject, bukan cuma approve
- Role-based routing approval

**5.2 Execution Runtime + Async** (Sumber #4 — requirement #1)
- Task queue durable (survive restart)
- Background worker untuk long-running agent
- Support session 20 menit–4 jam
- Scale to zero + scale up rapidly

**5.3 Observability (OTel GenAI)** (Sumber #2, #3 — ada standar resmi)
- Span types: `chat`, `invoke_agent`, `execute_tool`
- Atribut `gen_ai.*`: token usage, model, latency, finish reason
- Session-level metrics
- Token accounting per-span (untuk deteksi loop)

**5.4 Session State + Isolasi User** (Sumber #4 — requirement #2)
- Checkpointer persistent (SQLite → Postgres)
- Isolasi state antar user
- Long-term memory lintas sesi

**5.5 Identity + Auth** (Sumber #4 — requirement #4)
- Agent identity terkelola
- API key / token per user
- Least-privilege scope per tool

### FASE 6 (CONTINUOUS EVALUATION)

**6.1 Evaluation Harness** (Sumber #5, #6)
- Metrik: success rate, stepwise progress rate, tool selection accuracy, parameter accuracy, efficacy
- Multi-agent: coordination efficiency, communication overhead, plan quality, failure attribution
- Diagnostic tools (trace balik failure → agent/step bersalah)
- Benchmark suite (atau pakai MAESTRO/MultiAgentBench/AgentBoard)

### FASE 7 (MULTI-AGENT ORCHESTRATION)

**7.1 Topologi Kolaborasi** (Sumber #9)
- Supervisor (centralized) untuk 5 divisi
- Handoff antar divisi
- Shared memory / blackboard
- Graph state machine (pola LangGraph)

### FASE 8 (TRUE STREAMING & ERROR RECOVERY)

**8.1 Streaming token-by-token** (Sumber #4)
**8.2 Auto-retry + fallback untuk tool crash** (Sumber #2)

---

## 4. Prinsip Desain dari Riset (daftar checklist)

1. **"The tool itself is the gate"** — guardrail ada DI DALAM tool function, bukan prompt.
2. **"The model's intelligence is not a substitute for a permission boundary."**
3. **"No deployed system trusts an LLM alone for safety."**
4. **"Token cost is both a cost center and a functional signal."** — lacak token per span.
5. **"Emergent failures need semantic telemetry"** — bukan cuma "did it run?" tapi "what did it decide & why."
6. **"Evaluation is not part of tracing"** — butuh lapisan evaluasi terpisah.
7. **"Standard HTTP timeout 30s doesn't work for agents."**
8. **"75% produksi MAS evaluasi tanpa benchmark"** — jangan ikut; bangun benchmark dari awal.

---

## 5. Rekomendasi Konkret Next Step

**Rekomendasi: mulai dari FASE 5.1 (Guardrails + Human-in-the-Loop).**

Alasan:
1. **Paling dikonfirmasi** (Sumber #7: 21/21 sistem, Sumber #8: 4 lapis guardrail)
2. **Gap paling berbahaya** — Aeryn sekarang cuma blocklist string untuk `bash` yang bisa `rm -rf`
3. **Tidak butuh infra besar** — bisa dibangun di atas tool registry yang sudah ada
4. **Langsung menaikkan kualitas ke "produksi-grade"**

Setelah itu → 5.3 Observability (OTel GenAI), lalu 5.2 Runtime async.

---

## 6. Sumber Lengkap (untuk referensi)

1. MAESTRO — arXiv 2601.00481 — `https://arxiv.org/html/2601.00481`
2. OpenTelemetry for AI Agents — Zylos Research — `https://zylos.ai/research/2026-02-28-opentelemetry-ai-agent-observability`
3. OTel GenAI Semantic Conventions — MLflow/CNCF — `https://mlflow.org/docs/latest/genai/tracing/opentelemetry/genai-semconv`
4. Deploying Agentic AI to Production — Pramod (AWS/Azure) — `https://medium.com/@pramod21/deploying-agentic-ai-to-production-the-complete-aws-and-azure-playbook-ecb5f44367eb`
5. Evaluation & Benchmarking of LLM Agents — arXiv 2507.21504
6. Evaluating LLM-based Agents — Samira Ghodratnama (Google) — `https://samira-ghodratnama.github.io/posts/Evaluating-LLM-based-Agents-Metrics-Benchmarks-and-Best-Practices/`
7. Reframing LLM Agent Security as AHI — arXiv 2605.24309
8. 12 Guardrails Every AI Agent Needs — Contro1 — `https://contro1.com/resources/12-guardrails-every-ai-agent-needs-before-production`
9. Top 5 AI Agent Frameworks 2025 — Maxim — `https://maxim-articles.ghost.io/top-5-ai-agent-frameworks-in-2025-a-practical-guide-for-ai-builders`

---

> **Verdict:** Aeryn sudah jadi *agent core* yang berfungsi (Fase 1-4). Riset terpercaya menegaskan:
> yang membedakan *demo* vs *produksi* adalah 8 production requirements (runtime, state,
> tool security, identity, observability, guardrails, scalability, evaluation).
> Aeryn perlu Fase 5-8 untuk jadi *framework seutuhnya*, dimulai dari **Guardrails + HITL**.