# 🔍 Audit Report: Aeryn v2 — Engine vs Logic Classification

> Comprehensive audit of ALL 339 Python files + 29 Rust files.
> Goal: Move Engine → Rust, Logic → Python.

---

## 📊 Current State Summary

| Category | Files | Lines | Language |
|----------|-------|-------|----------|
| **Rust Engine** | 29 | 5,619 | Rust |
| **Python (new modules)** | ~15 | ~72,000 | Python |
| **Python (old monolith)** | ~324 | ~35,000 | Python |
| **TOTAL** | **368+** | **~112,619** | **Mixed** |

---

## 🎯 Classification Criteria

### 🦀 ENGINE (should be Rust)
- CPU-bound computations (vector ops, graph traversal, search)
- Memory-critical operations (caching, pooling)
- Parallel processing (batch operations, concurrent tasks)
- Low-level I/O (database, file parsing)
- Performance-sensitive paths (embedding, tokenization)

### 🐍 LOGIC (should be Python)
- Business rules and coordination
- API routing and serialization
- User interaction and state management
- Configuration and orchestration
- Analytics and reporting
- Plugin/skill composition

---

## 📋 Detailed Classification: OLD Monolith Modules

### 🔴 ENGINE — Must Move to Rust

| Module | File | Current | Reason |
|--------|------|---------|--------|
| **memory/decay.py** | `memory_decay.py` | CPU-bound math | Time-series decay calculations |
| **memory/graph.py** | `graph.py` | Graph ops | Graph traversal, path finding |
| **memory/graph_memory.py** | `graph_memory.py` | Graph ops | Memory-to-memory edges |
| **memory/hybrid_search.py** | `hybrid_search.py` | Search | Vector + keyword + graph search |
| **memory/semantic_recall.py** | `semantic_recall.py` | Search | Semantic similarity search |
| **memory/temporal_memory.py** | `temporal_memory.py` | Time-series | Temporal queries |
| **memory/entity_resolution.py** | `entity_resolution.py` | Matching | Entity deduplication |
| **memory/memory_indexer.py** | `memory_indexer.py` | Indexing | Memory indexing |
| **memory/memory_consolidation.py** | `memory_consolidation.py` | Merge | Memory merging algorithms |
| **database/vector_db.py** | `vector_db.py` | Vector ops | ChromaDB/SQLite vector store |
| **database/semantic_indexer.py** | `semantic_indexer.py` | Indexing | Semantic index operations |
| **database/semantic_search.py** | `semantic_search.py` | Search | Semantic search queries |
| **database/db_adapter.py** | `db_adapter.py` | DB ops | SQLite-to-PostgreSQL adapter |
| **database/shared_db.py** | `shared_db.py` | DB ops | Shared database operations |
| **utils/embedding_bridge.py** | `embedding_bridge.py` | Embedding | Embedding model interface |
| **utils/performance.py** | `performance.py` | Monitoring | Performance metrics collection |
| **utils/cache.py** | `cache.py` | Caching | LRU cache implementation |
| **utils/data_encryption.py** | `data_encryption.py** | Crypto | Data encryption/decryption |
| **safety/sandbox.py** | `sandbox.py` | Isolation | Code execution sandbox |
| **safety/security_kernel.py** | `security_kernel.py` | Security | Security kernel operations |
| **safety/terminal_tool.py** | `terminal_tool.py` | Execution | Terminal command execution |
| **platform/tool_runtime.py** | `tool_runtime.py` | Execution | Tool execution runtime |
| **platform/agent_daemon.py** | `agent_daemon.py` | Daemon | Agent daemon loop |
| **platform/background_queue.py** | `background_queue.py` | Queue | Background task queue |
| **platform/realtime.py** | `realtime.py` | WebSocket | Real-time communication |
| **platform/websocket_server.py** | `websocket_server.py` | WebSocket | WebSocket server |
| **fullstack/engine.py** | `engine.py` | Generation | Full-stack generation engine |
| **fullstack/backend.py** | `backend.py` | Scaffolding | Backend scaffolding |
| **fullstack/frontend.py** | `frontend.py` | Scaffolding | Frontend scaffolding |
| **fullstack/database.py** | `database.py` | Scaffolding | Database scaffolding |
| **fullstack/deploy.py** | `deploy.py` | Deploy | Deployment automation |
| **fullstack/planner.py** | `planner.py` | Planning | Project planning |
| **fullstack/test_gen.py** | `test_gen.py` | Testing | Test generation |

**Total Engine: ~33 modules → Move to Rust**

---

### 🟢 LOGIC — Keep in Python

| Module | File | Current | Reason |
|--------|------|---------|--------|
| **auth/** | `auth.py`, `api_keys.py`, `rate_limiter.py`, `sso_manager.py` | Auth | Business rules, JWT, OAuth |
| **billing/** | `billing.py`, `cost_tracking.py`, `usage_metering.py` | Billing | Cost calculation, usage tracking |
| **agents/** | `*/master_agent.py`, `*/sub_agents_real.py` | Coordination | Agent orchestration |
| **workflow/** | `phase_workflow.py` | Workflow | Workflow definition |
| **workflow_dsl/** | `workflow.py`, `actions.py` | DSL | Workflow DSL |
| **plugins/** | `*/registry.py`, `*/loader.py` | Plugin | Plugin management |
| **plugin_system/** | `*/base.py`, `*/builtin/auth_plugin.py` | Plugin | Plugin system |
| **observability/** | `tracer.py` | Tracing | Custom tracing |
| **personal/** | `context.py`, `personalization.py`, `proactive_engine.py` | Personalization | User context |
| **reasoning/** | `constitutional_ai.py`, `dream_synthesis.py`, `emotional_intelligence.py` | Reasoning | Cognitive reasoning |
| **safety/** | `guardrails.py`, `injection_sweep.py`, `owasp_security.py` | Safety | Safety rules |
| **platform/** | `plugin_registry.py`, `plugin_marketplace.py`, `plugin_system.py` | Platform | Plugin platform |
| **memory/** | `vault.py`, `session_history.py`, `social_memory.py` | Memory | Memory management |
| **mcp/** | `server.py`, `client.py` | MCP | MCP protocol |
| **orchestration/** | `crew_orchestrator.py` | Orchestration | Multi-agent orchestration |
| **multi_agent/** | `orchestrator.py` | Multi-agent | Agent coordination |
| **dashboard/** | `server.py`, `run_server.py` | Dashboard | Dashboard server |
| **connectors/** | `vault_connector.py` | Connector | External connectors |
| **cost/** | `model_router.py`, `token_monitor.py` | Cost | Cost optimization |
| **hermes/** | `hermes_brain.py`, `hermes_hands.py`, `hermes_reflex.py` | Hermes | Hermes integration |
| **hermes_plugin/** | `loader.py`, `hermes_bridge_init.py` | Hermes | Hermes plugin |
| **fullstack/templates/** | `base.py`, `react_fastify.py`, `vue_fastify.py` | Templates | Project templates |
| **fullstack/cli/** | `main.py` | CLI | CLI interface |
| **fullstack/migration/** | `manager.py` | Migration | Database migration |
| **utils/** | `config.py`, `logger.py`, `llm_client.py`, `model_client.py` | Utils | Configuration, logging |
| **utils/** | `event_bus.py`, `tool_schema.py`, `structured_output.py` | Utils | Event handling |
| **utils/** | `dynamic_router.py`, `fallback_router.py`, `adaptive_inference.py` | Utils | Routing logic |
| **utils/** | `persona_engine.py`, `bica_alignment.py`, `cog_mem_lifecycle.py` | Utils | Persona, alignment |
| **utils/** | `context_pruner.py`, `reconsideration_guard.py`, `latent_value.py` | Utils | Context management |
| **utils/** | `meta_evolution.py`, `swarm_convergence.py`, `sla_monitoring.py` | Utils | Evolution, monitoring |
| **utils/** | `dynamic_schema.py`, `multimodal.py`, `image_tools.py` | Utils | Schema, multimodal |
| **utils/** | `basic_tools.py`, `guardrails.py`, `tui_monitor.py` | Utils | Tools, monitoring |
| **utils/** | `workflow_dag.py`, `memory_pool.py`, `memory_vault_bridge.py` | Utils | DAG, memory |
| **utils/** | `error_handling.py`, `error_recovery.py`, `patch_sqlite.py` | Utils | Error handling |
| **ci_cd/** | `generator.py` | CI/CD | CI/CD generation |
| **wizard/** | `interactive.py` | Wizard | Interactive wizard |
| **installer/** | `script.py` | Installer | Installation script |
| **integrations/** | `sdk.py` | Integration | SDK integration |
| **job_queue/** | `queue.py` | Queue | Job queue |
| **auto_rollback/** | `manager.py` | Rollback | Auto-rollback |
| **env_management/** | `manager.py` | Env | Environment management |
| **error_solver/** | `solver.py` | Solver | Error solving |
| **debug_mode/** | `debugger.py` | Debug | Debug mode |
| **deploy_dashboard/** | `dashboard.py` | Deploy | Deploy dashboard |
| **diff_preview/** | `viewer.py` | Diff | Diff preview |
| **distributed_tracing/** | `tracer.py` | Tracing | Distributed tracing |
| **headless_mode/** | `runner.py` | Headless | Headless mode |
| **help/** | `helper.py` | Help | Help system |
| **gallery/** | `examples.py` | Gallery | Examples gallery |
| **oneclick/** | `generator.py` | OneClick | One-click generation |
| **proactive/** | `warnings.py` | Proactive | Proactive warnings |
| **progress/** | `indicator.py` | Progress | Progress indicator |
| **rate_limiting/** | `limiter.py` | Rate Limit | Rate limiting |
| **success_anim/** | `animator.py` | Animation | Success animation |
| **smart_seeder/** | `generator.py` | Seeder | Smart seeder |
| **template_inheritance/** | `base.py` | Template | Template inheritance |
| **template_preview/** | `preview.py` | Preview | Template preview |
| **undo/** | `manager.py` | Undo | Undo manager |
| **websocket_template/** | `generator.py` | WebSocket | WebSocket template |
| **working_tests/** | `generator.py` | Tests | Working tests |
| **workspace/** | `manager.py` | Workspace | Workspace management |
| **api_designer/** | `designer.py` | API | API design |
| **api_versioning/** | `generator.py` | Versioning | API versioning |
| **audit_trail/** | `trail.py` | Audit | Audit trail |
| **batch_generate/** | `batch.py` | Batch | Batch generation |
| **cache_layer/** | `cache.py` | Cache | Cache layer |
| **config_file/** | `config.py` | Config | Configuration file |
| **custom_generators/** | `registry.py` | Custom | Custom generators |
| **custom_template/** | `editor.py` | Template | Custom template |
| **preview/** | `viewer.py` | Preview | Preview viewer |
| **plugin_docs/** | `docs.py` | Docs | Plugin docs |
| **plugin_marketplace/** | `client.py` | Marketplace | Plugin marketplace |
| **security/** | `memory_guard.py`, `prompt_injection.py`, `tool_permissions.py` | Security | Security logic |
| **security/dashboard/** | `compliance.py`, `security_dashboard.py` | Security | Security dashboard |
| **self_improvement/** | `engine.py` | Self-imp | Self-improvement |
| **adaptive/** | `monitor.py` | Adaptive | Adaptive monitoring |
| **advanced_monitoring/** | `monitor.py` | Monitoring | Advanced monitoring |
| **multi_region_deploy/** | `deployer.py` | Deploy | Multi-region deploy |
| **notification_system/** | `notification.py` | Notify | Notifications |
| **browser_automation/** | `browser.py` | Browser | Browser automation |
| **browser_vector.py** | `browser_vector.py` | Browser | Browser vector |
| **calendar_integration.py** | `calendar_integration.py` | Calendar | Calendar integration |
| **capability_bridge.py** | `capability_bridge.py` | Bridge | Capability bridge |
| **cloud_sync.py** | `cloud_sync.py` | Cloud | Cloud sync |
| **discord_bot.py** | `discord_bot.py` | Discord | Discord bot |
| **email_agent.py** | `email_agent.py` | Email | Email agent |
| **github_integration.py** | `github_integration.py` | GitHub | GitHub integration |
| **graphql_api.py** | `graphql_api.py` | GraphQL | GraphQL API |
| **mcp_production.py** | `mcp_production.py` | MCP | MCP production |
| **mcp_server.py** | `mcp_server.py` | MCP | MCP server |
| **multi_agent.py** | `multi_agent.py` | Multi-agent | Multi-agent |
| **multi_agent_rooms.py** | `multi_agent_rooms.py` | Rooms | Agent rooms |
| **multi_region.py** | `multi_region.py` | Region | Multi-region |
| **multi_tenant.py** | `multi_tenant.py` | Tenant | Multi-tenant |
| **orchestrator.py** | `orchestrator.py` | Orchestration | Orchestrator |
| **plugin_marketplace.py** | `plugin_marketplace.py` | Marketplace | Marketplace |
| **plugin_registry.py** | `plugin_registry.py` | Registry | Plugin registry |
| **plugin_system.py** | `plugin_system.py` | System | Plugin system |
| **realtime_rust.py** | `realtime_rust.py` | Rust | Real-time Rust |
| **skill_crystallization.py** | `skill_crystallization.py` | Skill | Skill crystallization |
| **skill_forge.py** | `skill_forge.py` | Skill | Skill forge |
| **sub_agent_runner.py** | `sub_agent_runner.py` | Sub-agent | Sub-agent runner |
| **task_executor.py** | `task_executor.py` | Task | Task executor |
| **telegram_bot.py** | `telegram_bot.py` | Telegram | Telegram bot |
| **tool_bridge.py** | `tool_bridge.py` | Tool | Tool bridge |
| **tool_governance.py** | `tool_governance.py` | Governance | Tool governance |
| **webhook_system.py** | `webhook_system.py` | Webhook | Webhook system |
| **websocket_rust.py** | `websocket_rust.py` | Rust | WebSocket Rust |
| **workspace_manager.py** | `workspace_manager.py` | Workspace | Workspace manager |

**Total Logic: ~180+ modules → Keep in Python**

---

## 📊 Migration Summary

| Category | Modules | Action |
|----------|---------|--------|
| **Engine → Rust** | ~33 | Rewrite in Rust, add PyO3 bindings |
| **Logic → Python** | ~180 | Keep as-is, clean up |
| **Already Rust** | ~12 | Keep and extend |
| **Already Python (new)** | ~15 | Keep and extend |

---

## 🎯 Migration Priority

### Priority 1: High-Impact Engine (move to Rust)
1. `database/vector_db.py` → Vector operations (already partially in Rust)
2. `memory/hybrid_search.py` → Search algorithms
3. `memory/decay.py` → Decay calculations
4. `utils/embedding_bridge.py` → Embedding interface
5. `database/db_adapter.py` → Database operations

### Priority 2: Medium-Impact Engine (move to Rust)
6. `memory/graph.py` → Graph operations
7. `memory/semantic_recall.py` → Semantic search
8. `safety/sandbox.py` → Sandbox execution
9. `platform/tool_runtime.py` → Tool execution
10. `fullstack/engine.py` → Generation engine

### Priority 3: Low-Impact (keep in Python, optimize)
11. All logic modules → Keep in Python
12. All coordination modules → Keep in Python

---

*Audit completed: 2026-09-02*
*Total files audited: 368+*
*Engine modules identified: ~33*
*Logic modules identified: ~180+*
