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
  [6] social.json : tidak ada test artifacts / traversal keys (V39.10f)
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

# V39.10f — social.json audit constants
SOCIAL_PATH = os.path.join(
    os.path.expanduser("~/aeryn-core-agent/Personalisasi/Database"),
    "social.json")
FORBIDDEN_KEY_MARKERS = ("smoke", "test", "parity", "chaos-", "fbtest",
                         "dttest", "mathlive", "reminder", "__test__",
                         "probe")
FORBIDDEN_KEY_PATTERNS = ("../", "../../", "\\", "/etc/")


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
        # New format: credential_pool.nous (list of credential dicts)
        pool = data.get("credential_pool", {})
        nous_list = pool.get("nous", [])
        if nous_list:
            # Any nous credential present = auth available
            return True, f"OK (credential_pool.nous: {len(nous_list)} cred)"
        # Old format: providers.nous.agent_key (single string)
        nous = data.get("providers", {}).get("nous", {})
        key_present = bool(nous.get("agent_key"))
        exp = nous.get("expires_at", 0)
        expired = isinstance(exp, (int, float)) and exp < time.time()
        if not key_present:
            return False, "agent_key hilang dari auth.json"
        if expired:
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


def check_social_memory() -> tuple:
    """V39.10f — audit social.json: cegah test artifacts/traversal leak."""
    if not os.path.exists(SOCIAL_PATH):
        return True, "OK (social.json belum ada, akan dibuat otomatis)"
    try:
        data = json.load(open(SOCIAL_PATH))
    except ValueError as e:
        return False, f"social.json korup: {e}"
    bad_people = []
    people = data.get("people", {})
    for key in people:
        k = str(key)
        if any(p in k for p in FORBIDDEN_KEY_PATTERNS):
            return False, f"traversal key ditemukan: {k}"
        kl = k.lower()
        if any(m in kl for m in FORBIDDEN_KEY_MARKERS):
            bad_people.append(k)
    bad_channels = []
    channels = data.get("channels", {})
    for key in channels:
        k = str(key)
        if any(p in k for p in FORBIDDEN_KEY_PATTERNS):
            return False, f"traversal key di channels: {k}"
        kl = k.lower()
        if any(m in kl for m in FORBIDDEN_KEY_MARKERS):
            bad_channels.append(k)
    if bad_people or bad_channels:
        return False, (f"test artifacts: {len(bad_people)} people, "
                       f"{len(bad_channels)} channels tersisa")
    found_sen = any(p.get("nama") == "Sen" for p in people.values())
    sen_ok = "Sen present" if found_sen else "Sen NOT found"
    return True, f"OK ({len(people)} people, {sen_ok})"


CHECKS = [
    ("state.db", check_state_db),
    ("hermes CLI", check_cli),
    ("auth agent_key", check_auth),
    ("library INDEX", check_index),
    ("memory_library API", check_memlib),
    ("social_memory", check_social_memory),
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
