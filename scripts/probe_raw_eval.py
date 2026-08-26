#!/usr/bin/env python3
"""V42.12 — Probe: AST scan semua modul + scripts untuk pola raw-eval/exec.

Probe M55–M65 rekursif: cari raw_eval/exec yang bukan test.
Dijalankan setelah setiap rilis V39.x untuk audit keamanan berkala.
"""
import ast
import glob
import os
import sys

BASE = os.path.expanduser("~/aeryn-core-agent")
if __name__ != "__main__" and BASE not in sys.path:
    sys.path.insert(0, BASE)

SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", "Personalisasi"}

def find_raw_exec():
    found = []
    for path in sorted(glob.glob(f"{BASE}/**/*.py", recursive=True)):
        if any(s in path for s in SKIP_DIRS):
            continue
        try:
            tree = ast.parse(open(path).read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and
                    isinstance(node.func, ast.Name) and
                    node.func.id in ("eval", "exec")):
                # cek apakah aman (test only / sandbox)
                if "test" in path or "sandbox" in path:
                    continue
                rel = os.path.relpath(path, BASE)
                found.append(f"{rel}:{node.lineno} ({node.func.id})")
    return found

if __name__ == "__main__":
    results = find_raw_exec()
    if results:
        print("RAW eval/exec ditemukan:")
        for r in results:
            print(f"  {r}")
        print(f"\n🚨 {len(results)} titik raw eval/exec — perlu audit!")
        sys.exit(1)
    else:
        print("✅ Tidak ada raw eval/exec — semua safe.")
        sys.exit(0)
