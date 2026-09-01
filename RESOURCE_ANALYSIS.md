# 📚 Resource Analysis — 10 Repository untuk Pengembangan Aeryn

> Analisis komprehensif 10 repository open-source untuk arah pengembangan Aeryn selanjutnya.

---

## 📊 Executive Summary

| # | Repository | Type | Stack | Key Takeaway for Aeryn |
|---|------------|------|-------|----------------------|
| 1 | **langchain** | Framework | Python | RAG patterns, agent architecture, tool system |
| 2 | **OpenMAIC** | Platform | Next.js/TS | Multi-agent learning, classroom generation |
| 3 | **atlas** | Product | Rust/TS | ACP thread protocol, agent management |
| 4 | **utopia** | Framework | Rust | Graph-based RAG, MCP connectors |
| 5 | **archify** | Tool | Node.js | Architecture visualization, IR rendering |
| 6 | **deepseek-harness** | Agent | TS | Plugin architecture, agent orchestration |
| 7 | **scientific-agent-skills** | Skills | Python | 163+ scientific skills, plugin standard |
| 8 | **superpowers** | Methodology | Multi | Composable agent skills, SDLC |
| 9 | **lobehub** | Platform | Next.js/TS | Agent marketplace, multi-model chat |
| 10 | **dify** | Platform | Python/TS | LLM workflow, RAG pipeline, agent tools |

---

## 🔬 Deep Analysis

---

### 1. 🔗 langchain-ai/langchain

**URL:** https://github.com/langchain-ai/langchain  
**Stars:** ~100k+  
**License:** MIT  
**Stack:** Python (3,044 files)

#### Architecture

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

#### Key Concepts

**1. Runnable Interface (LCEL)**
```python
# Declarative chain composition
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Invoke
result = chain.invoke("What is RAG?")

# Stream
async for chunk in chain.astream("What is RAG?"):
    print(chunk)
```

**2. Agent Patterns**
- **Tool Calling Agent** — Modern approach using function calling
- **OpenAI Functions Agent** — Legacy OpenAI functions
- **ReAct Agent** — Thought-action-observation loop
- **Self-Ask** — Decomposition-based reasoning
- **Constitutional AI** — Self-governance via principles

**3. Retrieval Patterns**
- **Contextual Compression** — Rerank + filter documents
- **Self-Query** — LLM-powered metadata filtering
- **Multi-Query** — Generate multiple query variations
- **Ensemble** — Combine multiple retrievers

**4. Memory Patterns**
- **ChatMessageHistory** — Store conversation history
- **ConversationBufferMemory** — Sliding window
- **ConversationSummaryMemory** — Summarized history
- **VectorStoreMemory** — Semantic retrieval of past messages

#### Lessons for Aeryn

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Runnable Interface | Use for RAG chain composition |
| Tool Calling Agent | Already partially implemented, extend |
| Contextual Compression | Add reranker for better retrieval |
| Constitutional AI | Already have, strengthen with principles |
| Text Splitters | Use for file processing |
| Standard Tests | Adopt testing patterns |

---

### 2. 🎓 THU-MAIC/OpenMAIC

**URL:** https://github.com/THU-MAIC/OpenMAIC  
**License:** MIT  
**Stack:** Next.js/TypeScript (2,827 files)

#### Architecture

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

#### Key Concepts

**1. Multi-Agent Learning**
- **Teacher Agent** — Generates course content
- **Student Agent** — Simulates learning
- **Evaluator Agent** — Assesses understanding
- **Tutor Agent** — Provides feedback

**2. Classroom Generation**
- Input: Document → Output: Interactive course
- Multi-modal: text, video, audio
- ComfyUI integration for image generation
- Voice synthesis (Azure TTS)

**3. Agent Orchestration**
- Sequential agent execution
- Agent-to-agent communication
- Shared context/memory
- Real-time streaming

#### Lessons for Aeryn

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Multi-agent collaboration | Extend current 5 divisions |
| Classroom/course generation | New capability |
| Real-time streaming | Already have, improve |
| Multi-modal support | Add image/audio/video |

---

### 3. 🌍 pacifio/atlas

**URL:** https://github.com/pacifio/atlas  
**License:** MIT  
**Stack:** Rust + TypeScript (4,848 files)

#### Architecture

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

#### Key Concepts

**1. ACP (Agent Communication Protocol)**
- Standardized agent-to-agent communication
- Thread-based conversations
- Multi-agent collaboration
- Protocol-first design

**2. Agent Management**
- **Agent Manager** — Start/stop/monitor agents
- **Agent Store** — Persist agent state
- **Agent Delta** — Incremental state updates
- **Agent Servers** — Runtime environment

**3. Tool System**
- Tool registration
- Tool discovery
- Tool execution sandboxing
- Tool result caching

#### Lessons for Aeryn

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Agent Communication Protocol | Define standard for inter-agent messaging |
| Agent lifecycle management | Add start/healthcheck/restart |
| Tool sandboxing | Already have, strengthen |
| Rust performance | Consider for hot paths |

---

### 4. 🏛️ deeplethe/utopia

**URL:** https://github.com/deeplethe/utopia  
**License:** Apache-2.0  
**Stack:** Rust + TypeScript (236 files)

#### Architecture

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

#### Key Concepts

**1. Graph-Based RAG**
- Knowledge graph construction
- Graph traversal for retrieval
- Entity relationship extraction
- Graph embeddings

**2. MCP (Model Context Protocol)**
- Standardized tool/resource/prompt access
- Client-server architecture
- Dynamic capability discovery
- Sandboxed execution

**3. Data Ingestion**
- Multi-format support
- Incremental updates
- Change detection
- Pipeline orchestration

#### Lessons for Aeryn

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Graph-based RAG | Add knowledge graph layer |
| MCP connectors | Implement MCP server/client |
| Incremental ingestion | Add file watching |
| Rust performance | Reference for optimization |

---

### 5. 🏗️ tt-a1i/archify

**URL:** https://github.com/tt-a1i/archify  
**License:** MIT  
**Stack:** Node.js (468 files)

#### Architecture

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

#### Key Concepts

**1. Intermediate Representation (IR)**
- Typed JSON schema for diagrams
- Agent produces IR → Archify renders
- Deterministic compilation
- Multiple output formats (HTML, SVG, PNG)

**2. Renderer System**
- Pluggable renderers per diagram type
- Shared components across renderers
- Validation before rendering
- Responsive output

**3. Agent Integration**
- Cursor, Claude Code, Codex CLI
- Structured output from agents
- Deterministic rendering
- Preview in chat

#### Lessons for Aeryn

| Pattern | Aeryn Implementation |
|---------|---------------------|
| IR pattern | Use for structured agent output |
| Renderer system | Pluggable output formats |
| Diagram generation | Add architecture visualization |
| Agent output validation | Validate before processing |

---

### 6. 🤖 deepseek-ai/deepseek-harness

**URL:** https://github.com/deepseek-ai/deepseek-harness  
**License:** MIT  
**Stack:** TypeScript (8,835 files)

#### Architecture

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

#### Key Concepts

**1. Everything-is-a-Plugin**
- Modular architecture
- Plugin discovery
- Dynamic loading
- Versioned plugins

**2. Agent Skills System**
- Composable skills
- Skill dependencies
- Skill versioning
- Skill marketplace

**3. Cordis Foundation**
- Spatiotemporal composability
- Event-driven architecture
- Time-aware computations
- Distributed execution

#### Lessons for Aeryn

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Plugin architecture | Already have, strengthen |
| Skill system | Adopt agent skill pattern |
| Event-driven | Add event bus |
| Code review skills | Add automated review |

---

### 7. 🔬 K-Dense-AI/scientific-agent-skills

**URL:** https://github.com/K-Dense-AI/scientific-agent-skills  
**License:** MIT  
**Stack:** Python (2,446 files)

#### Architecture

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

#### Key Concepts

**1. Agent Skills Standard**
- YAML skill definition
- Markdown documentation
- Reference implementations
- Test coverage

**2. Skill Structure**
```yaml
name: skill-name
description: What this skill does
version: 1.0.0
author: Author Name
dependencies:
  - package>=1.0
```

**3. Scientific Domains**
- Bioinformatics
- Data analysis
- Machine learning
- Statistical modeling
- Visualization

#### Lessons for Aeryn

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Skill YAML standard | Adopt for Aeryn skills |
| Reference implementations | Add for each skill |
| Test coverage | Mandatory for skills |
| Scientific domains | Add research capabilities |

---

### 8. ⚡ obra/superpowers

**URL:** https://github.com/obra/superpowers  
**License:** MIT  
**Stack:** Multi-language (194 files)

#### Architecture

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

#### Key Concepts

**1. Composable Skills**
- Small, focused skills
- Skills compose together
- Clear dependencies
- Testable in isolation

**2. Multi-Platform Support**
- Claude Code
- Codex
- Cursor
- Devin
- Gemini CLI
- GitHub Copilot
- Grok Build
- Hermes
- Kimi
- OpenCode
- Pi

**3. Development Methodology**
- Skill-first development
- Test-driven skills
- Documentation as code
- Continuous integration

#### Lessons for Aeryn

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Composable skills | Design skills as building blocks |
| Multi-platform | Make Aeryn agent-agnostic |
| Skill testing | Mandatory test per skill |
| Plugin manifest | Standard plugin metadata |

---

### 9. 🏢 lobehub/lobehub

**URL:** https://github.com/lobehub/lobehub  
**License:** AGPL-3.0  
**Stack:** Next.js/TypeScript (15,774 files)

#### Architecture

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

#### Key Concepts

**1. Agent Runtime**
- Multi-model support
- Tool calling
- Streaming responses
- Session management

**2. Plugin Marketplace**
- Agent plugins
- Model providers
- Tool integrations
- Theme customization

**3. Multi-Modal**
- Text chat
- Voice input
- Image generation
- File upload

**4. Database Layer**
- Drizzle ORM
- PostgreSQL
- Migration system
- Repository pattern

#### Lessons for Aeryn

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Agent runtime | Similar to Aeryn's divisions |
| Plugin marketplace | Add provider marketplace |
| Multi-modal | Extend beyond text |
| Drizzle ORM | Consider for migrations |

---

### 10. 🛠️ langgenius/dify

**URL:** https://github.com/langgenius/dify  
**License:** Apache-2.0 (with CLA)  
**Stack:** Python + Next.js (13,656 files)

#### Architecture

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

#### Key Concepts

**1. LLM Workflow Engine**
- Visual workflow builder
- Node-based editing
- Conditional loops
- Parallel execution

**2. RAG Pipeline**
- Document processing
- Chunking strategies
- Vector indexing
- Retrieval configuration

**3. Agent Tools**
- Built-in tools
- Custom tools
- Tool marketplace
- Tool testing

**4. Multi-Tenancy**
- Workspace isolation
- Member management
- Role-based access
- API rate limiting

#### Lessons for Aeryn

| Pattern | Aeryn Implementation |
|---------|---------------------|
| Visual workflow | Consider for complex RAG |
| Node-based editing | For advanced users |
| Tool marketplace | Already have plugins |
| Multi-tenancy | Add workspace isolation |

---

## 🎯 Integrated Recommendations

### Priority 1: Adopt LangChain Patterns

| Pattern | Implementation |
|---------|----------------|
| Runnable Interface | `aeryn_core/rag/runnables.py` |
| Text Splitters | `aeryn_core/processor/splitter.py` |
| Vector Store Interface | `aeryn_core/vector_store/base.py` |
| Agent Middleware | `aeryn_core/agents/middleware.py` |
| Constitutional AI | Strengthen existing |

### Priority 2: Plugin & Skill System

| Pattern | Source | Implementation |
|---------|--------|----------------|
| Skill YAML | scientific-agent-skills | `plugins/*/skill.yaml` |
| Plugin Manifest | superpowers | `plugins/*/plugin.json` |
| Plugin Discovery | deepseek-harness | Auto-discovery |
| Skill Testing | superpowers | Mandatory tests |

### Priority 3: Graph RAG & MCP

| Pattern | Source | Implementation |
|---------|--------|----------------|
| Graph RAG | utopia | `aeryn_core/graph/` |
| MCP Server | utopia | MCP protocol |
| MCP Client | utopia | Tool discovery |
| Connectors | utopia | External data |

### Priority 4: Multi-Agent & Observability

| Pattern | Source | Implementation |
|---------|--------|----------------|
| Agent Protocol | atlas | Inter-agent messaging |
| Agent Runtime | lobehub | Lifecycle management |
| Langfuse | langchain | Tracing & observability |
| Workflow Engine | dify | Visual RAG builder |

---

## 📋 Implementation Roadmap

### Phase 1: LangChain Integration (2 weeks)
- [ ] Add Runnable interface for RAG chains
- [ ] Implement text splitters (recursive, token-based)
- [ ] Create vector store abstraction
- [ ] Add agent middleware support
- [ ] Strengthen Constitutional AI

### Phase 2: Plugin & Skill System (1 week)
- [ ] Define skill YAML schema
- [ ] Create plugin manifest format
- [ ] Implement plugin discovery
- [ ] Add skill testing framework
- [ ] Document skill authoring guide

### Phase 3: Graph RAG & MCP (2 weeks)
- [ ] Implement graph-based RAG
- [ ] Create MCP server
- [ ] Add MCP client
- [ ] Build connector framework
- [ ] Add incremental ingestion

### Phase 4: Multi-Agent & Observability (1 week)
- [ ] Define agent communication protocol
- [ ] Implement agent lifecycle management
- [ ] Add Langfuse integration
- [ ] Create workflow visualization
- [ ] Add analytics dashboard

### Phase 5: Advanced Features (2 weeks)
- [ ] Multi-modal support (image, audio)
- [ ] Visual workflow builder
- [ ] Plugin marketplace
- [ ] Multi-tenancy improvements
- [ ] Performance optimization

---

## 🔗 Quick Reference

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

---

*Dokumentasi ini akan diperbarui seiring implementasi.*
*Last updated: 2026-09-02*
*Version: 1.0*
