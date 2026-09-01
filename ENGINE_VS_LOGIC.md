# 🏗️ Arsitektur Hybrid: Rust Engine + Python Logic

> Desain terpisah antara Engine (Rust) dan Logic (Python).
> Engine = performance-critical, Logic = business/coordination.
> **Engine diimplementasikan lebih dulu.**

---

## 📊 Pemisahan Sistem

### 🦀 ENGINE (Rust) — 12 Sistem

| # | Sistem | Sumber | Alasan Rust | FFI Binding |
|---|--------|--------|-------------|-------------|
| 1 | **Vector Store** | Quivr (FAISS) | Similarity search = CPU-bound, SIMD | `PyVectorStore` |
| 2 | **Text Splitter** | LangChain | String processing paralel | `PyTextSplitter` |
| 3 | **Embedding Engine** | Quivr | Batch embedding paralel | `PyEmbedder` |
| 4 | **Tokenizer** | LangChain + Quivr | CPU-bound, SIMD token counting | `PyTokenizer` |
| 5 | **Graph Traversal** | Utopia | BFS/DFS paralel | `PyGraphEngine` |
| 6 | **RAG Pipeline Core** | Quivr | Orchestrate retrieve→rerank→generate | `PyRAGPipeline` |
| 7 | **Processor Engine** | Quivr | Parse PDF/DOCX/EPUB parallel | `PyProcessor` |
| 8 | **MCP Protocol** | Utopia | Zero-copy serialization | `PyMCPServer` / `PyMCPClient` |
| 9 | **Workflow Executor** | Dify | Parallel node execution | `PyWorkflowEngine` |
| 10 | **Database Adapter** | Aeryn | Connection pooling, zero-copy | `PyDatabase` |
| 11 | **Serialization** | Quivr | Fast binary save/load | `PyBrainStorage` |
| 12 | **Search Engine** | Aeryn | Hybrid vector+keyword+graph | `PySearchEngine` |

### 🐍 LOGIC (Python) — 16 Sistem

| # | Sistem | Sumber | Alasan Python | Panggil Engine |
|---|--------|--------|---------------|----------------|
| 13 | **Brain Class API** | Quivr | Orchestration layer | VectorStore, TextSplitter, Embedder |
| 14 | **Skill YAML Standard** | SciAgentSkills | Config parsing | — |
| 15 | **Mandatory Skill Testing** | Superpowers | Test framework | — |
| 16 | **Composable Skills** | Superpowers | Dynamic composition | — |
| 17 | **Plugin Manifest** | DeepSeek Harness | JSON validation | — |
| 18 | **Agent Protocol** | Atlas | Message routing | MCP Protocol |
| 19 | **Multi-Agent Orch** | OpenMAIC | Workflow coordination | Workflow Executor |
| 20 | **Workflow Builder** | Dify | Business rules | Workflow Executor |
| 21 | **Workspace Isolation** | Dify | Access control | Database Adapter |
| 22 | **RBAC** | Aeryn | Permission checking | — |
| 23 | **API Key Mgmt** | Dify | Key rotation | — |
| 24 | **Cost Tracking** | Aeryn | Billing calculation | — |
| 25 | **Marketplace API** | LobeHub | CRUD operations | — |
| 26 | **Analytics Dashboard** | LobeHub | Data aggregation | — |
| 27 | **Langfuse Integration** | LangChain | Trace submission | — |
| 28 | **Drizzle ORM** | LobeHub | Migration, schema | Database Adapter |

---

## 📅 Prioritas Implementasi

### Fase 1: Core Engine (Rust) — 2-3 minggu
**Sistem:** Vector Store, Text Splitter, Embedding Engine, Tokenizer, Database Adapter

### Fase 2: Processing Engine (Rust) — 2 minggu
**Sistem:** Processor Engine, Graph Traversal, Search Engine, Serialization

### Fase 3: Protocol Engine (Rust) — 1-2 minggu
**Sistem:** MCP Protocol, Workflow Executor, RAG Pipeline Core

### Fase 4: Brain & Plugin Logic (Python) — 2 minggu
**Sistem:** Brain Class API, Skill YAML, Testing, Composable Skills, Plugin Manifest

### Fase 5: Multi-Agent & Workflow Logic (Python) — 1-2 minggu
**Sistem:** Agent Protocol, Multi-Agent Orch, Workflow Builder

### Fase 6: Auth & Tenancy Logic (Python) — 1 minggu
**Sistem:** Workspace Isolation, RBAC, API Key Mgmt, Cost Tracking

### Fase 7: Frontend & Analytics (Python + TypeScript) — 2 minggu
**Sistem:** Marketplace API, Analytics Dashboard, Langfuse Integration, Drizzle ORM

---

## 🔌 PyO3 Binding Layer

```rust
// crates/aeryn-py/src/lib.rs
use pyo3::prelude::*;

#[pymodule]
fn aeryn_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<vector::PyVectorStore>()?;
    m.add_class::<splitter::PyTextSplitter>()?;
    m.add_class::<embed::PyEmbedder>()?;
    m.add_class::<tokenizer::PyTokenizer>()?;
    m.add_class::<graph::PyGraphEngine>()?;
    m.add_class::<rag::PyRAGPipeline>()?;
    m.add_class::<processor::PyProcessor>()?;
    m.add_class::<mcp::PyMCPServer>()?;
    m.add_class::<mcp::PyMCPClient>()?;
    m.add_class::<workflow::PyWorkflowEngine>()?;
    m.add_class::<db::PyDatabase>()?;
    m.add_class::<storage::PyBrainStorage>()?;
    m.add_class::<search::PySearchEngine>()?;
    Ok(())
}
```

```python
# aeryn_core/engine/__init__.py
"""Python bindings untuk Rust engine."""
try:
    from aeryn_engine import (
        PyVectorStore,
        PyTextSplitter,
        PyEmbedder,
        PyTokenizer,
        PyGraphEngine,
        PyRAGPipeline,
        PyProcessor,
        PyMCPServer,
        PyMCPClient,
        PyWorkflowEngine,
        PyDatabase,
        PyBrainStorage,
        PySearchEngine,
    )
except ImportError:
    # Fallback ke pure Python implementation
    from .fallback import *
```

---

## 🏗️ Arsitektur Target

```
┌─────────────────────────────────────────────────────────────────┐
│                        PYTHON LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Brain API   │  │ Agent Orch  │  │ Workflow    │              │
│  │ (Logic)     │  │ (Logic)     │  │ Builder     │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                     │
│  ┌──────┴────────────────┴────────────────┴──────┐              │
│  │              PyO3 Bindings                      │              │
│  └──────┬────────────────┬────────────────┬──────┘              │
├─────────┼────────────────┼────────────────┼─────────────────────┤
│         │   RUST ENGINE  │                │                     │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐              │
│  │ VectorStore │  │ TextSplitter│  │ Embedder    │              │
│  │ (HNSW)      │  │ (Parallel)  │  │ (Batch)     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ GraphEngine │  │ Processor   │  │ Search      │              │
│  │ (BFS/DFS)   │  │ (PDF/DOCX)  │  │ (Hybrid)    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ MCP Protocol│  │ Workflow    │  │ Database    │              │
│  │ (Zero-copy) │  │ Executor    │  │ Adapter     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Cargo Workspace Structure

```
aeryn-engine/
├── Cargo.toml                 ← Workspace root
├── crates/
│   ├── aeryn-core/           ← Core types, errors, utils
│   ├── aeryn-vector/         ← HNSW vector store
│   ├── aeryn-splitter/       ← Text splitting
│   ├── aeryn-embed/          ← Embedding engine
│   ├── aeryn-tokenizer/      ← Tokenizer with cache
│   ├── aeryn-graph/          ← Graph traversal
│   ├── aeryn-rag/            ← RAG pipeline core
│   ├── aeryn-processor/      ← File processor
│   ├── aeryn-mcp/            ← MCP protocol
│   ├── aeryn-workflow/       ← Workflow executor
│   ├── aeryn-db/             ← Database adapter
│   ├── aeryn-storage/        ← Brain serialization
│   ├── aeryn-search/         ← Hybrid search
│   └── aeryn-py/             ← PyO3 bindings
└── src/
    └── lib.rs                 ← Re-export all
```

---

## 🔑 Key Decisions

### Mengapa Engine diutamakan?
1. **Performance-critical** — Vector search, text processing, embedding = CPU-bound
2. **Foundation** — Semua logic Python butuh engine yang cepat
3. **Parallelism** — Rust + Rayon = easy data parallelism
4. **Memory safety** — Tanpa GC pause, predictable performance

### Mengapa Logic tetap Python?
1. **Flexibility** — Business rules sering berubah
2. **Ecosystem** — LangChain, Quivr, Dify = Python
3. **Prototyping** — Cepat iterasi logic
4. **FFI overhead** — PyO3 cukup cepat untuk coordination

### Komunikasi Rust ↔ Python
- **PyO3** — Zero-copy untuk arrays, minimal overhead
- **Serde** — JSON untuk complex types
- **Batch operations** — Kurangi FFI calls

---

*Dokumentasi ini akan diperbarui seiring implementasi.*
*Last updated: 2026-09-02*
*Version: 1.0*
