# 🛣️ Pengembangan Aeryn: Arah & Roadmap

> Berbasis analisis komprehensif Quivr (The-Vibe-Company/quivr) dan evaluasi menyeluruh aeryn-core-agent.

---

## 📊 Executive Summary

| Aspek | Quivr (Reference) | Aeryn (Sekarang) | Gap |
|-------|-------------------|------------------|-----|
| **Arsitektur** | Brain-centric, modular | Monolith → Modular (sedang refactor) | ✅ Sudah dijalankan |
| **RAG Pipeline** | LangChain Chain | Custom pgvector | Perlu integrasi |
| **File Processing** | Multi-format (PDF/DOCX/EPUB/ODT) | Basic text | Perlu diperluas |
| **LLM Abstraction** | Multi-provider + tokenizer cache | Multi-provider | Perlu caching |
| **Storage** | Local/Transparent | PostgreSQL/SQLite | ✅ Lebih baik |
| **Observability** | Langfuse built-in | Custom tracer | Perlu integrasi |
| **Serialization** | Save/load brain | Partial | Perlu lengkap |
| **Frontend** | Chainlit | React SPA | ✅ Lebih custom |

---

## 🎯 Visi: Aeryn sebagai Agent SaaS Platform

```
┌─────────────────────────────────────────────────────────┐
│                    AERYN PLATFORM                        │
├─────────────────────────────────────────────────────────┤
│  Frontend (React SPA)  │  API Gateway (FastAPI)         │
│  - Dashboard           │  - /v1/chat, /v1/brain         │
│  - Brain Manager       │  - /v1/files, /v1/search       │
│  - Analytics           │  - /v1/admin, /v1/agents       │
├─────────────────────────────────────────────────────────┤
│                   CORE ENGINE                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ Brain   │  │ RAG     │  │ LLM     │  │ File    │   │
│  │ Manager │  │ Engine  │  │ Router  │  │ Proc.   │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ Vector  │  │ Storage │  │ Agent   │  │ Observ. │   │
│  │ Store   │  │ Adapter │  │ System  │  │ (trace) │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
├─────────────────────────────────────────────────────────┤
│              Infrastructure (PostgreSQL, Redis, PM2)    │
└─────────────────────────────────────────────────────────┘
```

---

## 📅 Roadmap: 6 Fase Development

---

### 🔵 Fase 1: RAG Engine Overhaul (2-3 minggu)

**Tujuan:** Memindahkan logika RAG ke pattern yang lebih modular dan powerful.

#### 1.1 Brain Class Implementation
```
Trigger: User memiliki koleksi dokumen + ingin QA session.

Implementasi:
- Brain class (mirip Quivr)
- BrainManager untuk CRUD brains
- BrainSerialization (save/load state)
- BrainInfo untuk metadata

Files:
  aeryn_core/brain/
    __init__.py
    brain.py              ← Core Brain class
    brain_manager.py      ← CRUD operations
    brain_serialization.py ← Save/load
    brain_info.py         ← Metadata models
    brain_defaults.py     ← Default configs
```

**Brain API:**
```python
# Create brain from files
brain = await Brain.afrom_files(
    name="Project Documentation",
    file_paths=["docs.pdf", "readme.md"],
    llm=LLMEndpoint.from_config(config)
)

# Search
results = await brain.asearch("How to deploy?", n_results=5)

# Ask with streaming
async for chunk in brain.ask_streaming("Explain the architecture"):
    print(chunk.content, end="")

# Save/Load
await brain.save("/path/to/brain")
brain = Brain.load("/path/to/brain")
```

#### 1.2 RAG Pipeline Modular
```
Trigger: Butuh fleksibilitas chain composition.

Implementasi:
- RetrievalConfig (max_history, max_files, prompt template)
- QuivrQARAG equivalent (AerynRAG)
- LangGraph alternative untuk complex workflows
- Streaming support

Files:
  aeryn_core/rag/
    __init__.py
    aeryn_rag.py          ← Main RAG chain
    rag_config.py         ← RetrievalConfig
    rag_models.py         ← Response models
    rag_prompts.py        ← Template prompts
    rag_utils.py          ← Helper functions
```

#### 1.3 Vector Store Abstraction
```
Trigger: Support multiple vector DBs (FAISS, PGVector, Pinecone).

Implementasi:
- VectorStoreBase abstract class
- FAISS implementation
- PGVector implementation (existing)
- Pinecone implementation

Files:
  aeryn_core/vector_store/
    __init__.py
    base.py               ← Abstract base
    faiss_store.py        ← FAISS adapter
    pgvector_store.py     ← PostgreSQL adapter
    pinecone_store.py     ← Pinecone adapter
```

---

### 🟢 Fase 2: File Processing Expansion (1-2 minggu)

**Tujuan:** Support lebih banyak format file seperti Quivr.

#### 2.1 Processor Registry
```
Trigger: User upload PDF, DOCX, EPUB, ODT.

Implementasi:
- BaseProcessor abstract class
- Processor auto-discovery via entry points
- Built-in processors (txt, md, pdf, docx, epub, odt)
- External processor support

Files:
  aeryn_core/processor/
    __init__.py
    base.py               ← BaseProcessor
    registry.py           ← Auto-discovery
    implementations/
      __init__.py
      default.py          ← Fallback processor
      text_processor.py   ← .txt, .md, .csv
      pdf_processor.py    ← PDF (PyMuPDF, pdfplumber)
      docx_processor.py   ← DOCX (python-docx)
      epub_processor.py   ← EPUB (ebooklib)
      odt_processor.py    ← ODT (odfpy)
      tika_processor.py   ← Apache Tika fallback
```

**Processor Interface:**
```python
class BaseProcessor(ABC):
    @abstractmethod
    async def process_file(self, file: QuivrFile) -> list[Document]:
        """Process file into chunks."""
        pass

    @abstractmethod
    def supports(self, file_extension: str) -> bool:
        """Check if processor supports this file type."""
        pass
```

#### 2.2 Text Splitter
```
Trigger: Chunk besar merusak kualitas embedding.

Implementasi:
- RecursiveCharacterTextSplitter
- Token-aware splitting
- Overlap configuration
- Metadata preservation

Files:
  aeryn_core/processor/
    splitter.py           ← Text splitting algorithms
```

---

### 🟡 Fase 3: LLM Abstraction Enhancement (1-2 minggu)

**Tujuan:** Multi-provider support yang lebih robust.

#### 3.1 Tokenizer Caching
```
Trigger: Tokenizer loading lambat, memory inefficient.

Implementasi:
- LLMTokenizer class with LRU cache
- HuggingFace tokenizer support
- tiktoken fallback
- Memory-bounded cache

Files:
  aeryn_core/llm/
    tokenizer.py          ← Tokenizer with caching
    llm_endpoint.py       ← Multi-provider LLM
    llm_config.py         ← LLM configuration
```

#### 3.2 LLM Router
```
Trigger: Butuh fallback otomatis saat provider down.

Implementasi:
- Priority-based routing
- Health check per provider
- Automatic failover
- Cost tracking

Files:
  aeryn_core/llm/
    llm_router.py         ← Multi-provider router
    health_check.py       ← Provider health monitoring
    cost_tracker.py       ← Usage cost tracking
```

---

### 🟠 Fase 4: Storage & Serialization (1-2 minggu)

**Tujuan:** Brain state bisa disimpan dan direkonstruksi.

#### 4.1 Storage Adapters
```
Trigger: Butuh fleksibilitas penyimpanan.

Implementasi:
- StorageBase abstract class
- LocalStorage (filesystem)
- TransparentStorage (in-memory)
- S3Storage (cloud)
- GCSStorage (cloud)

Files:
  aeryn_core/storage/
    __init__.py
    base.py               ← StorageBase abstract
    local_storage.py      ← Local filesystem
    transparent_storage.py ← In-memory
    s3_storage.py         ← AWS S3
    gcs_storage.py        ← Google Cloud Storage
```

#### 4.2 Brain Serialization
```
Trigger: User ingin export/import brain.

Implementasi:
- BrainSerialized model (Pydantic)
- Save to folder (config.json + vector_store/)
- Load from folder
- Version migration support

Files:
  aeryn_core/brain/
    brain_serialization.py ← Save/load logic
```

---

### 🔴 Fase 5: Observability & Analytics (1 minggu)

**Tujuan:** Monitoring dan tracing yang komprehensif.

#### 5.1 Langfuse Integration
```
Trigger: Butuh observability untuk debug dan analytics.

Implementasi:
- LangfuseService singleton
- Trace/Span tracking
- Token usage tracking
- Cost attribution

Files:
  aeryn_core/observability/
    __init__.py
    langfuse_service.py   ← Langfuse integration
    tracer.py             ← Custom tracer fallback
    metrics.py            ← Metrics collection
```

#### 5.2 Analytics Dashboard
```
Trigger: User ingin lihat usage stats.

Implementasi:
- Endpoint /v1/analytics/usage
- Endpoint /v1/analytics/costs
- Endpoint /v1/analytics/queries
- Real-time metrics

Files:
  apps/api/routers/
    analytics.py          ← Analytics endpoints
```

---

### 🟣 Fase 6: Frontend & UX (2-3 minggu)

**Tujuan:** Dashboard SPA yang comprehensive dan beautiful.

#### 6.1 Brain Management UI
```
Trigger: User butuh GUI untuk manage brains.

Pages:
- Brain list (cards with stats)
- Brain detail (files, chats, settings)
- Create brain wizard
- Upload files interface

Components:
  src/components/brain/
    BrainCard.tsx
    BrainDetail.tsx
    BrainWizard.tsx
    FileUploader.tsx
```

#### 6.2 Chat Interface
```
Trigger: Interaksi chat yang lebih baik.

Features:
- Streaming response display
- File attachment support
- Chat history sidebar
- Source citation display

Components:
  src/components/chat/
    ChatWindow.tsx
    MessageBubble.tsx
    StreamingText.tsx
    SourceCitation.tsx
```

#### 6.3 Analytics Dashboard
```
Trigger: Monitoring usage dan costs.

Features:
- Request volume charts
- Token usage breakdown
- Cost per brain/user
- LLM provider distribution

Components:
  src/components/analytics/
    UsageChart.tsx
    CostBreakdown.tsx
    ProviderStats.tsx
```

---

## 🔌 Quivr → Aeryn Integration Points

### Adopsi Langsung

| Komponen | Quivr | Aeryn Implementation |
|----------|-------|---------------------|
| Brain class | `Brain` | `aeryn_core/brain/brain.py` |
| RAG chain | `QuivrQARAG` | `aeryn_core/rag/aeryn_rag.py` |
| Processor registry | `registry.py` | `aeryn_core/processor/registry.py` |
| LLM endpoint | `LLMEndpoint` | `aeryn_core/llm/llm_endpoint.py` |
| Storage | `StorageBase` | `aeryn_core/storage/base.py` |
| Serialization | `BrainSerialized` | `aeryn_core/brain/brain_serialization.py` |
| Tokenizer cache | `LLMTokenizer` | `aeryn_core/llm/tokenizer.py` |
| Langfuse | `LangfuseService` | `aeryn_core/observability/langfuse_service.py` |

### Adaptasi (Aeryn-Specific)

| Aspek | Quivr | Aeryn |
|-------|-------|-------|
| Vector DB | FAISS default | PGVector default |
| Storage | Local/Transparent | PostgreSQL/SQLM |
| Auth | None | JWT + API keys |
| Multi-tenancy | None | Workspace-based |
| Billing | None | Usage metering |
| Agents | None | 5 cognitive divisions |
| Frontend | Chainlit | React SPA |

---

## 📋 Technical Debt & Refactoring

### Prioritas Tinggi

1. **Hapus legacy code**
   - `apps/web/templates/dashboard.html` (vanilla)
   - `apps/web/server.py` (old routes)
   - `apps/web-next/` (Next.js, tidak terpakai)

2. **Consolidate LLM modules**
   - `aeryn_core/utils/llm_client.py` → `aeryn_core/llm/llm_endpoint.py`
   - `aeryn_core/cost/model_router.py` → `aeryn_core/llm/llm_router.py`

3. **Unify vector stores**
   - `aeryn_core/database/vector_db.py` → `aeryn_core/vector_store/pgvector_store.py`
   - `aeryn_core/database/vector_rust.py` → deprecated

### Prioritas Sedang

4. **Standardize config**
   - `aeryn_core/utils/config.py` → Pydantic BaseSettings
   - Environment-based config loading

5. **Error handling**
   - Global exception handler (FastAPI middleware)
   - Structured error responses
   - Retry logic dengan exponential backoff

6. **Testing**
   - Unit tests untuk core modules
   - Integration tests untuk API endpoints
   - E2E tests untuk frontend

---

## 🏗️ Target Architecture (End State)

```
aeryn-core-agent/
├── aeryn_core/
│   ├── brain/               ← 🧠 Knowledge containers
│   │   ├── brain.py
│   │   ├── brain_manager.py
│   │   ├── brain_serialization.py
│   │   └── brain_info.py
│   ├── rag/                 ← 🔍 RAG engine
│   │   ├── aeryn_rag.py
│   │   ├── rag_config.py
│   │   ├── rag_models.py
│   │   ├── rag_prompts.py
│   │   └── rag_utils.py
│   ├── llm/                 ← 🤖 LLM abstraction
│   │   ├── llm_endpoint.py
│   │   ├── llm_router.py
│   │   ├── llm_config.py
│   │   └── tokenizer.py
│   ├── processor/           ← 📄 File processing
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── splitter.py
│   │   └── implementations/
│   │       ├── text_processor.py
│   │       ├── pdf_processor.py
│   │       ├── docx_processor.py
│   │       ├── epub_processor.py
│   │       └── odt_processor.py
│   ├── vector_store/        ← 💾 Vector databases
│   │   ├── base.py
│   │   ├── pgvector_store.py
│   │   ├── faiss_store.py
│   │   └── pinecone_store.py
│   ├── storage/             ← 📁 File storage
│   │   ├── base.py
│   │   ├── local_storage.py
│   │   ├── transparent_storage.py
│   │   └── s3_storage.py
│   ├── agents/              ← 🤖 Cognitive agents
│   │   ├── agent_base.py
│   │   ├── creative_agent.py
│   │   ├── reasoning_agent.py
│   │   └── governance_agent.py
│   ├── observability/       ← 📊 Monitoring
│   │   ├── langfuse_service.py
│   │   ├── tracer.py
│   │   └── metrics.py
│   ├── auth/                ← 🔐 Authentication
│   │   ├── auth.py
│   │   ├── api_keys.py
│   │   └── rate_limiter.py
│   ├── billing/             ← 💰 Usage metering
│   │   ├── billing.py
│   │   └── usage_metering.py
│   ├── database/            ← 🗄️ Database layer
│   │   ├── db_adapter.py
│   │   ├── shared_db.py
│   │   └── migrations/
│   └── utils/               ← 🔧 Utilities
│       ├── config.py
│       ├── logger.py
│       └── performance.py
├── apps/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── main.py
│   │   │   ├── brain.py       ← Brain CRUD
│   │   │   ├── chat.py        ← Chat endpoints
│   │   │   ├── files.py       ← File upload
│   │   │   ├── search.py      ← Vector search
│   │   │   ├── agents.py      ← Agent execution
│   │   │   ├── analytics.py   ← Usage stats
│   │   │   ├── auth.py        ← Authentication
│   │   │   └── admin.py       ← Admin panel
│   │   └── aeryn_api.py       ← FastAPI app
│   └── web/                   ← React SPA
│       ├── src/
│       │   ├── pages/
│       │   │   ├── Dashboard.tsx
│       │   │   ├── BrainList.tsx
│       │   │   ├── BrainDetail.tsx
│       │   │   ├── Chat.tsx
│       │   │   ├── Analytics.tsx
│       │   │   └── Settings.tsx
│       │   ├── components/
│       │   │   ├── brain/
│       │   │   ├── chat/
│       │   │   ├── files/
│       │   │   └── analytics/
│       │   ├── hooks/
│       │   ├── stores/
│       │   └── utils/
│       └── package.json
├── plugins/
│   ├── postgres_memory/
│   ├── messaging_gateway/
│   └── experience_transfer/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── architecture.md
│   ├── api_reference.md
│   ├── brain_guide.md
│   └── deployment.md
├── ecosystem.config.cjs
├── CHANGELOG.md
└── README.md
```

---

## 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **API uptime** | 99.9% | PM2 + monitoring |
| **Response time** | < 500ms (p95) | API middleware |
| **RAG accuracy** | > 85% relevance | User feedback |
| **File processing** | PDF, DOCX, EPUB, ODT | Integration tests |
| **LLM providers** | 6+ providers | Unit tests |
| **Test coverage** | > 80% | pytest-cov |
| **User satisfaction** | NPS > 50 | Survey |

---

## 🔑 Key Decisions

### 1. LangChain vs Custom RAG
**Decision:** Hybrid — LangChain untuk chain composition, custom untuk optimasi.
**Reason:** LangChain provides flexibility, custom provides performance.

### 2. FAISS vs PGVector
**Decision:** PGVector default, FAISS optional for local dev.
**Reason:** PostgreSQL already in stack, no extra infrastructure.

### 3. Chainlit vs React SPA
**Decision:** React SPA (existing).
**Reason:** More customizable, better UX, already invested.

### 4. Monolith vs Microservices
**Decision:** Modular monolith.
**Reason:** Simpler deployment, easier debugging, sufficient for current scale.

---

## 🚀 Immediate Next Steps

1. **Fase 1.1** — Implement Brain class (1 minggu)
2. **Fase 1.2** — Implement RAG pipeline (1 minggu)
3. **Fase 2.1** — Implement Processor registry (3 hari)
4. **Fase 2.2** — Add PDF/DOCX processors (3 hari)
5. **Fase 3.1** — Add tokenizer caching (2 hari)

---

*Dokumentasi ini akan diperbarui seiring progress development.*
*Last updated: 2026-09-02*
*Version: 1.0*
