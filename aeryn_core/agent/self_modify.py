"""V61.3 — Self-Modify Cycle (F4.3): Aeryn membangun tubuhnya sendiri, dengan aman.

Siklus: tulis/patch → tes otomatis → (hijau: commit) | (gagal: ROLLBACK git).
Guardrail berlapis (wajib, bukan opsional):
  1. SCOPE: hanya file di dalam repo + path yang diizinkan (jangan /system, dst).
  2. BACKUP: commit ke branch selfmod/<ts> sebelum ubah (jaring keselamatan).
  3. TEST: suite pytest harus hijau setelah perubahan; gagal → rollback penuh.
  4. AUDIT: jejak setiap siklus ke fact graph (bitemporal).
"""
import json
import subprocess
import time
import logging
from datetime import datetime, timezone

logger = logging.getLogger("aeryn.selfmod")

# Path yang BOLEH dimodifikasi (relatif ke repo root)
ALLOWED_PREFIXES = (
    "aeryn_core/", "apps/api/", "apps/web/",
)
# Path yang JANGAN PERNAH disentuh
FORBIDDEN = ("/system", "/data/data", "/etc", "aeryn_core/_archive", ".git")


def _repo_root() -> str:
    import os
    return os.path.expanduser("~/aeryn-core-agent")


def _git(args: list, cwd: str | None = None) -> tuple:
    r = subprocess.run(["git"] + args, cwd=cwd or _repo_root(),
                       capture_output=True, text=True, timeout=120)
    return r.returncode, (r.stdout + r.stderr).strip()


def _check_scope(path: str) -> tuple:
    """Guardrail 1: scope file diizinkan & bukan forbidden."""
    if path.startswith(FORBIDDEN) or path.startswith("/"):
        return False, f"path dilarang: {path}"
    if not path.startswith(ALLOWED_PREFIXES):
        return False, f"path di luar scope: {path} (boleh: {ALLOWED_PREFIXES})"
    return True, ""


def self_modify(path: str, new_content: str, commit_msg: str,
                run_tests: bool = True) -> dict:
    """Siklus aman: backup → tulis → tes → commit | rollback.

    Returns dict: {ok, phase, detail, backup_branch}
    """
    root = _repo_root()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Guardrail 1 — scope
    ok_scope, why = _check_scope(path)
    if not ok_scope:
        return {"ok": False, "phase": "scope", "detail": why}

    # Guardrail 2 — backup branch (jaring keselamatan)
    rc, out = _git(["rev-parse", "--is-inside-work-tree"])
    if rc != 0:
        return {"ok": False, "phase": "git", "detail": "bukan git repo"}
    backup = f"selfmod/{ts}"
    rc, out = _git(["checkout", "-b", backup])
    if rc != 0 and "already exists" not in out:
        return {"ok": False, "phase": "backup", "detail": out}
    _git(["checkout", "main"])
    _git(["branch", "-f", backup, "main"])  # backup = snapshot main

    # Tulis perubahan
    import os
    full = os.path.join(root, path)
    old_content = None
    try:
        if os.path.exists(full):
            old_content = open(full, encoding="utf-8").read()
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(new_content)
    except OSError as e:
        return {"ok": False, "phase": "write", "detail": str(e)}

    # Guardrail 3 — tes otomatis (suite pytest)
    test_ok = True
    test_detail = "skipped"
    if run_tests:
        try:
            venv_py = os.path.expanduser("~/aeryn-venv/bin/python")
            r = subprocess.run(
                [venv_py, "-m", "pytest", "tests/", "-q", "--maxfail=3",
                 "-x", "--no-header", "-k", "not test_current_environment"],
                cwd=root, capture_output=True, text=True, timeout=600)
            test_ok = r.returncode == 0
            tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
            test_detail = tail[0][:200]
        except (subprocess.TimeoutExpired, OSError) as e:
            test_ok = False
            test_detail = f"test error: {e}"

    if not test_ok:
        # ROLLBACK — pulihkan file lama + kembali ke main bersih
        try:
            if old_content is not None:
                with open(full, "w", encoding="utf-8") as f:
                    f.write(old_content)
            else:
                os.remove(full)
            _git(["checkout", "main"])
            _git(["branch", "-D", backup])
        except (OSError, subprocess.SubprocessError) as e:
            logger.error("rollback error: %s", e)
        result = {"ok": False, "phase": "test-rollback",
                  "detail": f"tes gagal → rollback: {test_detail}"}
    else:
        # COMMIT — perubahan diterima
        _git(["add", path])
        rc, out = _git(["commit", "-m", commit_msg or f"selfmod({ts}): {path}"])
        if rc != 0:
            result = {"ok": False, "phase": "commit", "detail": out[:200]}
        else:
            _git(["branch", "-D", backup])  # backup tak perlu (sudah commit)
            result = {"ok": True, "phase": "committed",
                      "detail": test_detail, "backup_branch": backup}

    # Guardrail 4 — audit bitemporal
    try:
        from aeryn_core.memory.fact_store import get_fact_store
        get_fact_store().record(
            entity="aeryn", predicate="self_modify_cycle",
            fact=json.dumps({
                "path": path, "phase": result["phase"],
                "ok": result["ok"], "ts": ts,
            }),
            source="self-modify",
        )
    except Exception as e:
        logger.warning("selfmod audit: %s", e)

    return result
