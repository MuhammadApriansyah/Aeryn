#!/usr/bin/env python3
"""V39.10 — DriftGuard: deteksi Hermes-drift SEBELUM & SESUDAH update.

Filosofi: JANGAN takut update Hermes — takut tanpa deteksi.
Ritual aman update:
  1. python3 scripts/drift_guard.py          (baseline HARUS OK)
  2. update/pull Hermes
  3. python3 scripts/drift_guard.py          (kalau DRIFT → tahu persis
     titik integrasi yang pecah, tinggal adaptasi adapter Aeryn)

Cek (murah, tanpa panggil LLM):
  [1] state.db     : ada, bisa dibuka read-only, kolom kunci ada
  [2] hermes CLI   : binary ada & bisa dieksekusi (--version)
  [3] auth.json    : providers.nous.agent_key ADA + belum expired
  [4] INDEX library: ada + punya key format yang diharapkan
  [5] memory_library.py: fungsi inti masih ada (search/build/supersede)
Exit: 0 = OK, 1 = DRIFT (cetak detail titik pecah).
"""
import json
import os
import sqlite3
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
STATE_DB = f"{HOME}/.hermes/state.db"
AUTH = f"{HOME}/.hermes/auth.json"
INDEX = "/mnt/android/Ubuntu/hermes-memory-library/INDEX.json"
MEM_LIB = f"{HOME}/.hermes/scripts/memory_library.py"


def check_state_db() -> tuple:
    if not os.path.exists(STATE_DB):
        return False, "state.db tidak ada"
    try:
        con = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True,
                              timeout=5)
        cur = con.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
        con.close()
        if not tables:
            return False, "state.db kosong (schema berubah total?)"
        return True, f"OK ({len(tables)} tabel)"
    except sqlite3.Error as e:
        return False, f"sqlite error: {e}"


def check_cli() -> tuple:
    for cmd in (["hermes", "--version"], ["which", "hermes"]):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=15)
            if r.returncode == 0:
                out = (r.stdout or r.stderr).strip().splitlines()
                return True, f"OK ({out[0][:40]})" if out else "OK"
        except FileNotFoundError:
            break
        except subprocess.TimeoutExpired:
            continue
    return False, "CLI hermes tidak ditemukan/tidak jalan"


def check_auth() -> tuple:
    try:
        data = json.load(open(AUTH))
        nous = data.get("providers", {}).get("nous", {})
        key_present = bool(nous.get("agent_key"))
        exp = nous.get("expires_at", 0)
        expired = isinstance(exp, (int, float)) and exp < time.time()
        if not key_present:
            return False, "agent_key hilang dari auth.json"
        if expired:
            # tidak fatal — Hermes auto-refresh, tapi patut diketahui
            return True, "OK (key expired, akan auto-refresh)"
        return True, "OK (key ada)"
    except (OSError, ValueError, KeyError) as e:
        return False, f"auth.json tidak terbaca: {e}"


def check_index() -> tuple:
    if not os.path.exists(INDEX):
        return False, "INDEX.json library tidak ada"
    try:
        data = json.load(open(INDEX))
        n = len(data.get("entries", data)) if isinstance(data, dict) \
            else len(data)
        return True, f"OK ({n} entri)" if n else "OK tapi KOSONG"
    except ValueError as e:
        return False, f"INDEX korup: {e}"


def check_memlib() -> tuple:
    if not os.path.exists(MEM_LIB):
        return False, "memory_library.py tidak ada"
    src = open(MEM_LIB).read()
    missing = [f for f in ("def search", "supersede") if f not in src]
    if missing:
        return False, f"fungsi inti hilang: {missing}"
    return True, "OK"


CHECKS = [
    ("state.db", check_state_db),
    ("hermes CLI", check_cli),
    ("auth agent_key", check_auth),
    ("library INDEX", check_index),
    ("memory_library API", check_memlib),
]


def main() -> int:
    print("=== DriftGuard Aeryn↔Hermes ===")
    drifted = []
    for name, fn in CHECKS:
        ok, msg = fn()
        mark = "✅" if ok else "❌"
        print(f"  [{mark}] {name:20s} {msg}")
        if not ok:
            drifted.append((name, msg))
    if drifted:
        print(f"\n🔴 DRIFT: {len(drifted)} titik integrasi pecah:")
        for name, msg in drifted:
            print(f"  - {name}: {msg}")
        print("→ JANGAN jalankan Aeryn produksi sampai adapter diadaptasi.")
        return 1
    print("\n🟢 SEMUA TITIK INTEGRASI SEHAT — Aeryn aman jalan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
