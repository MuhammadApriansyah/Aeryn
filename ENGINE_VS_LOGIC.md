# 🎯 Rekayasa Ulang: Engine (Rust) & Logic (Python)

> Pemisahan sistem berdasarkan fungsi: Engine (performance-critical) → Rust, Logic (business/coordination) → Python.
> Engine jadi prioritas utama.

---

## 📊 Pemisahan Engine vs Logic

### 🦀 ENGINE — Performance-Critical (Rust)

| # | Sistem | Sumber | Alasan Rust | Effort |
|---|--------|--------|-------------|--------|
| 1 | **Vector Store** | Quivr (FAISS) | Similarity search = CPU-bound, SIMD-friendly | 🔴 High |
| 2 | **Text Splitter** | LangChain | String processing paralel, memory-safe | 🟡 Medium |
| 3 | **Embedding Engine** | Quivr (OpenAI) | Batch embedding paralel, zero-copy serialization | 🟡 Medium |
| 4 | **Graph Traversal** | Utopia | BFS/DFS paralel, cache-friendly | 🔴 High |
| 5 | **Tokenizer** | LangChain + Quivr | CPU-bound, SIMD untuk token counting | 🟡 Medium |
| 6 | **RAG Pipeline Core** | Quivr | Orchestrate retrieve→rerank→generate dengan minimal overhead | 🔴 High |
| 7 | **Processor Engine** | Quivr | Parse PDF/DOCX/EPUB dengan parallel chunking | 🔴 High |
| 8 | **MCP Protocol** | Utopia | Zero-copy serialization, async I/O | 🟡 Medium |
| 9 | **Workflow Executor** | Dify | Parallel node execution, minimal overhead | 🟡 Medium |
| 10 | **Database Adapter** | Aeryn | Connection pooling, zero-copy row mapping | 🟡 Medium |
| 11 | **Serialization** | Quivr (Brain) | Fast binary format untuk save/load state | 🟢 Low |
| 12 | **Search Engine** | Aeryn | Hybrid vector + keyword + graph search | 🔴 High |

**Total Engine: 12 sistem**

---

### 🐍 LOGIC — Business & Coordination (Python)

| # | Sistem | Sumber | Alasan Python | Effort |
|---|--------|--------|---------------|--------|
| 13 | **Brain Class API** | Quivr | Orchestration layer, panggil Rust engine via FFI | 🟡 Medium |
| 14 | **Skill YAML Standard** | SciAgentSkills | Config parsing, validasi | 🟢 Low |
| 15 | **Mandatory Skill Testing** | Superpowers | Test framework, validasi | 🟢 Low |
| 16 | **Composable Skills** | Superpowers | Dynamic composition, dependency resolution | 🟡 Medium |
| 17 | **Plugin Manifest** | DeepSeek Harness | JSON parsing, validation | 🟢 Low |
| 18 | **Agent Communication Protocol** | Atlas | Message routing, serialization | 🟡 Medium |
| 19 | **Multi-Agent Orchestration** | OpenMAIC | Workflow-based coordination | 🟡 Medium |
| 20 | **Workflow Builder (Conditional)** | Dify | Business rules, user-defined logic | 🟡 Medium |
| 21 | **Workspace Isolation** | Dify | Access control, tenant resolution | 🟢 Low |
| 22 | **RBAC** | Aeryn (existing) | Permission checking | 🟢 Low |
| 23 | **API Key Management** | Dify | Key rotation, scoping | 🟢 Low |
| 24 | **Cost Tracking** | Aeryn (existing) | Billing calculation, aggregation | 🟢 Low |
| 25 | **Agent Marketplace API** | LobeHub | CRUD, search, rating | 🟢 Low |
| 26 | **Analytics Dashboard** | LobeHub | Data aggregation, reporting | 🟡 Medium |
| 27 | **Langfuse Integration** | LangChain | Trace submission, span tracking | 🟢 Low |
| 28 | **Drizzle ORM Schema** | LobeHub | Migration, schema definition | 🟡 Medium |

**Total Logic: 16 sistem**

---

## 📅 Prioritas Implementasi: ENGINE (Rust) Duluan

### 🥇 Fase 1: Core Engine (Rust)
**Tujuan:** Fondasi performa tinggi untuk semua operasi data.

| # | Sistem | FFI Interface | Python Binding |
|---|--------|---------------|----------------|
| 1 | **Vector Store** | `fn search(query: &[f32], k: usize) -> Vec<(usize, f32)>` | `class VectorStore:` → panggil Rust via PyO3 |
| 2 | **Text Splitter** | `fn split_text(text: &str, chunk_size: usize, overlap: usize) -> Vec<String>` | `class TextSplitter:` |
| 3 | **Embedding Engine** | `fn embed_batch(texts: &[&str]) -> Vec<Vec<f32>>` | `class Embedder:` |
| 4 | **Tokenizer** | `fn count_tokens(text: &str) -> usize` | `class Tokenizer:` |
| 5 | **Database Adapter** | `fn query(sql: &str, params: &[Value]) -> Vec<Row>` | `class Database:` |

**Hasil:** Aeryn punya core engine 10-100x lebih cepat dari Python murni.

---

### 🥈 Fase 2: Processing Engine (Rust)
**Tujuan:** File processing dan graph operations.

| # | Sistem | FFI Interface | Python Binding |
|---|--------|---------------|----------------|
| 6 | **Processor Engine** | `fn process_file(path: &str) -> Vec<Chunk>` | `class ProcessorRegistry:` |
| 7 | **Graph Traversal** | `fn bfs(graph: &Graph, start: usize, depth: usize) -> Vec<usize>` | `class GraphMemory:` |
| 8 | **Search Engine** | `fn hybrid_search(query: &str, filters: &Filters) -> Vec<SearchResult>` | `class SearchEngine:` |
| 9 | **Serialization** | `fn save_brain(brain: &BrainState, path: &str) -> Result<()>` | `class BrainStorage:` |

**Hasil:** File processing, graph operations, dan serialization cepat.

---

### 🥉 Fase 3: Protocol Engine (Rust)
**Tujuan:** MCP dan Workflow execution dengan performa tinggi.

| # | Sistem | FFI Interface | Python Binding |
|---|--------|---------------|----------------|
| 10 | **MCP Protocol** | `fn handle_request(req: &[u8]) -> Vec<u8>` | `class MCPServer:` / `class MCPClient:` |
| 11 | **Workflow Executor** | `fn execute_node(node: &Node, inputs: &Inputs) -> Outputs` | `class WorkflowEngine:` |
| 12 | **RAG Pipeline Core** | `fn retrieve(query: &str, n: usize) -> Vec<Document>` | `class AerynRAG:` |

**Hasil:** MCP protocol dan workflow execution dengan minimal overhead.

---

## 📅 Prioritas Implementasi: LOGIC (Python) Setelah Engine

### 4️⃣ Fase 4: Brain & Plugin Logic (Python)
**Tujuan:** Orchestration layer yang panggil Rust engine.

| # | Sistem | Deskripsi | Gunakan Engine |
|---|--------|-----------|----------------|
| 13 | **Brain Class API** | `Brain.from_files()`, `brain.asearch()`, `brain.ask_streaming()` | VectorStore, TextSplitter, Embedder |
| 14 | **Skill YAML Standard** | `skill.yaml` manifest + validation | — |
| 15 | **Mandatory Skill Testing** | `pytest` for every plugin | — |
| 16 | **Composable Skills** | Skill composition + dependency resolution | — |
| 17 | **Plugin Manifest** | `plugin.json` format | — |

---

### 5️⃣ Fase 5: Multi-Agent & Workflow Logic (Python)
**Tujuan:** Koordinasi agent dan workflow builder.

| # | Sistem | Deskripsi | Gunakan Engine |
|---|--------|-----------|----------------|
| 18 | **Agent Protocol** | Message routing, thread management | MCP Protocol |
| 19 | **Multi-Agent Orch** | Sequential/parallel orchestration | Workflow Executor |
| 20 | **Workflow Builder** | Conditional logic, node types | Workflow Executor |

---

### 6️⃣ Fase 6: Auth & Tenancy Logic (Python)
**Tujuan:** Multi-tenant dan access control.

| # | Sistem | Deskripsi | Gunakan Engine |
|---|--------|-----------|----------------|
| 21 | **Workspace Isolation** | Tenant resolution, data scoping | Database Adapter |
| 22 | **RBAC** | Permission checking | — |
| 23 | **API Key Mgmt** | Rotation, revocation, scopes | — |
| 24 | **Cost Tracking** | Billing calculation | — |

---

### 7️⃣ Fase 7: Frontend & Analytics (Python + TypeScript)
**Tujuan:** UI dan reporting layer.

| # | Sistem | Deskripsi | Gunakan Engine |
|---|--------|-----------|----------------|
| 25 | **Marketplace API** | CRUD, search, rating | — |
| 26 | **Analytics Dashboard** | Usage, cost, performance | — |
| 27 | **Langfuse Integration** | Trace submission | — |
| 28 | **Drizzle ORM** | Migration, schema | Database Adapter |

---

## 🏗️ Arsitektur Hybrid Rust ↔ Python

```
┌─────────────────────────────────────────────────────────────────┐
│                         PYTHON LAYER                            │
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

## 🔌 PyO3 Binding Pattern

```rust
// src/engine/vector_store.rs
#[pyclass]
pub struct VectorStore {
    inner: Arc<RwLock<HnswIndex>>,
}

#[pymethods]
impl VectorStore {
    #[new]
    fn new(dim: usize) -> Self { ... }
    
    fn add(&mut self, ids: Vec<String>, embeddings: Vec<Vec<f32>>) { ... }
    
    fn search(&self, query: Vec<f32>, k: usize) -> Vec<(String, f32)> { ... }
    
    fn save(&self, path: &str) -> PyResult<()> { ... }
    
    #[staticmethod]
    fn load(path: &str) -> PyResult<Self> { ... }
}
```

```python
# aeryn_core/engine/vector_store.py
from aeryn_engine import VectorStore as _VectorStore

class VectorStore:
    """Python wrapper untuk Rust VectorStore."""
    
    def __init__(self, dim: int = 1536):
        self._inner = _VectorStore(dim)
    
    def add(self, ids: list[str], embeddings: list[list[float]]):
        self._inner.add(ids, embeddings)
    
    def search(self, query: list[float], k: int = 5) -> list[tuple[str, float]]:
        return self._inner.search(query, k)
```

---

## 📦 Cargo Workspace Structure

```
aeryn-engine/                  ← Rust workspace
├── Cargo.toml
├── crates/
│   ├── aeryn-vector/          ← HNSW vector store
│   ├── aeryn-splitter/        ← Text splitting
│   ├── aeryn-embed/           ← Embedding batch processing
│   ├── aeryn-tokenizer/       ← Token counting
│   ├── aeryn-graph/           ← Graph traversal
│   ├── aeryn-search/          ← Hybrid search engine
│   ├── aeryn-mcp/             ← MCP protocol
│   ├── aeryn-workflow/        ← Workflow executor
│   ├── aeryn-db/              ← Database adapter
│   ├── aeryn-serde/           ← Serialization
│   └── aeryn-py/              ← PyO3 bindings
└── src/
    └── lib.rs                 ← Re-export all
```

---

## 📅 Timeline Estimasi

| Fase | Komponen | Durasi |
|------|----------|--------|
| Fase 1 | Core Engine (Rust) | 2-3 minggu |
| Fase 2 | Processing Engine (Rust) | 2 minggu |
| Fase 3 | Protocol Engine (Rust) | 1-2 minggu |
| Fase 4 | Brain & Plugin Logic (Python) | 2 minggu |
| Fase 5 | Multi-Agent & Workflow (Python) | 1-2 minggu |
| Fase 6 | Auth & Tenancy (Python) | 1 minggu |
| Fase 7 | Frontend & Analytics | 2 minggu |

**Total: ~11-14 minggu (3-3.5 bulan)**

---

*Dokumentasi ini akan diperbarui seiring implementasi.*
*Last updated: 2026-09-02*
*Version: 1.0*
