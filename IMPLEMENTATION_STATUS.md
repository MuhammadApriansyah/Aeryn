# 🧠 Aeryn v2 — Implementasi Hybrid Rust Engine + Python Logic

> Implementasi bertahap dengan penuh perhatian.
> Engine (Rust) → Logic (Python) → Frontend (TypeScript).

---

## 📊 Status Implementasi

### ✅ Fase 1: Core Engine (Rust) — SELESAI

| Crate | File | Lines | Fungsi |
|-------|------|-------|--------|
| `aeryn-core` | `error.rs` | 150+ | Error types, macros |
| `aeryn-core` | `types.rs` | 800+ | Document, Chunk, Embedding, Brain, Workflow, MCP, Graph |
| `aeryn-core` | `utils.rs` | 500+ | Hashing, distance, normalization, compression |
| `aeryn-vector` | `distance.rs` | 300+ | Cosine, Euclidean, Manhattan, Dot, Hamming |
| `aeryn-vector` | `hnsw.rs` | 700+ | HNSW index, search, insert, remove, serialize |
| `aeryn-vector` | `index.rs` | 400+ | VectorIndex abstraction, BruteForce |
| `aeryn-vector` | `storage.rs` | 200+ | Persistence layer |
| `aeryn-splitter` | `recursive.rs` | 350+ | Recursive character splitter |
| `aeryn-splitter` | `token.rs` | 200+ | Token-based splitter |
| `aeryn-tokenizer` | `lib.rs` | 200+ | LRU cache tokenizer |
| `aeryn-db` | `lib.rs` | 150+ | SQLite adapter |
| `aeryn-processor` | `lib.rs` | 300+ | File processor registry |
| `aeryn-mcp` | `lib.rs` | 50+ | MCP module structure |

**Total Rust: ~4,300+ lines**

---

### 🔄 Fase 2-7: Sedang Dikerjakan

| Fase | Status | Komponen |
|------|--------|----------|
| Fase 2: Processing Engine | 🔄 In Progress | Processor, Graph, Search, Serialization |
| Fase 3: Protocol Engine | ⏳ Pending | MCP Server/Client, Workflow Executor, RAG Pipeline |
| Fase 4: Brain & Plugin Logic | ⏳ Pending | Brain API, Skill YAML, Testing |
| Fase 5: Multi-Agent Logic | ⏳ Pending | Agent Protocol, Orchestration |
| Fase 6: Auth & Tenancy | ⏳ Pending | Workspace, RBAC, API Keys |
| Fase 7: Frontend | ⏳ Pending | Dashboard, Chat, Analytics |

---

## 🏗️ Arsitektur Final

```
aeryn-core-agent/
├── aeryn-engine/                    ← RUST ENGINE
│   ├── Cargo.toml
│   └── crates/
│       ├── aeryn-core/             ← Types, errors, utils
│       ├── aeryn-vector/           ← HNSW vector store
│       ├── aeryn-splitter/         ← Text splitting
│       ├── aeryn-embed/            ← Embedding engine
│       ├── aeryn-tokenizer/        ← Tokenizer
│       ├── aeryn-db/               ← Database adapter
│       ├── aeryn-processor/        ← File processor
│       ├── aeryn-graph/            ← Graph engine
│       ├── aeryn-search/           ← Hybrid search
│       ├── aeryn-serde/            ← Serialization
│       ├── aeryn-mcp/              ← MCP protocol
│       ├── aeryn-workflow/         ← Workflow executor
│       ├── aeryn-rag/              ← RAG pipeline
│       └── aeryn-py/               ← PyO3 bindings
│
├── aeryn_core/                      ← PYTHON LOGIC
│   ├── engine/                      ← Rust engine wrappers
│   │   ├── __init__.py
│   │   ├── vector.py               ← PyVectorStore
│   │   ├── splitter.py             ← PyTextSplitter
│   │   ├── tokenizer.py            ← PyTokenizer
│   │   ├── database.py             ← PyDatabase
│   │   └── processor.py            ← PyProcessor
│   │
│   ├── brain/                       ← Brain class API
│   │   ├── __init__.py
│   │   ├── brain.py                ← Brain class
│   │   ├── manager.py              ← BrainManager
│   │   ├── serialization.py        ← Save/load
│   │   └── info.py                 ← BrainInfo
│   │
│   ├── plugins/                     ← Plugin system
│   │   ├── __init__.py
│   │   ├── manifest.py             ← PluginManifest
│   │   ├── loader.py               ← PluginLoader
│   │   ├── registry.py             ← PluginRegistry
│   │   ├── testing.py              ← Mandatory tests
│   │   └── marketplace.py          ← Marketplace
│   │
│   ├── skills/                      ← Skill system
│   │   ├── __init__.py
│   │   ├── definition.py           ← SkillDefinition
│   │   ├── loader.py               ← SkillLoader
│   │   ├── yaml_parser.py          ← YAML parser
│   │   ├── composable.py           ← Composable skills
│   │   └── testing.py              ← Skill testing
│   │
│   ├── agents/                      ← Multi-agent system
│   │   ├── __init__.py
│   │   ├── protocol.py             ← AgentProtocol
│   │   ├── manager.py              ← AgentManager
│   │   ├── orchestrator.py         ← MultiAgentOrchestrator
│   │   └── divisions/              ← 5 cognitive divisions
│   │
│   ├── workflow/                    ← Workflow engine
│   │   ├── __init__.py
│   │   ├── builder.py              ← WorkflowBuilder
│   │   ├── executor.py             ← WorkflowExecutor
│   │   ├── nodes.py                ← Node types
│   │   └── conditions.py           ← Conditional logic
│   │
│   ├── auth/                        ← Auth & tenancy
│   │   ├── __init__.py
│   │   ├── workspace.py            ← Workspace isolation
│   │   ├── rbac.py                 ← Role-based access
│   │   ├── api_keys.py             ← API key management
│   │   └── jwt.py                  ← JWT authentication
│   │
│   ├── billing/                     ← Billing & usage
│   │   ├── __init__.py
│   │   ├── tracker.py              ← UsageTracker
│   │   └── cost.py                 ← CostCalculator
│   │
│   ├── observability/               ← Observability
│   │   ├── __init__.py
│   │   ├── tracer.py               ← Custom tracer
│   │   ├── langfuse.py             ← Langfuse integration
│   │   └── metrics.py              ← Metrics collection
│   │
│   └── utils/                       ← Utilities
│       ├── __init__.py
│       ├── config.py               ← Configuration
│       ├── logger.py               ← Logging
│       └── llm_client.py           ← LLM client
│
├── apps/
│   ├── api/                         ← FastAPI backend
│   │   ├── routers/
│   │   │   ├── brain.py
│   │   │   ├── chat.py
│   │   │   ├── files.py
│   │   │   ├── agents.py
│   │   │   ├── workflow.py
│   │   │   ├── plugins.py
│   │   │   ├── analytics.py
│   │   │   └── auth.py
│   │   └── main.py
│   │
│   └── web/                         ← React SPA
│       └── src/
│           ├── pages/
│           ├── components/
│           ├── hooks/
│           └── stores/
│
├── plugins/                         ← Plugin directory
│   ├── code-review/
│   ├── scientific-research/
│   └── web-search/
│
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## 🔑 Key Design Decisions

### 1. Rust Engine Priority
- **Vector Store** — HNSW index, 10-100x faster than Python
- **Text Splitter** — Parallel string processing
- **Tokenizer** — LRU cache, SIMD-friendly
- **Database** — Connection pooling, zero-copy

### 2. Python Logic Flexibility
- **Brain API** — Orchestration layer
- **Plugin System** — YAML manifests, mandatory testing
- **Multi-Agent** — Protocol-based communication
- **Workflow** — Conditional/parallel execution

### 3. PyO3 Bindings
- **Zero-copy** for arrays via `numpy` compatibility
- **Batch operations** to minimize FFI overhead
- **Fallback** to pure Python if Rust unavailable

---

*Dokumentasi ini akan diperbarui seiring implementasi.*
*Last updated: 2026-09-02*
*Version: 2.0*
