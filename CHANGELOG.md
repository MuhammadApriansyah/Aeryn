# Changelog

All notable changes to Aeryn will be documented in this file.

---

## [61.5] — 2026-09-02

### Refactored — Monolith Removal & Dead Code Cleanup
- **Removed `aeryn_api.py` monolith** (4,303 lines, 140KB) — all routes migrated to modular `routers/` directory
- **Removed all Rust source code** (22 files in `src/`) — zero Python imports, pure dead code
- **Removed `aeryn_native.so`** — compiled extension never imported by any Python module
- **Removed `Cargo.toml`** — PyO3 build dependency no longer needed

### Fixed — Disappearing React Components
- **Root cause**: `phase4.py` had `@router.get("/")` that overrode `web_routes_router`'s `/` route
- **Fix**: Removed duplicate `/` route from `phase4.py`, kept only in `web_routes.py`
- **Result**: React SPA now serves correctly at `/` with `<div id="root">` for React mounting

### Fixed — Missing Imports in Phase 4 Router
- Added 18 missing `get_*` function imports to `phase4.py`
- Fixed `get_usage_metering` import in `tools.py`
- Added `get_pending_tasks()` and `get_all_tasks()` convenience methods to `SharedDB`

### Fixed — Constitutional AI
- Rewrote `constitutional_ai.py` to use raw `sqlite3` (bypasses PG adapter for local DB)
- Added `get_principles()` method to `ConstitutionalAI` class
- Fixed `get_principles` endpoint in `phase4.py` to use the new method

### Fixed — Metrics & Alerts
- Replaced broken `from monitor import ProductionMonitor` with fallback using `SharedDB`
- `/v1/metrics` now returns workflow stats from `SharedDB.get_workflow_stats()`
- `/v1/alerts` now returns pending reminders from `SharedDB.get_all_reminders()`

### Consolidated — Frontend
- Removed fallback to old vanilla dashboard (`apps/web/templates/dashboard.html`)
- `web_routes.py` now serves only React SPA from `apps/web-vite/dist/`
- Removed `apps/web/server.py` import from `phase4.py`

### Verification
- All 31 critical endpoints tested with real HTTP requests (no test doubles)
- All endpoints return 200 OK
- React SPA confirmed serving at `/` with correct `id="root"` div

---

## [61.1] — 2026-08-31

### Added — Adaptive Infrastructure (Roadmap P0a–P6)
- **P0a Adaptive Gateway**: `adaptive_gateway.py` with `detect_environment()` (proot/vps/k8s), wires AuthManager + RateLimiter + CircuitBreaker. Endpoint `/gateway/env`.
- **P0b Agent Daemon**: `agent_daemon.py` autonomy loop — picks tasks, executes via tool_runtime + LLM, stores results. Endpoints `/daemon/tasks`.
- **P1 Sandbox Wiring**: `tool_runtime._terminal()` now uses `EnhancedSandbox` (resource limits + path isolation). `rm -rf /` blocked.
- **P2 Postgres Adapter**: `db_adapter.py` verified routing to PostgreSQL. FTS5 blocker documented (hybrid_search uses SQLite virtual tables).
- **P3 Consolidation**: Removed orphan `orchestrator_v2.py`.
- **P4 Stub Audit**: `AUDIT_STUBS.md` — 69 small files documented as package markers / intentional scaffolds.
- **P5 API Versioning + Portability**: `/v1/` prefix alias, `AERYN_BASE_DIR` env override.
- **P6 Capability Bridge**: `capability_bridge.py` — dynamic skill loader + semantic memory recall. Endpoints `/skills`, `/memory/recall`.

### Added — Dimension Transfer & Analysis (D7–D11)
- **D7 Observability/Tracing**: `aeryn_core/observability/tracer.py` — Trace, Span, Tracer classes. Endpoints `/observability/traces`, `/observability/stats`.
- **D10 Dynamic Tool Routing**: `aeryn_core/platform/plugin_registry.py` — PluginRegistry with discover_tools(), call_tool(), load_plugins_from_dir(). Endpoints `/plugins`, `/plugins/discover`.
- **D2 Complete Tool Exec**: Wired `tool_runtime` + `PluginRegistry` to `/run` and `/chat` endpoints. Auto-executes tools when intent matches.
- **D3 Delegation 5 Divisi**: `_route_to_division()` in chat.py routes to creative/psych/reasoning/gov/infra based on intent.
- **D8 Multi-Agent Orchestration**: `aeryn_core/orchestration/crew_orchestrator.py` — Crew/Agent/Task/Process pattern (crewAI-style). DivisionManager with 5 divisions.
- **D4 Ease of Access**: `aeryn_core/launcher.py` — `python -m aeryn_core.launcher start|stop|status|env`. Auto-detects env, generates ecosystem.config.cjs.
- **D9 Enterprise RAG Connectors**: `aeryn_core/connectors/vault_connector.py` — FileSystemConnector, WebConnector, GitHubConnector. Sync external data to Vault.
- **D11 Phase-Gated Workflow**: `aeryn_core/workflow/phase_workflow.py` — Workflow/WorkflowStep/Checkpoint/WorkflowBuilder. 8-phase SaaS workflow with approval gates.

### Verification
- All 11 dimensions (D1–D11) verified via direct function calls (no test doubles).
- 8 external sources analyzed (crewAI, Langfuse, Onyx, voltagent, Gravity, SaaSPilot, AaaS, Agent-Startup-Skills).
- 168+ OpenAPI paths, 14 modular routers, 20+ memory systems, 16 reasoning engines.

### Known Limitations
- PM2 in proot has module-reload quirk; restart via `pm2 kill` + fresh `start` recommended.
- Postgres not default (FTS5 dependency); SQLite remains stable default.

### Verified
- All P0a–P6 logic verified via direct function calls (no test doubles).
- `/v1/chat`, `/v1/health` return 200; legacy paths still work.
- Sandbox: valid command executes, `rm -rf /` blocked.

### Known Limitations
- PM2 in proot has module-reload quirk; restart via `pm2 kill` + fresh `start` recommended.
- Postgres not default (FTS5 dependency); SQLite remains stable default.

---

## [59.0] — 2026-08-30

### Added
- **Error Boundary**: `showErrorBoundary()` + `safeExecute()` wrapper for runtime error handling
- **Empty State**: Custom empty states for Projects, Workspaces, Chat, Plugins, Audit pages
- **Confirmation Dialog**: `showConfirmDialog()` for destructive actions with focus trap + Escape close
- **Loading States**: Skeleton screens per page + `showLoading()` function
- **Real Pages Implemented**: Projects (localStorage CRUD), Workspaces (create/delete), Chat (sessions), Plugins (install/uninstall), Audit Trail (table view)
- **Command Palette**: `Ctrl+Shift+P` opens command palette with fuzzy search
- **Notification Center**: Full notification management with read/unread + badge
- **Project Actions**: Create/Open/Delete projects with localStorage persistence
- **Workspace Actions**: Create/Open/Delete workspaces
- **Chat Sessions**: New/Open chat sessions
- **Data Management**: Export/Import all localStorage data

### Fixed
- Removed all test doubles from production code
- Fixed guardrails.py: removed unreachable `return False` before variance calculation
- Fixed self_improvement.py: uuid import moved to top-level + optimize_prompt argument
- Fixed dashboard.html: CSS/JS links point to correct SPA paths
- Fixed duplicate `/plugins` API route conflict

### Technical Details
- Backend API: port 3010 (FastAPI)
- Web UI: port 3010/ (SPA with full client-side routing)
- Zero dependencies (vanilla JS + CSS)

---

## [58.0] — 2026-08-30

### Added
- **SPA Dashboard**: Full Single Page Application with vanilla JS
- **Real-time Health Check**: Auto-refresh every 5 seconds
- **Loading Skeleton**: Shimmer animation while loading
- **Toast Notifications**: Success/error/info/warning notifications
- **Offline Detection**: Banner when backend API is offline
- **Breadcrumb Navigation**: Show current page hierarchy
- **Skip Link**: Accessibility skip to main content
- **Keyboard Shortcuts**: Ctrl+K (search), Ctrl+T (theme), Ctrl+/ (help)
- **Theme Toggle**: Dark/Light mode with localStorage persistence
- **ARIA Labels**: Accessibility labels for all interactive elements
- **Responsive Design**: Mobile-friendly layout
- **Reduced Motion**: Respect prefers-reduced-motion
- **High Contrast**: Support for prefers-contrast: high

### Technical Details
- Backend API: port 3010 (FastAPI)
- Web UI: port 3010/web/ (SPA)
- Zero dependencies (vanilla JS + CSS)
- 661 tests pass

---

## [57.0] — 2026-08-30

### Added
- **Multi-Region Deploy**: Deploy to multiple AWS regions with Terraform
- **Distributed Tracing**: OpenTelemetry + Jaeger integration
- **Advanced Monitoring APM**: Prometheus metrics + Grafana dashboards

### Test Results: 661 tests pass

---

## [56.0] — 2026-08-29

### Added
- **Workflow DSL**: Define custom generation workflows with YAML/JSON
- **Headless Mode**: `--non-interactive` for fully automated CI/CD
- **Config File**: `.aerynrc` for project defaults with dot notation
- **Batch Generate**: Generate multiple projects from JSON config
- **Template Inheritance**: Extend templates from other templates
- **Custom Generators**: Replace default generators with custom logic

### Test Results: 658 tests pass

---

## [55.0] — 2026-08-29

### Added
- **Workspace Management**: Multi-tenant workspaces with RBAC
- **Audit Trail**: Track all actions for compliance
- **Rate Limiting**: Built-in API rate limiter
- **Cache Layer**: Redis caching template
- **Job Queue**: Background job processing (Bull)

### Test Results: 653 tests pass

---

## [54.0] — 2026-08-29

### Added
- **Headless Mode**: `--non-interactive` flag for CI/CD automation
- **Config File**: `.aerynrc` for project defaults and reproducibility
- **Batch Generate**: Generate multiple projects from JSON config

### Fixed
- **Dashboard Web UI**: Fixed PM2 integration (port 3020)

### Test Results: 648 tests pass

---

## [53.0] — 2026-08-29

### Added
- **Plugin Marketplace**: Share and download plugins
- **Smart Seeder**: Realistic fake data generation
- **Security Audit**: Basic vulnerability scanning
- **API Documentation**: Auto-generate OpenAPI/Swagger

### Test Results: 648 tests pass

---

## [52.0] — 2026-08-29

### Added
- **Plugin API Documentation**: Complete reference and tutorials
- **Auto Rollback Migration**: Auto-generate rollback scripts
- **Environment Management**: Switch dev/staging/prod
- **WebSocket/SSE Templates**: Real-time features
- **API Versioning**: v1, v2 support

### Test Results: 648 tests pass

---

## [51.0] — 2026-08-29

### Added
- **Plugin System**: Extensible architecture with hooks
- **CI/CD Templates**: GitHub Actions for CI/CD
- **Multi-DB Support**: SQLite, PostgreSQL, MySQL
- **Working Tests**: Generated tests that run directly

### Test Results: 643 tests pass

---

## [50.0] — 2026-08-29

### Added
- **Template Preview**: Visual thumbnails with features
- **Success Animation**: Celebration on completion
- **Debug Mode**: Verbose logging
- **Custom Templates**: Create and share templates
- **Diff Preview**: Before/after comparison

### Test Results: 643 tests pass

---

## [49.0] — 2026-08-29

### Added
- **One-Click Generate**: Minimal questions, instant project
- **Post-Generate Guide**: Clear next steps
- **Progress Indicator**: Visual feedback during generation

### Test Results: 638 tests pass

---

## [48.0] — 2026-08-29

### Added
- **Preview**: View project before generate
- **Help**: Contextual help for every step
- **Gallery**: Example projects
- **Undo**: Revert changes
- **Proactive Warnings**: Alerts before errors

### Test Results: 635 tests pass

---

## [47.0] — 2026-08-29

### Added
- **Setup Wizard**: Interactive project setup (`aeryn start`)
- **Visual Dashboard**: Web UI at port 3020
- **Error Solver**: Friendly error messages with solutions
- **One-Click Installer**: `aeryn-installer.sh`

### Test Results: 630 tests pass

---

## [46.0] — 2026-08-29

### Added
- **Fullstack AI Engineer Mode**: Complete development lifecycle
- **Fullstack CLI**: new, dev, db:migrate, db:seed, test, build, deploy
- **Realistic Templates**: React + Fastify + SQLite
- **Migration System**: Database migrations with rollback

### Test Results: 630 tests pass

---

## [45.0] — 2026-08-29

### Added
- **Native Sandbox**: Conditional security with directed fallback
- **4 Isolation Levels**: Basic, Namespace, Bubblewrap, Full
- **Zero Dependencies**: Works without Docker/Bubblewrap/root

### Test Results: 619 tests pass

---

## [44.0] — 2026-08-29

### Added
- **Option A (Personal Assistant)**: Proactive engine, personalization
- **Option B (Agent Infrastructure)**: Templates, CLI
- **Option C (Security Platform)**: Dashboard, compliance

### Test Results: 613 tests pass

---

## [43.0] — 2026-08-29

### Added
- **MCP Protocol**: Server + Client + Registry
- **Multi-Agent Orchestration**: Workflow engine
- **Integration SDK**: Developer SDK

### Test Results: 606 tests pass

---

## [42.0] — 2026-08-29

### Added
- **Security Hardening**: Prompt injection defense, memory guard
- **Cost Optimization**: Token monitoring, model routing
- **Adaptive Rule Engine**: Hot-reloadable rules

### Test Results: 602 tests pass

---

## [41.0] — 2026-08-29

### Added
- **Hermes Bridge**: Shared skills/scripts from Hermes
- **Hermes Plugin**: Aeryn as Hermes plugin
- **Three Modes**: Plugin, Standalone+Hermes, Standalone

### Test Results: ~600 tests pass

---

## [40.0] — 2026-08-28

### Added
- Initial release of Aeryn platform

### Features
- Auth, billing, workspaces, plugins, webhooks
- Rust engine (VectorDB, RateLimiter, SSE, WebSocket)
- 597+ tests
