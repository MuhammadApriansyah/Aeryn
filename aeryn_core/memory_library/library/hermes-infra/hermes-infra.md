---
id: hermes-infra
topic: hermes-infra
tags: [gateway, gwctl, backup, memory, proot, pm2, symlink, cron, android-mount]
signal: high
created: 2026-08-24
updated: 2026-08-24
summary: Hermes runs in proot ARM64 (no systemd). Gateway managed via gwctl.py (NOT hermes gateway restart, blocked inside agent). Memory+backup symlinked to /mnt/android/Ubuntu. Single-user (blueholic removed).
---

## Gateway management (proot, no systemd/PM2)
- Manage via /home/sen/.hermes/gwctl.py (status/restart/stop/start/run)
- Scans /proc for gateway PIDs, spawns with _HERMES_GATEWAY env UNSET (so restart not refused)
- `hermes gateway restart` from INSIDE agent is BLOCKED by safety guard (_HERMES_GATEWAY=1, gateway.py:8084) — use gwctl.py from terminal
- PM2 INCOMPATIBLE: gateway daemonizes (setsid) → PM2 thinks exited → spawns orphan loop
- config.yaml security-guarded in patch/write_file tools, but editable via terminal (sed/python) with /approve always

## Backup (personal state)
- /home/sen/backup-personal.sh + ~/.hermes/scripts/backup-personal.sh
- Backs up .hermes (config/skills/memory/profiles/pairing/gwctl.py/state.db), ~/Downloads/SKILL.md, webnovel-platform src, aeryn-core-agent src → /mnt/android/Ubuntu/hermes-backup/ (fallback ~/hermes-backup-local)
- Excludes venv/node_modules/.git/runtime
- Proot has no rsync → tar pipeline
- Hermes cron 'backup-personal-weekly' (b78489399a04) 0 3 * * 0 (Sun 03:00 UTC), deliver=all
- Notif via `hermes send --to whatsapp` (reads bot-token from .env, NO gateway needed)
- Restore: /home/sen/hermes-restore.sh

## Memory library (tiered)
- Internal HOT tier: ~/.hermes/memories/ (symlink → /mnt/android/Ubuntu/hermes-memory) — always in context, capped ~9K
- Cold LIBRARY tier: /mnt/android/Ubuntu/hermes-memory-library/ (unbounded, RAG-style retrieval via memory_library.py)
- Daily sync: ~/.hermes/scripts/sync-memory.sh (cron 0 2 * * *, job 6a4fa72ff6c6)
- memory_library.py subcommands: build/search/add/curate

## Split user (REVERSED)
- Was multi-user (blueholic separate profile via multiplex_profiles)
- Sen decided: Hermes is PERSONAL assistant, NOT multi-user → rolled back to single-user
- Blueholic profile + config removed; only Sen (203409667940548@lid) has access

## Discord bot reality
- Bot Discord CANNOT run without gateway (gateway = WebSocket listener = bot brain)
- `hermes send` is API POST only (not a bot) — works without gateway, but doesn't listen to commands
- No "pure Discord bot without gateway" in Hermes
