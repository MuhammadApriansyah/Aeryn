# 🚀 Aeryn v2 — Development Phase Documentation

> Detailed development roadmap with task breakdown, acceptance criteria, and estimates.
> Version: 2.0
> Last Updated: 2026-09-02

---

## Current Status

| Aspect | Status |
|--------|--------|
| Infrastructure | ✅ Complete (FastAPI, PM2, deployment) |
| HTTP Endpoints | ✅ 200+ endpoints, all tested |
| Rust Engine | ✅ 6 C API functions working |
| Agent Core | ❌ Not started |
| LLM Integration | ❌ Not started |
| Tool System | ❌ Not started |
| Frontend Chat | ❌ Not started |

---

## Phase 1: Agent Core (1-2 weeks)

> Build the fundamental agent loop: LLM → Tool → Response.

### 1.1 LLM Client

**Goal:** Connect to LLM providers (OpenAI, Anthropic, local).

| Task | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| Provider abstraction | `LLMClient` class with `chat()` method | Can switch providers via config | 4 |
| OpenAI integration | `OpenAIClient(LLMClient)` | GPT-4o works | 3 |
| Anthropic integration | `AnthropicClient(LLMClient)` | Claude works | 3 |
| Local LLM support | `LocalLLMClient(LLMClient)` | Ollama/local works | 4 |
| Streaming | `chat_stream()` yields tokens | Real-time token stream | 4 |
| Retry & backoff | Auto-retry on 429/500 | 3 retries with exponential backoff | 2 |
| Token counting | Count tokens for context management | Accurate count | 2 |

**Files:**
- `aeryn_core/llm/client.py` — Base LLMClient
- `aeryn_core/llm/openai_client.py`
- `aeryn_core/llm/anthropic_client.py`
- `aeryn_core/llm/local_client.py`
- `aeryn_core/llm/token_counter.py`

**Test:**
```python
client = LLMClient.from_config()
response = client.chat([
    {"role": "system", "content": "You are Aeryn."},
    {"role": "user", "content": "Hello!"}
])
assert len(response) > 0
```

---

### 1.2 Tool Registry

**Goal:** Dynamic tool registration and invocation.

| Task | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| Tool schema | JSON Schema for tool definition | Valid schema | 2 |
| Tool registry | `ToolRegistry` class | Register/list/get tools | 3 |
| Tool invocation | Call tool by name with args | Returns tool result | 3 |
| Error handling | Tool errors don't crash agent | Graceful error | 2 |
| Async support | `async_call()` for I/O tools | Non-blocking | 2 |

**Files:**
- `aeryn_core/tools/registry.py`
- `aeryn_core/tools/base.py`
- `aeryn_core/tools/types.py`

**Test:**
```python
registry = ToolRegistry()
registry.register("echo", echo_tool)
result = registry.call("echo", {"text": "hello"})
assert result == "hello"
```

---

### 1.3 Core Tools

**Goal:** 5 essential tools for agent operation.

| Tool | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| `bash` | Execute shell command | Returns stdout/stderr | 4 |
| `file_read` | Read file content | Returns file content | 2 |
| `file_write` | Write file content | Creates/overwrites file | 2 |
| `file_search` | Search files by content | Returns matching files | 3 |
| `web_search` | Search the web | Returns search results | 4 |
| `web_fetch` | Fetch URL content | Returns page content | 3 |

**Files:**
- `aeryn_core/tools/bash.py`
- `aeryn_core/tools/file_read.py`
- `aeryn_core/tools/file_write.py`
- `aeryn_core/tools/file_search.py`
- `aeryn_core/tools/web_search.py`
- `aeryn_core/tools/web_fetch.py`

**Test:**
```python
result = bash_tool.execute({"command": "echo hello"})
assert result["stdout"].strip() == "hello"

result = file_read_tool.execute({"path": "/tmp/test.txt"})
assert "content" in result
```

---

### 1.4 Agent Loop

**Goal:** System prompt → User message → LLM → Tool call → Response.

| Task | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| System prompt builder | Build system prompt from config | Includes persona, tools, context | 3 |
| Message history | Token-bounded conversation | Auto-trim old messages | 4 |
| Tool call parsing | Parse LLM tool calls | Handles multiple formats | 4 |
| Tool execution | Execute tool calls from LLM | Returns results to LLM | 4 |
| Max iterations | Limit tool call loops | Prevents infinite loops | 2 |
| Error recovery | Handle LLM/tool errors | Graceful degradation | 3 |
| Streaming response | Stream tokens to client | Real-time output | 4 |

**Files:**
- `aeryn_core/agent/loop.py`
- `aeryn_core/agent/prompt.py`
- `aeryn_core/agent/history.py`
- `aeryn_core/agent/tool_call.py`

**Test:**
```python
agent = Agent(llm_client, tool_registry)
response = agent.run("Hello, what can you do?")
assert response.role == "assistant"
assert len(response.content) > 0
```

---

### 1.5 Chat Endpoint

**Goal:** Single HTTP endpoint for agent interaction.

| Task | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| `/v1/chat` POST | Send message, get response | Returns agent response | 3 |
| `/v1/chat/stream` SSE | Stream response tokens | Real-time stream | 4 |
| Session management | Multi-turn conversation | Maintains context | 3 |
| Workspace isolation | Separate sessions per workspace | No cross-contamination | 2 |

**Files:**
- `apps/api/routers/chat.py` (update)

**Test:**
```bash
curl -X POST http://localhost:3010/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "session_id": "test"}'
# Returns: {"role": "assistant", "content": "..."}
```

---

### Phase 1 Acceptance Criteria

- [ ] Agent can respond to user messages
- [ ] Agent can call tools (bash, file_read, file_write)
- [ ] Agent maintains conversation context
- [ ] Agent handles errors gracefully
- [ ] Streaming response works
- [ ] Session isolation works

**Total Estimate: ~80 hours (1-2 weeks)**

---

## Phase 2: Memory & Context (1 week)

> Integrate memory systems with agent loop.

### 2.1 Memory Recall

**Goal:** Retrieve relevant memories before LLM call.

| Task | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| Memory search | Search vault + semantic + graph | Returns top-k memories | 4 |
| Relevance scoring | Score memories by relevance | Accurate ranking | 3 |
| Context injection | Inject memories into system prompt | Within token budget | 3 |
| Memory ranking | Rank by recency + relevance | Best memories first | 2 |

**Files:**
- `aeryn_core/memory/recall.py`
- `aeryn_core/memory/ranking.py`

---

### 2.2 Memory Write

**Goal:** Save important information after conversation.

| Task | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| Auto-save | Auto-save facts to vault | Facts persisted | 3 |
| Entity extraction | Extract entities from messages | Entities stored | 4 |
| Preference learning | Learn user preferences | Preferences updated | 3 |
| Memory consolidation | Merge related memories | No duplicates | 3 |

**Files:**
- `aeryn_core/memory/write.py`
- `aeryn_core/memory/extract.py`

---

### 2.3 Context Window Management

**Goal:** Keep conversation within token limits.

| Task | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| Token budget | Allocate tokens for history, tools, memories | Never exceeds limit | 3 |
| Auto-summarize | Summarize old messages | Fits in budget | 4 |
| Sliding window | Keep recent messages | Context preserved | 2 |

**Files:**
- `aeryn_core/agent/context.py`

---

### Phase 2 Acceptance Criteria

- [ ] Agent recalls relevant memories
- [ ] Agent saves new facts automatically
- [ ] Context window never exceeds token limit
- [ ] Old messages are summarized
- [ ] Entity extraction works

**Total Estimate: ~30 hours (1 week)**

---

## Phase 3: Frontend Chat (3-5 days)

> Build chat UI for agent interaction.

### 3.1 Chat Component

**Goal:** React component for chat interface.

| Task | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| Message list | Display conversation history | Scrollable, styled | 4 |
| Input box | Text input with send | Enter to send | 2 |
| Streaming display | Show tokens as they appear | Real-time | 4 |
| Tool call display | Show tool calls in UI | Collapsible, formatted | 3 |
| Code syntax highlighting | Highlight code blocks | Syntax colors | 3 |

**Files:**
- `apps/web/src/components/Chat.tsx`
- `apps/web/src/components/Message.tsx`
- `apps/web/src/components/ToolCall.tsx`

---

### 3.2 Session Management

**Goal:** Multi-session support in frontend.

| Task | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| Session list | List past sessions | Clickable | 3 |
| New session | Create new chat | Clears context | 2 |
| Session switch | Switch between sessions | Context preserved | 3 |
| Session delete | Delete session | Confirmation dialog | 2 |

**Files:**
- `apps/web/src/components/SessionList.tsx`
- `apps/web/src/hooks/useSessions.ts`

---

### 3.3 Settings UI

**Goal:** Configure agent settings.

| Task | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| Provider selection | Choose LLM provider | Dropdown | 2 |
| Model selection | Choose model | Per-provider models | 2 |
| System prompt | Edit system prompt | Text area | 2 |
| Tool toggle | Enable/disable tools | Checkboxes | 2 |

**Files:**
- `apps/web/src/components/Settings.tsx`

---

### Phase 3 Acceptance Criteria

- [ ] Chat UI works with agent
- [ ] Streaming response displays in real-time
- [ ] Tool calls are visible
- [ ] Multiple sessions work
- [ ] Settings can be changed

**Total Estimate: ~30 hours (3-5 days)**

---

## Phase 4: Multi-Agent & Advanced (2 weeks)

> Enable 5 cognitive divisions and plugin system.

### 4.1 Division System

**Goal:** 5 cognitive divisions as agent personalities.

| Task | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| Division config | YAML config per division | 5 configs | 4 |
| Creative division | Style, POV, narrative | Works as agent | 4 |
| Psych division | Mental health, peace | Works as agent | 4 |
| Reasoning division | MCTS, FOL, critique | Works as agent | 6 |
| Governance division | Constitutional compliance | Works as agent | 4 |
| Infrastructure division | Sync, validation | Works as agent | 4 |
| Division routing | Route to correct division | Accurate routing | 4 |

**Files:**
- `aeryn_core/agent/divisions/creative.yaml`
- `aeryn_core/agent/divisions/psych.yaml`
- `aeryn_core/agent/divisions/reasoning.yaml`
- `aeryn_core/agent/divisions/gov.yaml`
- `aeryn_core/agent/divisions/infra.yaml`
- `aeryn_core/agent/divisions/router.py`

---

### 4.2 Plugin System

**Goal:** Dynamic tool loading from plugins.

| Task | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| Plugin manifest | YAML manifest for plugins | Valid schema | 3 |
| Plugin loader | Load plugins from directory | Auto-discover | 4 |
| Plugin tools | Register plugin tools | Tools available | 3 |
| Plugin marketplace | Browse and install plugins | REST API | 6 |
| Plugin sandbox | Isolate plugin execution | Security | 4 |

**Files:**
- `aeryn_core/plugins/manifest.py`
- `aeryn_core/plugins/loader.py`
- `aeryn_core/plugins/marketplace.py`
- `aeryn_core/plugins/sandbox.py`

---

### 4.3 Advanced Features

| Task | Description | Acceptance | Hours |
|------|-------------|------------|-------|
| Multi-step planning | Break complex tasks into steps | Plans executed | 6 |
| Self-reflection | Agent reflects on its own output | Improves quality | 4 |
| Error correction | Agent corrects its own mistakes | Self-healing | 4 |
| Proactive suggestions | Agent suggests next actions | Relevant suggestions | 4 |

**Files:**
- `aeryn_core/agent/planning.py`
- `aeryn_core/agent/reflection.py`
- `aeryn_core/agent/proactive.py`

---

### Phase 4 Acceptance Criteria

- [ ] 5 divisions work as separate agents
- [ ] Division routing is accurate
- [ ] Plugins can be loaded dynamically
- [ ] Marketplace API works
- [ ] Multi-step planning works
- [ ] Self-reflection improves quality

**Total Estimate: ~50 hours (2 weeks)**

---

## Summary

| Phase | Duration | Hours | Deliverable |
|-------|----------|-------|-------------|
| **Phase 1: Agent Core** | 1-2 weeks | 80 | Working agent with tools |
| **Phase 2: Memory & Context** | 1 week | 30 | Memory-augmented agent |
| **Phase 3: Frontend Chat** | 3-5 days | 30 | Chat UI |
| **Phase 4: Multi-Agent** | 2 weeks | 50 | 5 divisions + plugins |
| **TOTAL** | **5-6 weeks** | **190** | **Complete agent** |

---

## Architecture After Completion

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐     │
│  │  Chat UI    │  Sessions   │  Settings   │  Tool View  │     │
│  └─────────────┴─────────────┴─────────────┴─────────────┘     │
└──────────────────────────────┬──────────────────────────────────┘
                               │ /v1/chat
┌──────────────────────────────▼──────────────────────────────────┐
│                     Agent Core (Python)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Agent Loop                                               │  │
│  │  System Prompt → User Message → LLM → Tool Call → Loop   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐     │
│  │  LLM Client │  Tool Reg   │  Divisions  │  Plugins    │     │
│  └─────────────┴─────────────┴─────────────┴─────────────┘     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Memory Recall → Context Window → Memory Write            │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ C FFI
┌──────────────────────────────▼──────────────────────────────────┐
│                      Rust Engine                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  cosine_similarity, hash_text, find_top_k, ...            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

> Generated: 2026-09-02
> Author: Hermes Agent (Nous Research)
> Version: 2.0
