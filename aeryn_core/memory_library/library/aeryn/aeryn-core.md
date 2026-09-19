---
id: aeryn-core
topic: aeryn
tags: [aeryn, arisylla, cognitive, sde, tensor, rust, planner, sub-agent]
signal: low
created: 2026-08-24
updated: 2026-08-24
summary: Aeryn = multi-agent persona (45 sub-agents, 5 divisions), applied universally not on-demand. Cognitive core = Python+Rust at ~/aeryn-core-agent. Persona SKILL.md lives in Downloads (NOT a Hermes skill).
superseded_by: aeryn-core-v30-plus
superseded_at: 2026-08-25
superseded_reason: arsitektur berubah di V30+, lihat entry baru
---


## Architecture
- Multi-agent AI persona system (45 sub-agents, cognitive architecture, 5 divisions)
- Applied universally rather than as on-demand skill
- Prefers practical implementations over pure theory; casual Indonesian+English

## Cognitive core (Aeryn-Core)
- Python+Rust at ~/aeryn-core-agent
- Daemon PM2 aeryn-core port 3010 FastAPI (/compile,/digest,/memory/<sid>,/health)
- Emotional tensor leaky integration, Rust memory vault, anti-injection governance, persists across sessions (Sen's choice)
- Rebuild .so: maturin develop --release in venv-proot

## V27 (2026-08-24)
- Agentic loop stable on free providers
- Fallback: OpenRouter :free daily quota exhausted → NVIDIA NIM meta/llama-3.1-8b-instruct (~1s); HTTPError/timeout → break to next candidate, DON'T raise (was hanging >10min)
- Guard: ONE tool-call/turn; tool exception fail-soft
- Planner heuristic-first for numbered goals (0 LLM calls), persist plans/, GET /agent/plan/{sid}
- max_wall_seconds=240 cuts slow runs
- Terminal tier power sandboxed: read-only whitelist + reject shell metachars + cwd lock; div4 gate rejects rm -rf → audit ANOMALIES_PRESENT
- Auto-promote native after 5x parity shadow
- Pra-V28: episodic memory → post-run reflection → activate division_1&3 (dead code) → emotion tensor→tone

## Persona file
- ~/Downloads/SKILL.md (Aeryn/Arisylla recursive persona, Stage V)
- Sen EXPLICIT: "jangan dijadikan skill hermes cuy" — keep logic in local file, develop recursive scale stronger
- When requested, keep complex cognitive/recursive architectures decoupled from Hermes core skills
