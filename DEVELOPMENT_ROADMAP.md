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

## 📚 Resource Analysis — 10 Repository untuk Pengembangan Aeryn

> Analisis komprehensif 10 repository open-source untuk arah pengembangan Aeryn selanjutnya.

### 📊 Executive Summary

| # | Repository | Type | Stack | Key Takeaway for Aeryn |
|---|------------|------|-------|----------------------|
| 1 | **langchain** | Framework | Python (3,044 files) | RAG patterns, agent architecture, LCEL |
| 2 | **OpenMAIC** | Platform | Next.js/TS (2,827 files) | Multi-agent learning, classroom generation |
| 3 | **atlas** | Product | Rust/TS (4,848 files) | ACP thread protocol, agent management |
| 4 | **utopia** | Framework | Rust/TS (236 files) | Graph-based RAG, MCP connectors |
| 5 | **archify** | Tool | Node.js (468 files) | Architecture visualization, IR rendering |
| 6 | **deepseek-harness** | Agent | TS (8,835 files) | Plugin architecture, agent orchestration |
| 7 | **scientific-agent-skills** | Skills | Python (2,446 files) | 163+ scientific skills, plugin standard |
| 8 | **superpowers** | Methodology | Multi (194 files) | Composable agent skills, SDLC |
| 9 | **lobehub** | Platform | Next.js/TS (15,774 files) | Agent marketplace, multi-model chat |
| 10 | **dify** | Platform | Python/TS (13,656 files) | LLM workflow, RAG pipeline, agent tools |

---

### 🔬 Deep Analysis

---

#### 1. 🔗 langchain-ai/langchain

**URL:** https://github.com/langchain-ai/langchain  
**Stars:** ~100k+  
**License:** MIT  
**Stack:** Python (3,044 files)

**Architecture:**
```
langchain/
├── libs/
│   ├── core/                    ← Core abstractions
│   │   └── langchain_core/
│   │       ├── runnables/       ← Runnable interface (LCEL)
│   │       ├── tools/           ← Tool definitions
│   │       ├── embeddings/      ← Embedding models
│   │       ├── vectorstores/    ← Vector store interface
│   │       ├── documents/       ← Document model
│   │       ├── prompts/         ← Prompt templates
│   │       ├── messages/        ← Message types
│   │       ├── output_parsers/  ← Output parsing
│   │       ├── tracers/         ← Observability
│   │       └── callbacks/       ← Callback handlers
│   ├── langchain/               ← Classic chains
│   │   ├── agents/              ← Agent implementations
│   │   │   ├── agent_toolkits/  ← 30+ toolkits
│   │   │   ├── openai_tools/    ← OpenAI function calling
│   │   │   ├── tool_calling_agent/
│   │   │   └── ...
│   │   ├── chains/              ← Chain compositions
│   │   │   ├── retrieval_qa/    ← RAG chain
│   │   │   ├── conversational_retrieval/
│   │   │   ├── constitutional_ai/
│   │   │   └── ...
│   │   ├── retrievers/          ← Retrieval patterns
│   │   ├── memory/              ← Chat history
│   │   └── tools/               ← 50+ built-in tools
│   ├── langchain_v1/            ← V1 redesign
│   │   ├── agents/
│   │   │   └── middleware/      ← Agent middleware
│   │   └── ...
│   ├── partners/                ← Provider integrations
│   │   ├── openai/
│   │   ├── anthropic/
│   │   ├── groq/
│   │   ├── mistralai/
│   │   ├── ollama/
│   │   └── ...
│   ├── text-splitters/          ← Text splitting
│   └── standard-tests/          ← Testing framework
└── docs/
```

**Key Concepts:**

**Runnable Interface (LCEL):**
```python
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
result = chain.invoke("What is RAG?")
async for chunk in chain.astream("What is RAG?"):
    print(chunk)
```

**Agent Patterns:**
- Tool Calling Agent — Modern approach using function calling
- OpenAI Functions Agent — Legacy OpenAI functions
- ReAct Agent — Thought-action-observation loop
- Self-Ask — Decomposition-based reasoning
- Constitutional AI — Self-governance via principles

**Retrieval Patterns:**
- Contextual Compression — Rerank + filter documents
- Self-Query — LLM-powered metadata filtering
- Multi-Query — Generate multiple query variations
- Ensemble — Combine multiple retrievers

**Memory Patterns:**
- ChatMessageHistory — Store conversation history
- ConversationBufferMemory — Sliding window
- ConversationSummaryMemory — Summarized history
- VectorStoreMemory — Semantic retrieval of past messages

**Lessons for Aeryn:**

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Runnable Interface | Use for RAG chain composition |
| Tool Calling Agent | Already partially implemented, extend |
| Contextual Compression | Add reranker for better retrieval |
| Constitutional AI | Already have, strengthen with principles |
| Text Splitters | Use for file processing |
| Standard Tests | Adopt testing patterns |

---

#### 2. 🎓 THU-MAIC/OpenMAIC

**URL:** https://github.com/THU-MAIC/OpenMAIC  
**License:** MIT  
**Stack:** Next.js/TypeScript (2,827 files)

**Architecture:**
```
OpenMAIC/
├── app/                         ← Next.js app
│   ├── api/                     ← API routes
│   │   ├── agent/               ← Agent endpoints
│   │   ├── chat/                ← Chat endpoints
│   │   ├── classroom/           ← Classroom generation
│   │   ├── generate/            ← Content generation
│   │   ├── comfyui-workflows/   ← AI workflow integration
│   │   └── ...
│   ├── editor/                  ← Course editor
│   └── ...
├── components/                  ← UI components
├── configs/                     ← Configurations
├── hooks/                       ← React hooks
├── lib/                         ← Utilities
└── types/                       ← TypeScript types
```

**Key Concepts:**

**Multi-Agent Learning:**
- Teacher Agent — Generates course content
- Student Agent — Simulates learning
- Evaluator Agent — Assesses understanding
- Tutor Agent — Provides feedback

**Classroom Generation:**
- Input: Document → Output: Interactive course
- Multi-modal: text, video, audio
- ComfyUI integration for image generation
- Voice synthesis (Azure TTS)

**Lessons for Aeryn:**

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Multi-agent collaboration | Extend current 5 divisions |
| Classroom/course generation | New capability |
| Real-time streaming | Already have, improve |
| Multi-modal support | Add image/audio/video |

---

#### 3. 🌍 pacifio/atlas

**URL:** https://github.com/pacifio/atlas  
**License:** MIT  
**Stack:** Rust + TypeScript (4,848 files)

**Architecture:**
```
atlas/
├── crates/                      ← Rust workspace
│   ├── atlas-acp-thread/        ← Agent Communication Protocol
│   ├── atlas-agent-delta/       ← Agent state management
│   ├── atlas-agent-manager/     ← Agent lifecycle
│   ├── atlas-agent-servers/     ← Agent server runtime
│   ├── atlas-agent-store/       ← Agent persistence
│   ├── atlas-cli/               ← CLI interface
│   ├── atlas-gateway/           ← Gateway/routing
│   ├── atlas-model/             ← Model definitions
│   ├── atlas-tools/             ← Tool system
│   └── ...
├── src/                         ← TypeScript frontend
│   ├── components/
│   ├── hooks/
│   ├── stores/
│   └── ...
├── landing/                     ← Marketing site
└── docs/
```

**Key Concepts:**

**ACP (Agent Communication Protocol):**
- Standardized agent-to-agent communication
- Thread-based conversations
- Multi-agent collaboration
- Protocol-first design

**Agent Management:**
- Agent Manager — Start/stop/monitor agents
- Agent Store — Persist agent state
- Agent Delta — Incremental state updates
- Agent Servers — Runtime environment

**Lessons for Aeryn:**

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Agent Communication Protocol | Define standard for inter-agent messaging |
| Agent lifecycle management | Add start/healthcheck/restart |
| Tool sandboxing | Already have, strengthen |
| Rust performance | Consider for hot paths |

---

#### 4. 🏛️ deeplethe/utopia

**URL:** https://github.com/deeplethe/utopia  
**License:** Apache-2.0  
**Stack:** Rust + TypeScript (236 files)

**Architecture:**
```
utopia/
├── crates/                      ← Rust workspace
│   ├── utopia-core/             ← Core engine
│   ├── utopia-graph/            ← Graph-based RAG
│   ├── utopia-llm/              ← LLM abstraction
│   ├── utopia-mcp/              ← MCP connectors
│   ├── utopia-ingest/           ← Data ingestion
│   ├── utopia-connectors/       ← External connectors
│   ├── utopia-extract/          ← Data extraction
│   └── ...
├── web/                         ← TypeScript frontend
└── docs/
```

**Key Concepts:**

**Graph-Based RAG:**
- Knowledge graph construction
- Graph traversal for retrieval
- Entity relationship extraction
- Graph embeddings

**MCP (Model Context Protocol):**
- Standardized tool/resource/prompt access
- Client-server architecture
- Dynamic capability discovery
- Sandboxed execution

**Lessons for Aeryn:**

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Graph-based RAG | Add knowledge graph layer |
| MCP connectors | Implement MCP server/client |
| Incremental ingestion | Add file watching |
| Rust performance | Reference for optimization |

---

#### 5. 🏗️ tt-a1i/archify

**URL:** https://github.com/tt-a1i/archify  
**License:** MIT  
**Stack:** Node.js (468 files)

**Architecture:**
```
archify/
├── archify/                     ← Core library
│   ├── bin/                     ← CLI entry
│   ├── renderers/               ← Renderer implementations
│   │   ├── architecture/        ← Architecture diagrams
│   │   ├── dataflow/            ← Data flow diagrams
│   │   ├── lifecycle/           ← Lifecycle diagrams
│   │   ├── sequence/            ← Sequence diagrams
│   │   └── workflow/            ← Workflow diagrams
│   ├── references/              ← Reference implementations
│   ├── migrations/              ← Version migrations
│   └── recipes/                 ← Usage recipes
├── examples/                    ← Example outputs
├── generated/                   ← Generated diagrams
└── docs/
```

**Key Concepts:**

**Intermediate Representation (IR):**
- Typed JSON schema for diagrams
- Agent produces IR → Archify renders
- Deterministic compilation
- Multiple output formats (HTML, SVG, PNG)

**Lessons for Aeryn:**

| Pattern | Aeryn Implementation |
|---------|---------------------|
| IR pattern | Use for structured agent output |
| Renderer system | Pluggable output formats |
| Diagram generation | Add architecture visualization |
| Agent output validation | Validate before processing |

---

#### 6. 🤖 deepseek-ai/deepseek-harness

**URL:** https://github.com/deepseek-ai/deepseek-harness  
**License:** MIT  
**Stack:** TypeScript (8,835 files)

**Architecture:**
```
deepseek-harness/
├── .agents/                     ← Agent skills
│   ├── skills/                  ← Skill definitions
│   │   ├── dsh-code-review/
│   │   ├── dsh-doc/
│   │   ├── dsh-ci-test-reliability/
│   │   └── ...
│   └── notes/                   ← Agent notes
├── apps/                        ← Applications
├── packages/                    ← Shared packages
├── scripts/                     ← Build scripts
└── docs/
```

**Key Concepts:**

**Everything-is-a-Plugin:**
- Modular architecture
- Plugin discovery
- Dynamic loading
- Versioned plugins

**Agent Skills System:**
- Composable skills
- Skill dependencies
- Skill versioning
- Skill marketplace

**Lessons for Aeryn:**

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Plugin architecture | Already have, strengthen |
| Skill system | Adopt agent skill pattern |
| Event-driven | Add event bus |
| Code review skills | Add automated review |

---

#### 7. 🔬 K-Dense-AI/scientific-agent-skills

**URL:** https://github.com/K-Dense-AI/scientific-agent-skills  
**License:** MIT  
**Stack:** Python (2,446 files)

**Architecture:**
```
scientific-agent-skills/
├── skills/                      ← 163+ skills
│   ├── adaptyv/                 ← Adaptive learning
│   ├── aeon/                    ← Time series
│   ├── anndata/                 ← Data analysis
│   ├── analytical-method-validation/
│   └── ...
├── docs/                        ← Documentation
├── tests/                       ← Test suite
└── plugin.json                  ← Plugin manifest
```

**Key Concepts:**

**Agent Skills Standard:**
```yaml
name: skill-name
description: What this skill does
version: 1.0.0
author: Author Name
dependencies:
  - package>=1.0
```

**Scientific Domains:**
- Bioinformatics
- Data analysis
- Machine learning
- Statistical modeling
- Visualization

**Lessons for Aeryn:**

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Skill YAML standard | Adopt for Aeryn skills |
| Reference implementations | Add for each skill |
| Test coverage | Mandatory for skills |
| Scientific domains | Add research capabilities |

---

#### 8. ⚡ obra/superpowers

**URL:** https://github.com/obra/superpowers  
**License:** MIT  
**Stack:** Multi-language (194 files)

**Architecture:**
```
superpowers/
├── .claude-plugin/              ← Claude Code plugin
├── .codex-plugin/               ← Codex plugin
├── .cursor-plugin/              ← Cursor plugin
├── .devin-plugin/               ← Devin plugin
├── .hermes-plugin/              ← Hermes plugin
├── .kimi-plugin/                ← Kimi plugin
├── .opencode/                   ← OpenCode plugin
├── .pi/                         ← Pi plugin
├── docs/                        ← Documentation
├── hooks/                       ← Git hooks
└── skills/                      ← Skill implementations
```

**Key Concepts:**

**Composable Skills:**
- Small, focused skills
- Skills compose together
- Clear dependencies
- Testable in isolation

**Multi-Platform Support:**
- Claude Code, Codex, Cursor, Devin, Gemini CLI
- GitHub Copilot, Grok Build, Hermes, Kimi, OpenCode, Pi

**Lessons for Aeryn:**

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Composable skills | Design skills as building blocks |
| Multi-platform | Make Aeryn agent-agnostic |
| Skill testing | Mandatory test per skill |
| Plugin manifest | Standard plugin metadata |

---

#### 9. 🏢 lobehub/lobehub

**URL:** https://github.com/lobehub/lobehub  
**License:** AGPL-3.0  
**Stack:** Next.js/TypeScript (15,774 files)

**Architecture:**
```
lobehub/
├── apps/
│   ├── desktop/                 ← Electron app
│   ├── cli/                     ← CLI tool
│   └── server/                  ← Backend (Hono)
├── packages/
│   ├── database/                ← Drizzle ORM
│   ├── agent-runtime/           ← Agent runtime
│   ├── locales/                 ← i18n
│   └── ...
├── src/
│   ├── app/                     ← Next.js app
│   ├── routes/                  ← SPA routes
│   ├── features/                ← Feature modules
│   ├── store/                   ← Zustand stores
│   └── services/                ← API services
├── docs/
└── e2e/                         ← E2E tests
```

**Key Concepts:**

**Agent Runtime:**
- Multi-model support
- Tool calling
- Streaming responses
- Session management

**Plugin Marketplace:**
- Agent plugins
- Model providers
- Tool integrations
- Theme customization

**Database Layer:**
- Drizzle ORM
- PostgreSQL
- Migration system
- Repository pattern

**Lessons for Aeryn:**

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Agent runtime | Similar to Aeryn's divisions |
| Plugin marketplace | Add provider marketplace |
| Multi-modal | Extend beyond text |
| Drizzle ORM | Consider for migrations |

---

#### 10. 🛠️ langgenius/dify

**URL:** https://github.com/langgenius/dify  
**License:** Apache-2.0 (with CLA)  
**Stack:** Python + Next.js (13,656 files)

**Architecture:**
```
dify/
├── api/                         ← Python backend
│   ├── app.py                   ← Flask app
│   ├── app_factory.py           ← App factory
│   ├── controllers/             ← API controllers
│   ├── services/                ← Business logic
│   ├── models/                  ← Database models
│   ├── extensions/              ← Extensions
│   ├── tasks/                   ← Background tasks
│   └── ...
├── web/                         ← Next.js frontend
│   ├── app/                     ← Pages
│   ├── components/              ← UI components
│   ├── hooks/                   ← React hooks
│   ├── stores/                  ← State management
│   └── ...
├── docker/                      ← Docker configs
├── docs/                        └── ...
└── sdks/                        ← Client SDKs
```

**Key Concepts:**

**LLM Workflow Engine:**
- Visual workflow builder
- Node-based editing
- Conditional loops
- Parallel execution

**RAG Pipeline:**
- Document processing
- Chunking strategies
- Vector indexing
- Retrieval configuration

**Agent Tools:**
- Built-in tools
- Custom tools
- Tool marketplace
- Tool testing

**Multi-Tenancy:**
- Workspace isolation
- Member management
- Role-based access
- API rate limiting

**Lessons for Aeryn:**

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Visual workflow | Consider for complex RAG |
| Node-based editing | For advanced users |
| Tool marketplace | Already have plugins |
| Multi-tenancy | Add workspace isolation |

---

### 🎯 Integrated Recommendations

**Priority 1: Adopt LangChain Patterns**

| Pattern | Implementation |
|---------|----------------|
| Runnable Interface | `aeryn_core/rag/runnables.py` |
| Text Splitters | `aeryn_core/processor/splitter.py` |
| Vector Store Interface | `aeryn_core/vector_store/base.py` |
| Agent Middleware | `aeryn_core/agents/middleware.py` |
| Constitutional AI | Strengthen existing |

**Priority 2: Plugin & Skill System**

| Pattern | Source | Implementation |
|---------|--------|----------------|
| Skill YAML | scientific-agent-skills | `plugins/*/skill.yaml` |
| Plugin Manifest | superpowers | `plugins/*/plugin.json` |
| Plugin Discovery | deepseek-harness | Auto-discovery |
| Skill Testing | superpowers | Mandatory tests |

**Priority 3: Graph RAG & MCP**

| Pattern | Source | Implementation |
|---------|--------|----------------|
| Graph RAG | utopia | `aeryn_core/graph/` |
| MCP Server | utopia | MCP protocol |
| MCP Client | utopia | Tool discovery |
| Connectors | utopia | External data |

**Priority 4: Multi-Agent & Observability**

| Pattern | Source | Implementation |
|---------|--------|----------------|
| Agent Protocol | atlas | Inter-agent messaging |
| Agent Runtime | lobehub | Lifecycle management |
| Langfuse | langchain | Tracing & observability |
| Workflow Engine | dify | Visual RAG builder |

---

### 📋 Updated Implementation Roadmap

**Phase 1: LangChain Integration (2 weeks)**
- [ ] Add Runnable interface for RAG chains
- [ ] Implement text splitters (recursive, token-based)
- [ ] Create vector store abstraction
- [ ] Add agent middleware support
- [ ] Strengthen Constitutional AI

**Phase 2: Plugin & Skill System (1 week)**
- [ ] Define skill YAML schema
- [ ] Create plugin manifest format
- [ ] Implement plugin discovery
- [ ] Add skill testing framework
- [ ] Document skill authoring guide

**Phase 3: Graph RAG & MCP (2 weeks)**
- [ ] Implement graph-based RAG
- [ ] Create MCP server
- [ ] Add MCP client
- [ ] Build connector framework
- [ ] Add incremental ingestion

**Phase 4: Multi-Agent & Observability (1 week)**
- [ ] Define agent communication protocol
- [ ] Implement agent lifecycle management
- [ ] Add Langfuse integration
- [ ] Create workflow visualization
- [ ] Add analytics dashboard

**Phase 5: Advanced Features (2 weeks)**
- [ ] Multi-modal support (image, audio)
- [ ] Visual workflow builder
- [ ] Plugin marketplace
- [ ] Multi-tenancy improvements
- [ ] Performance optimization

---

### 🔗 Quick Reference

| Need | Best Source | Why |
|------|-------------|-----|
| RAG patterns | langchain | Most comprehensive |
| Agent skills | superpowers | Composable, tested |
| Plugin system | deepseek-harness | Everything-is-a-plugin |
| Graph RAG | utopia | Knowledge graphs |
| MCP | utopia | Standard protocol |
| Multi-agent | atlas | ACP protocol |
| Scientific | scientific-agent-skills | 163+ skills |
| Frontend | lobehub | Modern, clean UI |
| Workflow | dify | Visual builder |
| Visualization | archify | IR + rendering |

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
