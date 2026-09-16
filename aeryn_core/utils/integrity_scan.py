#!/usr/bin/env python3
"""P2 deep — Integritas kode Aeryn: scan 3 anti-pola.

1) ERROR-HANDLING: `except: pass` / pengecualian ditelan mentah (no log).
2) RETURN HARDCODED/placeholder di router: return literal tanpa kerja nyata.
3) TEST-DOUBLE di file tes: mock/patch/MagicMock/Stub.

Output: ringkasan jumlah + lokasi, untuk ditindaklanjuti jadi nyata.
"""
import ast
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # aeryn-core-agent (dirname=.../aeryn_core/utils)
SCAN = [
    os.path.join(ROOT, "apps", "api", "routers"),
    os.path.join(ROOT, "aeryn_core"),
]


def py_files(base):
    for dirpath, _, files in os.walk(base):
        if dirpath.startswith(os.path.join(ROOT, "aeryn_core", "_archive")):
            continue
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(dirpath, f)


def scan_error_swallow():
    """except ...: pass  (dan bare except) — error ditelan."""
    hits = []
    for base in SCAN:
        for fp in py_files(base):
            src = open(fp, encoding="utf-8", errors="ignore").read()
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    body_is_pass = len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
                    if body_is_pass:
                        rel = os.path.relpath(fp, ROOT)
                        how = "bare except" if node.type is None else "except aliased-pass"
                        hits.append((rel, node.lineno, how))
    return hits


def scan_hardcoded_return():
    """Return literal placeholder di router: `return {...}` tanpa panggilan."""
    hits = []
    base = os.path.join(ROOT, "apps", "api", "routers")
    for fp in py_files(base):
        src = open(fp, encoding="utf-8", errors="ignore").read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for fn in ast.walk(tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = fn.body
                last = body[-1] if body else None
                if isinstance(last, ast.Return) and isinstance(last.value, ast.Dict):
                    all_lit = all(isinstance(k, ast.Constant) and isinstance(v, ast.Constant)
                                  for k, v in zip(last.value.keys, last.value.values))
                    # kerja nyata = ada panggilan fungsi/attribut di body selain return
                    work = any(isinstance(n, (ast.Call, ast.Attribute))
                               for s in body[:-1] for n in ast.walk(s))
                    if all_lit and not work and len(last.value.keys) >= 2:
                        rel = os.path.relpath(fp, ROOT)
                        hits.append((rel, fn.name, fn.lineno))
    return hits


def scan_test_doubles():
    """File tes yang pakai mock/patch/MagicMock/Stub."""
    hits = []
    test_dir = os.path.join(ROOT, "tests")
    for fp in py_files(test_dir):
        src = open(fp, encoding="utf-8", errors="ignore").read()
        pats = ["unittest.mock", "MagicMock", "@patch(", "@mock.patch", "monkeypatch",
                "MagicMock()", "create_mock"]
        if any(p in src for p in pats):
            rel = os.path.relpath(fp, ROOT)
            hits.append(rel)
    return hits


def main():
    print("=== 1) ERROR HANDLING (except pass / bare) ===")
    sw = scan_error_swallow()
    print(f"  total: {len(sw)}")
    for rel, ln, how in sw[:40]:
        print(f"   {rel}:{ln}  [{how}]")
    print(f"  …(sisa {max(0, len(sw)-40)} lagi)" if len(sw) > 40 else "")

    print("\n=== 2) RETURN HARDCODED (literal placeholder di router) ===")
    hc = scan_hardcoded_return()
    print(f"  total: {len(hc)}")
    for rel, name, ln in hc[:40]:
        print(f"   {rel}:{ln}  def {name}")
    print(f"  …(sisa {max(0, len(hc)-40)} lagi)" if len(hc) > 40 else "")

    print("\n=== 3) TEST-DOUBLE di tests/ ===")
    td = scan_test_doubles()
    print(f"  total file: {len(td)}")
    for f in td[:40]:
        print(f"   {f}")
    print(f"  …(sisa {max(0, len(td)-40)} lagi)" if len(td) > 40 else "")


if __name__ == "__main__":
    main()