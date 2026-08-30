# Changelog

All notable changes to Aeryn will be documented in this file.

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

