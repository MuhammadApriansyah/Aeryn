# 🛣️ Pengembangan Aeryn: Arah & Roadmap

> Aeryn dibangun dari integrasi 11 repository open-source terbaik. Bukan sekadar referensi — tapi fondasi kode nyata.

---

## 📊 Sumber Pengembangan

| # | Repository | Stack | Peran di Aeryn |
|---|------------|-------|----------------|
| 1 | **Quivr** | Python | Brain class, RAG engine, processor registry |
| 2 | **LangChain** | Python | Runnable interface, agent patterns, text splitters |
| 3 | **OpenMAIC** | Next.js/TS | Multi-agent orchestration, classroom generation |
| 4 | **Atlas** | Rust/TS | Agent Communication Protocol, lifecycle management |
| 5 | **Utopia** | Rust/TS | Graph-based RAG, MCP connectors |
| 6 | **Archify** | Node.js | IR rendering, architecture visualization |
| 7 | **DeepSeek Harness** | TS | Plugin architecture, agent skills |
| 8 | **Scientific Agent Skills** | Python | 163+ skills, YAML standard |
| 9 | **Superpowers** | Multi | Composable skills, multi-platform |
| 10 | **LobeHub** | Next.js/TS | Agent marketplace, multi-model chat |
| 11 | **Dify** | Python/TS | Workflow engine, RAG pipeline |

---

## 🎯 Arsitektur Target: Aeryn v2

```
┌─────────────────────────────────────────────────────────────────┐
│                     AERYN v2 PLATFORM                           │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React SPA)         │  API Gateway (FastAPI)          │
│  - Dashboard                  │  - /v1/brain, /v1/chat          │
│  - Brain Manager (Quivr)      │  - /v1/files, /v1/search        │
│  - Agent Marketplace (LobeHub)│  - /v1/agents, /v1/workflow     │
│  - Workflow Builder (Dify)    │  - /v1/analytics, /v1/mcp       │
│  - Visualization (Archify)    │  - /v1/skills, /v1/classroom    │
├─────────────────────────────────────────────────────────────────┤
│                        CORE ENGINE                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Brain    │ │ RAG      │ │ LLM      │ │ File     │           │
│  │ (Quivr)  │ │ (LangCh.)│ │ (Multi)  │ │ (Quivr)  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Vector   │ │ Graph    │ │ Agent    │ │ Plugin   │           │
│  │ (PGVect) │ │ (Utopia) │ │ (Atlas)  │ │ (DSH)    │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ MCP      │ │ Workflow │ │ Skills   │ │ Multi-   │           │
│  │ (Utopia) │ │ (Dify)   │ │ (SciAg)  │ │ Agent    │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
├─────────────────────────────────────────────────────────────────┤
│              Infrastructure (PostgreSQL, Redis, PM2)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📅 Roadmap: 8 Fase Development

---

### 🔵 Fase 1: Brain & RAG Engine (dari Quivr + LangChain)

**Sumber:** Quivr `brain/`, LangChain `rags/`, `text_splitters/`

#### 1.1 Brain Class (dari Quivr)
```python
# Diadaptasi dari: quivr_core/brain/brain.py

class Brain:
    """Knowledge container — inti dari Aeryn."""
    
    def __init__(self, name, llm, vector_db, embedder, storage):
        self.id = uuid4()
        self.name = name
        self.llm = llm                    # LLMEndpoint
        self.vector_db = vector_db        # VectorStore
        self.embedder = embedder          # Embeddings
        self.storage = storage            # StorageBase
        self.chat_history = ChatHistory()
    
    @classmethod
    async def from_files(cls, name, file_paths, **kwargs):
        """Buat brain dari file paths."""
        # 1. Load files ke storage
        # 2. Process files (processor registry)
        # 3. Split text (text splitters)
        # 4. Embed chunks
        # 5. Store ke vector db
    
    async def asearch(self, query, n_results=5):
        """Cari dokumen relevan."""
    
    async def ask_streaming(self, question):
        """Tanya dengan streaming."""
    
    async def save(self, folder_path):
        """Simpan state ke folder."""
    
    @classmethod
    def load(cls, folder_path):
        """Load state dari folder."""
```

#### 1.2 RAG Pipeline (dari LangChain)
```python
# Diadaptasi dari: langchain_core/runnables

class AerynRAG:
    """RAG chain dengan LangChain Runnable interface."""
    
    def build_chain(self):
        """Build chain: Question → Retrieve → Prompt → LLM → Answer"""
        chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        return chain
    
    def with_reranker(self, reranker):
        """Tambah contextual compression."""
        self.retriever = ContextualCompressionRetriever(
            base_compressor=reranker,
            base_retriever=self.retriever
        )
```

#### 1.3 Text Splitters (dari LangChain)
```python
# Diadaptasi dari: langchain_text_splitters

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    MarkdownHeaderTextSplitter,
)

class SplitterFactory:
    @staticmethod
    def create(file_extension, **kwargs):
        if file_extension in [".md", ".markdown"]:
            return MarkdownHeaderTextSplitter(**kwargs)
        elif file_extension in [".py", ".js", ".ts"]:
            return TokenTextSplitter(**kwargs)
        else:
            return RecursiveCharacterTextSplitter(**kwargs)
```

#### 1.4 Processor Registry (dari Quivr)
```python
# Diadaptasi dari: quivr_core/processor/registry.py

class ProcessorRegistry:
    """Auto-discovery untuk file processors."""
    
    _processors: Dict[str, Type[BaseProcessor]] = {}
    
    @classmethod
    def register(cls, file_extensions: List[str]):
        def decorator(processor_cls):
            for ext in file_extensions:
                cls._processors[ext] = processor_cls
            return processor_cls
        return decorator
    
    @classmethod
    def get_processor(cls, file_extension: str) -> BaseProcessor:
        return cls._processors.get(file_extension, DefaultProcessor)()
```

**Files:**
```
aeryn_core/brain/
    __init__.py
    brain.py              ← Dari Quivr
    brain_manager.py      ← CRUD operations
    brain_serialization.py ← Save/load
    brain_info.py         ← Metadata models
    chat_history.py       ← Dari Quivr

aeryn_core/rag/
    __init__.py
    aeryn_rag.py          ← Dari LangChain
    rag_config.py         ← RetrievalConfig
    rag_models.py         ← Response models
    rag_prompts.py        ← Template prompts
    runnables.py          ← Dari LangChain LCEL

aeryn_core/processor/
    __init__.py
    base.py               ← BaseProcessor
    registry.py           ← Dari Quivr
    splitter.py           ← Dari LangChain text_splitters
    implementations/
        __init__.py
        text.py           ← .txt, .md, .csv
        pdf.py            ← PDF (PyMuPDF)
        docx.py           ← DOCX (python-docx)
        epub.py           ← EPUB (ebooklib)
        odt.py            ← ODT (odfpy)
        tika.py           ← Apache Tika fallback
```

---

### 🟢 Fase 2: Multi-Agent System (dari OpenMAIC + Atlas)

**Sumber:** OpenMAIC `app/api/agent/`, Atlas `crates/atlas-agent-*/`

#### 2.1 Agent Communication Protocol (dari Atlas)
```python
# Diadaptasi dari: atlas-acp-thread

class ACPMessage:
    """Agent Communication Protocol message."""
    sender: str
    receiver: str
    thread_id: str
    content: str
    metadata: Dict[str, Any]

class AgentThread:
    """Thread-based agent conversation."""
    
    def __init__(self, thread_id: str):
        self.thread_id = thread_id
        self.messages: List[ACPMessage] = []
    
    async def send(self, message: ACPMessage):
        """Kirim message ke thread."""
    
    async def receive(self) -> ACPMessage:
        """Terima message dari thread."""
```

#### 2.2 Agent Lifecycle (dari Atlas)
```python
# Diadaptasi dari: atlas-agent-manager

class AgentManager:
    """Start/stop/monitor agents."""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
    
    async def start_agent(self, agent_id: str, config: AgentConfig):
        """Start agent dengan config."""
    
    async def stop_agent(self, agent_id: str):
        """Stop agent."""
    
    async def health_check(self, agent_id: str) -> bool:
        """Cek health agent."""
    
    async def restart_agent(self, agent_id: str):
        """Restart agent."""
```

#### 2.3 Multi-Agent Orchestration (dari OpenMAIC)
```python
# Diadaptasi dari: OpenMAIC app/api/agent/

class MultiAgentOrchestrator:
    """Orchestrate multiple agents."""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
    
    async def execute_sequential(self, tasks: List[AgentTask]):
        """Execute agents sequentially."""
        results = []
        for task in tasks:
            agent = self.agents[task.agent_id]
            result = await agent.execute(task)
            results.append(result)
        return results
    
    async def execute_parallel(self, tasks: List[AgentTask]):
        """Execute agents in parallel."""
        return await asyncio.gather(*[
            self.agents[task.agent_id].execute(task)
            for task in tasks
        ])
    
    async def classroom_generation(self, document: str):
        """Generate classroom dari document (OpenMAIC pattern)."""
        teacher = self.agents["teacher"]
        student = self.agents["student"]
        evaluator = self.agents["evaluator"]
        
        # Teacher generates content
        content = await teacher.generate(document)
        # Student learns
        understanding = await student.learn(content)
        # Evaluator assesses
        assessment = await evaluator.assess(understanding)
        
        return {"content": content, "understanding": understanding, "assessment": assessment}
```

**Files:**
```
aeryn_core/agents/
    __init__.py
    agent_base.py         ← Base agent class
    agent_manager.py      ← Dari Atlas
    agent_protocol.py     ← Dari Atlas ACP
    orchestrator.py       ← Dari OpenMAIC
    divisions/
        __init__.py
        creative.py       ← Creative division
        reasoning.py      ← Reasoning division
        governance.py     ← Governance division
        infra.py          ← Infrastructure division
        psych.py          ← Psychology division
```

---

### 🟡 Fase 3: Graph RAG & MCP (dari Utopia)

**Sumber:** Utopia `crates/utopia-graph/`, `crates/utopia-mcp/`

#### 3.1 Graph-Based RAG (dari Utopia)
```python
# Diadaptasi dari: utopia-graph

class GraphRAG:
    """Knowledge graph untuk retrieval."""
    
    def __init__(self, graph_store, embedder):
        self.graph = graph_store
        self.embedder = embedder
    
    async def build_graph(self, documents: List[Document]):
        """Build knowledge graph dari documents."""
        # 1. Extract entities
        # 2. Extract relationships
        # 3. Create graph nodes/edges
        # 4. Generate graph embeddings
    
    async def traverse(self, query: str, depth: int = 3):
        """Traverse graph untuk retrieval."""
        # 1. Find starting nodes
        # 2. Traverse edges
        # 3. Return relevant subgraph
    
    async def hybrid_search(self, query: str):
        """Combine vector + graph search."""
        vector_results = await self.vector_search(query)
        graph_results = await self.traverse(query)
        return self.merge_results(vector_results, graph_results)
```

#### 3.2 MCP Server/Client (dari Utopia)
```python
# Diadaptasi dari: utopia-mcp

class MCPServer:
    """Model Context Protocol server."""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self.prompts: Dict[str, Prompt] = {}
    
    def register_tool(self, name: str, handler: Callable):
        """Register tool."""
    
    def register_resource(self, uri: str, handler: Callable):
        """Register resource."""
    
    def register_prompt(self, name: str, handler: Callable):
        """Register prompt."""
    
    async def handle_request(self, request: MCPRequest):
        """Handle MCP request."""

class MCPClient:
    """Model Context Protocol client."""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.tools: Dict[str, Tool] = {}
    
    async def discover(self):
        """Discover server capabilities."""
        self.tools = await self.request("tools/list")
        self.resources = await self.request("resources/list")
        self.prompts = await self.request("prompts/list")
    
    async def call_tool(self, name: str, arguments: Dict):
        """Call remote tool."""
```

**Files:**
```
aeryn_core/graph/
    __init__.py
    graph_rag.py          ← Dari Utopia
    graph_store.py        ← Graph storage backend
    entity_extractor.py   ← Entity extraction
    relationship_extractor.py ← Relationship extraction

aeryn_core/mcp/
    __init__.py
    server.py             ← Dari Utopia
    client.py             ← Dari Utopia
    types.py              ← MCP types
    connectors/
        __init__.py
        database.py       ← Database connector
        api.py            ← API connector
        filesystem.py     ← Filesystem connector
```

---

### 🟠 Fase 4: Plugin & Skill System (dari DeepSeek Harness + Scientific Agent Skills + Superpowers)

**Sumber:** DeepSeek Harness `.agents/skills/`, Scientific Agent Skills `skills/`, Superpowers `.claude-plugin/`

#### 4.1 Plugin Architecture (dari DeepSeek Harness)
```python
# Diadaptasi dari: deepseek-harness everything-is-a-plugin

class PluginManager:
    """Plugin discovery dan loading."""
    
    def __init__(self, plugin_dirs: List[str]):
        self.plugin_dirs = plugin_dirs
        self.plugins: Dict[str, Plugin] = {}
    
    def discover(self):
        """Discover plugins dari directories."""
        for plugin_dir in self.plugin_dirs:
            for plugin_path in Path(plugin_dir).glob("*/plugin.json"):
                self.load_plugin(plugin_path)
    
    def load_plugin(self, manifest_path: Path):
        """Load plugin dari manifest."""
        manifest = json.loads(manifest_path.read_text())
        plugin = Plugin.from_manifest(manifest)
        self.plugins[plugin.name] = plugin
    
    def get_plugin(self, name: str) -> Plugin:
        """Get plugin by name."""
```

#### 4.2 Skill YAML Standard (dari Scientific Agent Skills)
```yaml
# Diadaptasi dari: scientific-agent-skills plugin.json
name: skill-name
description: What this skill does
version: 1.0.0
author: Author Name
license: MIT
dependencies:
  - package>=1.0
entry_point: skills/skill_name/
tests:
  - tests/test_skill_name.py
```

```python
class SkillLoader:
    """Load skills dari YAML manifest."""
    
    def __init__(self, skills_dir: str):
        self.skills_dir = skills_dir
        self.skills: Dict[str, Skill] = {}
    
    def load_all(self):
        """Load all skills."""
        for skill_path in Path(self.skills_dir).glob("*/skill.yaml"):
            self.load_skill(skill_path)
    
    def load_skill(self, manifest_path: Path):
        """Load single skill."""
        manifest = yaml.safe_load(manifest_path.read_text())
        skill = Skill.from_manifest(manifest)
        self.skills[skill.name] = skill
```

#### 4.3 Composable Skills (dari Superpowers)
```python
# Diadaptasi dari: superpowers composable skills

class Skill:
    """Composable skill."""
    
    def __init__(self, name: str, description: str, dependencies: List[str]):
        self.name = name
        self.description = description
        self.dependencies = dependencies
        self.tests: List[TestCase] = []
    
    def compose(self, other: 'Skill') -> 'Skill':
        """Compose two skills together."""
        return Skill(
            name=f"{self.name}+{other.name}",
            description=f"{self.description} + {other.description}",
            dependencies=self.dependencies + other.dependencies
        )
    
    def test(self) -> TestResult:
        """Run skill tests."""
        return TestResult(passed=all(t.run() for t in self.tests))
```

**Files:**
```
aeryn_core/plugins/
    __init__.py
    plugin_base.py        ← Base plugin class
    plugin_manager.py     ← Dari DeepSeek Harness
    plugin_loader.py      ← Plugin loading
    skill_loader.py       ← Dari Scientific Agent Skills
    skill_yaml.py         ← YAML schema
    composable.py         ← Dari Superpowers
    tests/
        __init__.py
        test_plugin.py
        test_skill.py

plugins/                  ← Plugin directory
    code-review/
        plugin.json       ← Dari DeepSeek Harness
        skill.yaml        ← Dari Scientific Agent Skills
        __init__.py
        main.py
        tests/
            test_main.py
    scientific-research/
        plugin.json
        skill.yaml
        __init__.py
        main.py
    web-search/
        plugin.json
        skill.yaml
        __init__.py
        main.py
```

---

### 🔴 Fase 5: Workflow Engine (dari Dify)

**Sumber:** Dify `api/controllers/`, `api/services/`

#### 5.1 Workflow Builder (dari Dify)
```python
# Diadaptasi dari: dify api/services/workflow_service.py

class WorkflowEngine:
    """Visual workflow builder."""
    
    def __init__(self):
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: List[WorkflowEdge] = []
    
    def add_node(self, node_id: str, node_type: str, config: Dict):
        """Add node ke workflow."""
        self.nodes[node_id] = WorkflowNode(node_id, node_type, config)
    
    def add_edge(self, source: str, target: str, condition: str = None):
        """Add edge antara nodes."""
        self.edges.append(WorkflowEdge(source, target, condition))
    
    async def execute(self, input_data: Dict) -> Dict:
        """Execute workflow."""
        # 1. Find start nodes
        # 2. Execute nodes in order
        # 3. Handle conditions
        # 4. Return output
    
    async def execute_node(self, node_id: str, input_data: Dict) -> Dict:
        """Execute single node."""
        node = self.nodes[node_id]
        if node.type == "llm":
            return await self.execute_llm_node(node, input_data)
        elif node.type == "retrieval":
            return await self.execute_retrieval_node(node, input_data)
        elif node.type == "tool":
            return await self.execute_tool_node(node, input_data)
        elif node.type == "condition":
            return await self.execute_condition_node(node, input_data)
```

#### 5.2 Workflow Nodes (dari Dify)
```python
class WorkflowNode:
    """Base workflow node."""
    
    def __init__(self, node_id: str, node_type: str, config: Dict):
        self.node_id = node_id
        self.node_type = node_type
        self.config = config
    
    async def execute(self, input_data: Dict) -> Dict:
        """Execute node."""

class LLMNode(WorkflowNode):
    """LLM processing node."""
    
    async def execute(self, input_data: Dict) -> Dict:
        prompt = self.config["prompt"].format(**input_data)
        response = await self.llm.invoke(prompt)
        return {"output": response}

class RetrievalNode(WorkflowNode):
    """Document retrieval node."""
    
    async def execute(self, input_data: Dict) -> Dict:
        query = input_data["query"]
        results = await self.vector_db.asimilarity_search(query)
        return {"documents": results}

class ToolNode(WorkflowNode):
    """Tool execution node."""
    
    async def execute(self, input_data: Dict) -> Dict:
        tool_name = self.config["tool"]
        tool = self.plugin_manager.get_plugin(tool_name)
        result = await tool.execute(input_data)
        return {"output": result}
```

**Files:**
```
aeryn_core/workflow/
    __init__.py
    engine.py             ← Dari Dify
    nodes.py              ← Workflow nodes
    edges.py              ← Workflow edges
    builder.py            ← Visual builder API
    executor.py           ← Workflow execution
    conditions.py         ← Conditional logic
    templates/            ← Workflow templates
        __init__.py
        rag_qa.py         ← RAG QA workflow
        multi_agent.py    ← Multi-agent workflow
        research.py       ← Research workflow
```

---

### 🟣 Fase 6: Frontend & Visualization (dari LobeHub + Archify)

**Sumber:** LobeHub `src/routes/`, Archify `archify/renderers/`

#### 6.1 Agent Marketplace UI (dari LobeHub)
```typescript
// Diadaptasi dari: lobehub src/routes/

// Brain List Page
const BrainListPage: React.FC = () => {
    const brains = useBrains();
    return (
        <Grid>
            {brains.map(brain => (
                <BrainCard
                    key={brain.id}
                    name={brain.name}
                    fileCount={brain.files.length}
                    chatCount={brain.chats.length}
                    onSelect={() => navigate(`/brain/${brain.id}`)}
                />
            ))}
        </Grid>
    );
};

// Brain Detail Page
const BrainDetailPage: React.FC<{ brainId: string }> = ({ brainId }) => {
    const brain = useBrain(brainId);
    return (
        <Layout>
            <Sidebar>
                <FileList files={brain.files} />
                <ChatHistory chats={brain.chats} />
            </Sidebar>
            <Main>
                <ChatWindow brainId={brainId} />
            </Main>
        </Layout>
    );
};
```

#### 6.2 Workflow Builder UI (dari Dify)
```typescript
// Diadaptasi dari: dify web/app/components/workflow/

const WorkflowBuilder: React.FC = () => {
    const [nodes, setNodes] = useState<WorkflowNode[]>([]);
    const [edges, setEdges] = useState<WorkflowEdge[]>([]);
    
    return (
        <ReactFlow>
            {nodes.map(node => (
                <WorkflowNodeComponent key={node.id} node={node} />
            ))}
        </ReactFlow>
    );
};
```

#### 6.3 Architecture Visualization (dari Archify)
```typescript
// Diadaptasi dari: archify renderers/

interface DiagramIR {
    type: "architecture" | "dataflow" | "sequence" | "workflow";
    nodes: DiagramNode[];
    edges: DiagramEdge[];
    metadata: Record<string, any>;
}

const ArchitectureDiagram: React.FC<{ ir: DiagramIR }> = ({ ir }) => {
    // Render IR ke SVG/HTML
    return <SVGRenderer ir={ir} />;
};
```

**Files:**
```
apps/web/src/
    pages/
        Dashboard.tsx          ← Main dashboard
        BrainList.tsx          ← Dari LobeHub pattern
        BrainDetail.tsx        ← Dari LobeHub pattern
        Chat.tsx               ← Chat interface
        WorkflowBuilder.tsx    ← Dari Dify pattern
        AgentMarketplace.tsx   ← Dari LobeHub pattern
        Analytics.tsx          ← Usage analytics
    
    components/
        brain/
            BrainCard.tsx
            BrainWizard.tsx
            FileUploader.tsx
        chat/
            ChatWindow.tsx
            MessageBubble.tsx
            StreamingText.tsx
            SourceCitation.tsx
        workflow/
            WorkflowCanvas.tsx  ← Dari Dify
            NodePalette.tsx
            NodeConfig.tsx
        visualization/
            ArchitectureDiagram.tsx ← Dari Archify
            DataFlowDiagram.tsx
            SequenceDiagram.tsx
        marketplace/
            AgentCard.tsx       ← Dari LobeHub
            ProviderCard.tsx
            ToolCard.tsx
    
    hooks/
        useBrains.ts
        useBrain.ts
        useChat.ts
        useWorkflow.ts
        useAgents.ts
    
    stores/
        brainStore.ts           ← Zustand (dari LobeHub)
        chatStore.ts
        workflowStore.ts
        agentStore.ts
```

---

### ⚫ Fase 7: Observability & Analytics (dari LangChain + LobeHub)

**Sumber:** LangChain `langchain_core/tracers/`, LobeHub `packages/database/`

#### 7.1 Langfuse Integration (dari LangChain)
```python
# Diadaptasi dari: langchain_core/tracers

class AerynTracer:
    """Trace agent execution."""
    
    def __init__(self, langfuse_config: Optional[Dict] = None):
        if langfuse_config:
            self.langfuse = Langfuse(**langfuse_config)
        self.spans: List[Span] = []
    
    def start_span(self, name: str, metadata: Dict = None) -> Span:
        """Start trace span."""
        span = Span(name, metadata)
        self.spans.append(span)
        return span
    
    def end_span(self, span: Span, output: Any = None):
        """End trace span."""
        span.end(output)
    
    async def trace_agent(self, agent_id: str, task: str):
        """Trace agent execution."""
        with self.start_span(f"agent.{agent_id}", {"task": task}):
            # Execute agent
            pass
    
    async def trace_rag(self, query: str, docs: List[Document]):
        """Trace RAG pipeline."""
        with self.start_span("rag.query", {"query": query}):
            # Retrieve
            with self.start_span("rag.retrieve"):
                pass
            # Generate
            with self.start_span("rag.generate"):
                pass
```

#### 7.2 Analytics Dashboard (dari LobeHub)
```python
# Diadaptasi dari: lobehub packages/database

class AnalyticsService:
    """Usage analytics."""
    
    async def get_usage_stats(self, workspace_id: str) -> UsageStats:
        """Get usage statistics."""
        return UsageStats(
            total_requests=await self.count_requests(workspace_id),
            total_tokens=await self.sum_tokens(workspace_id),
            total_cost=await self.sum_cost(workspace_id),
            provider_breakdown=await self.get_provider_breakdown(workspace_id),
        )
    
    async def get_agent_stats(self, agent_id: str) -> AgentStats:
        """Get agent statistics."""
        return AgentStats(
            total_tasks=await self.count_tasks(agent_id),
            success_rate=await self.calculate_success_rate(agent_id),
            avg_duration=await self.calculate_avg_duration(agent_id),
        )
```

**Files:**
```
aeryn_core/observability/
    __init__.py
    tracer.py             ← Dari LangChain
    langfuse_service.py   ← Dari LangChain
    metrics.py            ← Metrics collection
    analytics.py          ← Dari LobeHub
    dashboard.py          ← Analytics dashboard API
```

---

### ⚪ Fase 8: Multi-Tenancy & Auth (dari Dify + LobeHub)

**Sumber:** Dify `api/models/`, LobeHub `src/store/`

#### 8.1 Workspace Isolation (dari Dify)
```python
# Diadaptasi dari: dify api/models/workspace

class Workspace:
    """Multi-tenant workspace."""
    
    def __init__(self, name: str, owner: str):
        self.id = uuid4()
        self.name = name
        self.owner = owner
        self.members: List[WorkspaceMember] = []
        self.brains: List[Brain] = []
        self.agents: List[Agent] = []
        self.api_keys: List[APIKey] = []
    
    def add_member(self, user_id: str, role: str):
        """Add member ke workspace."""
        self.members.append(WorkspaceMember(user_id, role))
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check user permission."""
        member = next(m for m in self.members if m.user_id == user_id)
        return permission in member.role.permissions
```

#### 8.2 API Key Management (dari Dify)
```python
class APIKeyManager:
    """API key management."""
    
    def create_api_key(self, workspace_id: str, name: str) -> str:
        """Create new API key."""
        key = f"sk-{uuid4().hex}"
        hashed = hashlib.sha256(key.encode()).hexdigest()
        # Store hashed key
        return key
    
    def validate_api_key(self, key: str) -> Optional[str]:
        """Validate API key, return workspace_id."""
        hashed = hashlib.sha256(key.encode()).hexdigest()
        # Lookup hashed key
        return workspace_id
    
    def revoke_api_key(self, workspace_id: str, key_id: str):
        """Revoke API key."""
```

**Files:**
```
aeryn_core/auth/
    __init__.py
    workspace.py          ← Dari Dify
    api_keys.py           ← Dari Dify
    permissions.py        ← Role-based access
    rate_limiter.py       ← API rate limiting
    jwt.py                ← JWT authentication
```

---

## 📋 Target Directory Structure

```
aeryn-core-agent/
├── aeryn_core/
│   ├── brain/               ← 🧠 DARI QUIVR
│   │   ├── brain.py
│   │   ├── brain_manager.py
│   │   ├── brain_serialization.py
│   │   ├── brain_info.py
│   │   └── chat_history.py
│   ├── rag/                 ← 🔍 DARI LANGCHAIN
│   │   ├── aeryn_rag.py
│   │   ├── rag_config.py
│   │   ├── rag_models.py
│   │   ├── rag_prompts.py
│   │   └── runnables.py
│   ├── processor/           ← 📄 DARI QUIVR + LANGCHAIN
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── splitter.py
│   │   └── implementations/
│   │       ├── text.py
│   │       ├── pdf.py
│   │       ├── docx.py
│   │       ├── epub.py
│   │       └── odt.py
│   ├── agents/              ← 🤖 DARI OPENMAIC + ATLAS
│   │   ├── agent_base.py
│   │   ├── agent_manager.py
│   │   ├── agent_protocol.py
│   │   ├── orchestrator.py
│   │   └── divisions/
│   │       ├── creative.py
│   │       ├── reasoning.py
│   │       ├── governance.py
│   │       ├── infra.py
│   │       └── psych.py
│   ├── graph/               ← 📊 DARI UTOPIA
│   │   ├── graph_rag.py
│   │   ├── graph_store.py
│   │   ├── entity_extractor.py
│   │   └── relationship_extractor.py
│   ├── mcp/                 ← 🔌 DARI UTOPIA
│   │   ├── server.py
│   │   ├── client.py
│   │   ├── types.py
│   │   └── connectors/
│   │       ├── database.py
│   │       ├── api.py
│   │       └── filesystem.py
│   ├── plugins/             ← 🧩 DARI DEEPSEEK HARNESS + SCIENTIFIC AGENT SKILLS + SUPERPOWERS
│   │   ├── plugin_base.py
│   │   ├── plugin_manager.py
│   │   ├── plugin_loader.py
│   │   ├── skill_loader.py
│   │   ├── skill_yaml.py
│   │   └── composable.py
│   ├── workflow/            ← 🔄 DARI DIFY
│   │   ├── engine.py
│   │   ├── nodes.py
│   │   ├── edges.py
│   │   ├── builder.py
│   │   ├── executor.py
│   │   ├── conditions.py
│   │   └── templates/
│   │       ├── rag_qa.py
│   │       ├── multi_agent.py
│   │       └── research.py
│   ├── llm/                 ← 🤖 DARI QUIVR + LANGCHAIN
│   │   ├── llm_endpoint.py
│   │   ├── llm_router.py
│   │   ├── llm_config.py
│   │   └── tokenizer.py
│   ├── vector_store/        ← 💾 DARI QUIVR + LANGCHAIN
│   │   ├── base.py
│   │   ├── pgvector_store.py
│   │   ├── faiss_store.py
│   │   └── pinecone_store.py
│   ├── storage/             ← 📁 DARI QUIVR
│   │   ├── base.py
│   │   ├── local_storage.py
│   │   ├── transparent_storage.py
│   │   └── s3_storage.py
│   ├── observability/       ← 📊 DARI LANGCHAIN + LOBEHUB
│   │   ├── tracer.py
│   │   ├── langfuse_service.py
│   │   ├── metrics.py
│   │   ├── analytics.py
│   │   └── dashboard.py
│   ├── auth/                ← 🔐 DARI DIFY + LOBEHUB
│   │   ├── workspace.py
│   │   ├── api_keys.py
│   │   ├── permissions.py
│   │   ├── rate_limiter.py
│   │   └── jwt.py
│   ├── billing/             ← 💰 DARI DIFY
│   │   ├── billing.py
│   │   └── usage_metering.py
│   ├── database/            ← 🗄️ DARI LOBEHUB
│   │   ├── db_adapter.py
│   │   ├── shared_db.py
│   │   └── migrations/
│   └── utils/               ← 🔧
│       ├── config.py
│       ├── logger.py
│       └── performance.py
├── apps/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── main.py
│   │   │   ├── brain.py
│   │   │   ├── chat.py
│   │   │   ├── files.py
│   │   │   ├── search.py
│   │   │   ├── agents.py
│   │   │   ├── workflow.py
│   │   │   ├── mcp.py
│   │   │   ├── skills.py
│   │   │   ├── analytics.py
│   │   │   ├── auth.py
│   │   │   └── admin.py
│   │   └── aeryn_api.py
│   └── web/                 ← 🌐 DARI LOBEHUB + DIFY + ARCHIFY
│       ├── src/
│       │   ├── pages/
│       │   ├── components/
│       │   │   ├── brain/
│       │   │   ├── chat/
│       │   │   ├── workflow/
│       │   │   ├── visualization/
│       │   │   └── marketplace/
│       │   ├── hooks/
│       │   ├── stores/
│       │   └── utils/
│       └── package.json
├── plugins/                 ← 🧩 PLUGIN DIRECTORY
│   ├── code-review/
│   ├── scientific-research/
│   ├── web-search/
│   └── data-analysis/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── architecture.md
│   ├── api_reference.md
│   ├── brain_guide.md
│   ├── workflow_guide.md
│   ├── plugin_guide.md
│   └── deployment.md
├── ecosystem.config.cjs
├── CHANGELOG.md
└── README.md
```

---

## 📊 Success Metrics

| Metric | Target | Source Pattern |
|--------|--------|----------------|
| **API uptime** | 99.9% | Atlas agent health check |
| **Response time** | < 500ms (p95) | LangChain Runnable |
| **RAG accuracy** | > 85% relevance | Quivr + LangChain |
| **File processing** | PDF, DOCX, EPUB, ODT | Quivr processor registry |
| **LLM providers** | 6+ providers | LangChain partners |
| **Plugin system** | Auto-discovery | DeepSeek Harness |
| **Workflow** | Visual builder | Dify |
| **Multi-tenancy** | Workspace isolation | Dify |
| **Test coverage** | > 80% | Superpowers |
| **User satisfaction** | NPS > 50 | LobeHub UX |

---

*Dokumentasi ini akan diperbarui seiring implementasi.*
*Last updated: 2026-09-02*
*Version: 2.0*
