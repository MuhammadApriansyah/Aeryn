# Team Structure

> **Purpose**: Document the Aeryn development pipeline team roles and responsibilities.
> **Rule**: This reflects the actual autonomous agent workflow used for Sprint development.

---

## 🏢 Team Composition

The Aeryn development pipeline operates as a **multi-agent autonomous system**. There is no human team — all roles are fulfilled by AI agents using the Hermes Agent framework.

### Roles & Responsibilities

| Role | Agent | Primary Tools |
|------|-------|---------------|
| **Lead Agent** | Primary orchestrator | `terminal`, `read_file`, `write_file`, `git` |
| **Implementation Agent** | Feature implementer | `terminal`, `patch`, `write_file` |
| **Testing Agent** | Test verification | `terminal` (pytest, curl) |
| **Documentation Agent** | Doc updates | `write_file`, `patch` |
| **QC Agent** | Final audit | `terminal`, `search_files`, `grep` |

---

## 🤝 Workflow Coordination

### Multi-Agent Orchestration

```python
# Using Hermes delegation framework
from hermes_tools import delegate_task

# Spawn implementation sub-agents for parallel work
tasks = [
    {"goal": "Implement error boundary in dashboard.js", "context": "vanilla JS, no mocks"},
    {"goal": "Fix guardrails.py placeholder code", "context": "variance check must run"},
    {"goal": "Write system prompt templates", "context": "docs/prompts/"},
]

results = delegate_task(tasks=tasks)
```

### Cross-Session Sync

- State DB: `~/.hermes/state.db`
- Handoff: `handoff.py --task "<description>"`
- Checkpoints: `achp checkpoint` triggers handoff

---

## 🎯 Sprint Cadence

### Sprint Planning (Pre-Sprint)
- **Duration**: 1-2 hours
- **Participants**: Lead Agent
- **Deliverables**: Sprint plan document, task breakdown

### Daily Standup (Per Sprint)
- **Duration**: 5 minutes
- **Format**: Check progress against sprint goals
- **Tool**: Internal state tracking via `todo` tool

### Sprint Review (Post-Sprint)
- **Duration**: 1-2 hours
- **Participants**: All roles
- **Deliverables**: Updated docs, pushed code

### Sprint Retrospective (Post-Sprint)
- **Duration**: 1 hour
- **Participants**: Lead Agent
- **Deliverables**: Improvement notes for next sprint

---

## 📊 Task Assignment

### Task Granularity
- Small tasks: 1 file, ~100 lines → single agent
- Medium tasks: 3-5 files, ~500 lines → delegated to sub-agent
- Large tasks: 10+ files → delegated with parallel execution

### Priority System

| Priority | Description | Timeline |
|----------|-------------|----------|
| ⭐⭐⭐⭐⭐ | Critical — blocks other work | Must do this sprint |
| ⭐⭐⭐⭐ | High — important but not blocking | Do after priority 1 |
| ⭐⭐⭐ | Medium — nice to have | Backlog if time allows |
| ⭐⭐ | Low — optional | Future sprint |
| ⭐ | Trivial — polish | Icebox |

---

## 🛠️ Tools & Environment

### Primary Development Environment
- **OS**: Ubuntu 25.10 ARM64
- **Shell**: Bash via Hermes terminal
- **Python**: 3.11 (venv at `venv-proot/`)
- **Process Manager**: PM2 (single process: `aeryn-api`)

### Agent Tools Available
| Category | Tools |
|----------|-------|
| **File I/O** | `read_file`, `write_file`, `patch`, `search_files` |
| **Terminal** | `terminal`, `execute_code`, `process` |
| **Delegation** | `delegate_task` (parallel sub-agents) |
| **Memory** | `memory`, `session_search` |
| **Web** | `web_search`, `web_extract` |
| **Skills** | `skill_view`, `skill_manage`, `skills_list` |

### Environment Constraints
- No Docker — native PM2 deployment
- No PostgreSQL — SQLite only (errors expected, system handles gracefully)
- No GPU — CPU-only inference
- 11GB RAM (7.5GB used, 3.7GB available)

---

## 📋 Communication Protocol

### Code Reviews
- All code changes must be reviewed by Lead Agent
- Review checklist:
  - [ ] No test doubles
  - [ ] Follows existing patterns
  - [ ] Tests pass (661 baseline)
  - [ ] Documentation updated

### Issue Tracking
Issues are tracked via GitHub Issues, but development is autonomous:
- No human review required
- Full autonomous approval granted
- Issues created for major blockers only

### Change Management
- All changes go through `git`
- Branch: `main` (no feature branches)
- Commit messages follow: `type(scope): description`
- Push to `origin/main` after test verification

---

## 🏆 Quality Standards

### Definition of Done
A sprint is complete when:
1. All planned features implemented with real code
2. All 661 tests pass
3. Zero test doubles in production code
4. All documentation updated
5. Pushed to `origin/main`

### Zero Test Double Rule
- **No mocks, stubs, fakes, or doubles in production code**
- Tests must exercise real functionality
- `grep -rn "unittest.mock" aeryn_core/ apps/` → must return 0

### Performance Baseline
- API response time: < 500ms for simple endpoints
- Dashboard load: < 2 seconds
- Tests: < 60 seconds for full suite

---

*Team structure v59.0 — autonomous multi-agent system. Updated 2026-08-30.*
