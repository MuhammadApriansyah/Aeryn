# Arsip V33-Hygiene (2026-08-25)

Modul TIDAK TERJANGKAU dari entry point mana pun (daemon/gateway/chat)
dan tidak punya test: dipindah dari jalur produksi via `git mv`.

Kriteria: import-graph audit AST dari scripts/aeryn_daemon.py,
scripts/discord_gateway.py, run_aeryn_chat.py → zero reachable + zero test.

RESTORE: `git mv _archive/v33-hygiene/<path> <path_asal>`
Modul ber-test yang sengaja DIPARKIR (tidak diarsip): dynamic_schema,
memory_consolidation, memory_curator, multi_agent, verification_gate.
