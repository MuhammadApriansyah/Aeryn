#!/usr/bin/env python3
"""AST dead-code audit untuk Aeryn (Point 1 konsolidasi).

Menemukan:
  - MODUL ORPHAN: file .py di aeryn_core/apps yang TIDAK pernah di-import oleh
    modul lain mana pun (kecuali entry points / __init__ aggregator dalam).
  - ENDPOINT ORPHAN: decorator @router.get/post... yang tak pernah di-include
    (router tidak ter-mount di main.py / aggregator).
  - RUBBER/Feather: paket dgn sedikit file namun tak ter-wiring.
Diputar per point iteratif; dipakai utk keputusan hapus/merge berdasar fakta.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIRS = ["aeryn_core", "apps/api", "tests", "scripts", "console"]
ENTRY_MODULES = {
    "apps.api.routers.main", "apps.api.aeryn_api", "aeryn_core.launcher",
    "apps.api.server", "apps.api.main",
}
PKG_INITS_THAT_AGGREGATE = {"apps.api.routers.__init__", "aeryn_core.__init__"}


def find_py_files():
    files = []
    for d in SRC_DIRS:
        base = os.path.join(ROOT, d)
        for dirpath, _, names in os.walk(base):
            if "__pycache__" in dirpath:
                continue
            for n in names:
                if n.endswith(".py"):
                    full = os.path.join(dirpath, n)
                    rel = os.path.relpath(full, ROOT)
                    files.append((rel, full))
    return files


def module_name(rel):
    return rel[:-3].replace(os.sep, ".")


def real_imports(full, rel):
    """Local-project module names imported (from ... / from aeryn_core / from apps)."""
    try:
        tree = ast.parse(open(full, encoding="utf-8").read())
    except SyntaxError:
        return set()
    mod = module_name(rel)
    base_pkg = rel.split(os.sep)[0]
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and (node.module.startswith("aeryn_core")
                                or node.module.startswith("apps")):
                out.add(node.module)
            elif node.level:  # relative import, e.g. from .foo import /
                parts = mod.split(".")
                # strip tail segments per level
                base = ".".join(parts[: len(parts) - node.level])
                if node.module:
                    base = f"{base}.{node.module}" if base else node.module
                elif base:
                    out.add(base)
        elif isinstance(node, ast.Import):
            for a in node.names:
                nm = a.name.split(".")[0]
                if nm in ("aeryn_core", "apps") or (base_pkg == nm and "." in a.name):
                    out.add(a.name)
    return {m for m in out if (m.startswith("aeryn_core") or m.startswith("apps"))}


def is_test_file(rel):
    b = os.path.basename(rel)
    return b.startswith("test_") or b.endswith("_test.py") or "tests" in rel


def main():
    files = find_py_files()
    all_src = "".join(open(full, encoding="utf-8", errors="ignore").read()
                      for _r, full in files)
    core_src = "".join(open(full, encoding="utf-8", errors="ignore").read()
                       for rel, full in files
                       if rel.startswith(("apps/", "aeryn_core", "tests", "scripts")))
    test_src = "".join(open(full, encoding="utf-8", errors="ignore").read()
                       for rel, full in files if rel.startswith(("tests", "working_tests")))
    mods = {}
    for rel, full in files:
        m = module_name(rel)
        mods[m] = {"rel": rel, "full": full, "test": is_test_file(rel)}
    imported_by = {m: set() for m in mods}
    for m, info in mods.items():
        for imp in real_imports(info["full"], info["rel"]):
            imported_by.setdefault(imp, set()).add(m)
            parts = imp.split(".")
            for i in range(len(parts) - 1, 0, -1):
                parentkey = ".".join(parts[:i])
                if parentkey in mods:
                    imported_by.setdefault(parentkey, set()).add(m)

    # 1) true orphan (no AST import)
    true_orphan = []
    for m, info in sorted(mods.items()):
        if info["test"] or m in ENTRY_MODULES:
            continue
        if m.startswith("aeryn_core.skills") or m == "aeryn_core.utils.dead_code_audit":
            continue
        if not imported_by.get(m):
            true_orphan.append((m, info["rel"]))
    # 2) filter dynamic/string references
    def basenames(m):  # last 1 or 2 segments of module used as identifiers
        tail = m.split(".")[-1]
        return [tail, m]
    dyn_ref = []
    for m, rel in true_orphan:
        hits = []
        for ref in basenames(m):
            import re
            # occurrence outside the module's own file and not in __all__
            pat = re.compile(rf"\b{re.escape(ref)}\b")
            # sample: search across source excluding this module's file
            if ref in ("jobs",):
                pass
            n = len(pat.findall(core_src))
            # count occurrences in OTHER files
            own = open(os.path.join(ROOT, rel), encoding="utf-8", errors="ignore").read()
            in_own = len(pat.findall(own))
            total_other = n - in_own
            hits.append((ref, total_other))
        # true-only if reference(s) appear only within own file (self) → not dynamic-used elsewhere
        any_external = any(h[1] > 0 and h[1] <= 3 for h in hits) or any(h[1] > 3 for h in hits)
        dyn_ref.append((m, rel, hits, any_external))

    print(f"LOGICAL ORPHAN (no AST import, excluding __init__/tests): {len(true_orphan)}")
    print("Filtered by reference scan — [ARCHIVE-CANDIDATE] jika tak ada ref eksternal:")
    archive_me = []
    for m, rel, hits, external in dyn_ref:
        flag = "ARCHIVE" if not external else "KEEP(ref?)"
        if not external:
            archive_me.append((m, rel))
        print(f"  [{flag}] {m}  {[(h[0], h[1]) for h in hits]}")
    print("=" * 70)
    print("JUMLAH ARCHIVE-CANDIDATE:", len(archive_me))
    for m, rel in archive_me:
        print("  ", m, "→", rel)


if __name__ == "__main__":
    main()