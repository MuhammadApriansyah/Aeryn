V61.1 — Konsolidasi batch 1 (arsip dead-code)

Tanggal: 2026-09-13
Metode: audit AST (dead_code_audit.py) — modul tanpa SATU pun import nyata
  dan tanpa referensi eksternal (identitas unik, count = 0 di seluruh source).
Modul di-MOVE (bukan dihapus) ke ./aeryn_core/_archive/consolidation_v1/
  agar reversibel & non-destruktif.

Peta PATH ASLI -> ARSIP:
  aeryn_core/auth/rate_rust.py                 -> rate_rust.py        (stub Rust rate-limit)
  aeryn_core/cost/model_router.py              -> model_router.py     (cost model routing — unused)
  aeryn_core/cost/token_monitor.py             -> token_monitor.py    (cost token usage — unused)
  aeryn_core/platform/realtime_rust.py         -> realtime_rust.py    (stub Rust realtime)
  aeryn_core/platform/websocket_rust.py        -> websocket_rust.py   (stub Rust websocket)
  aeryn_core/plugin_system/builtin/auth_plugin.py -> auth_plugin.py   (plugin auth — belum ditarik)
  aeryn_core/utils/tui_monitor.py              -> tui_monitor.py      (TUI monitor unused)

Alasan masukkan ke batch 1: nama modul unik, tidak muncul di MANA pun
  dalam codebase (import AST ATAU string/dynamic), dan parent __init__
  tidak wildcard-import. MOVE reversibel via git.

Verifikasi: `from apps.api.routers.main import app` sukses; /health sehat.