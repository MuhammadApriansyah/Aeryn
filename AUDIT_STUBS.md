# Audit: Small Files (< 20 lines) in aeryn_core

> Generated during P4 audit. 69 files < 20 lines found.
> Conclusion: **No deletion needed** — majority are `__init__.py` (package markers) + intentional agent scaffolds.

## Breakdown

### `__init__.py` (package markers) — KEEP
- `aeryn_core/utils/__init__.py` (5 lines)
- `aeryn_core/reasoning/__init__.py` (5 lines)
- `aeryn_core/hermes/__init__.py` (2 lines)
- `aeryn_core/billing/__init__.py` (7 lines)
- `aeryn_core/mcp/__init__.py` (3 lines)
- `aeryn_core/multi_agent/__init__.py` (2 lines)
- `aeryn_core/integrations/__init__.py` (2 lines)
- ... (total ~25 `__init__.py`)

**Reason**: Required for Python package discovery. Deleting breaks imports.

### Agent Scaffolds (intentional) — KEEP
- `aeryn_core/agents/division_1_creative/sub_agent_pov/agent.py` (12 lines)
- `aeryn_core/agents/division_1_creative/sub_agent_style/agent.py` (14 lines)
- `aeryn_core/agents/division_3_reasoning/sub_agent_critique/agent.py` (16 lines)
- `aeryn_core/agents/division_3_reasoning/middleware.py` (17 lines)

**Reason**: These are template agents loaded by `multi_agent` orchestrator. Small because logic is in base classes.

### Modules with only `__init__.py` (no impl yet) — MONITOR
- `aeryn_core/wizard/` — scaffold only
- `aeryn_core/gallery/` — scaffold only
- `aeryn_core/preview/` — scaffold only
- `aeryn_core/undo/` — scaffold only
- `aeryn_core/help/` — scaffold only

**Action**: Documented as "planned modules". Not dead code, but not yet implemented.

## Recommendation
No cleanup action required. The 69 "small files" are structural, not defective.
If future cleanup wanted: implement `wizard/`, `gallery/`, `preview/` or remove their directories.
