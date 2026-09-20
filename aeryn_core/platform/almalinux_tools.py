#!/usr/bin/env python3
"""V62.2 — FW2.2: AlmaLinux worker sebagai delegated toolchain (agent tool).

`almalinux_build`: build/pip-install paket berat DI DALAM AlmaLinux via proot
(wheel manylinux aarch64 prebuilt = detik). Register sebagai agent tool —
Aeryn delegasi kerja berat ke pelayannya.
Real APIs only — no test doubles.
"""

import os
import subprocess
import shlex

HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")
ALMA_ROOT = os.environ.get("AERYN_ALMA_ROOT", os.path.join(HOME, "almalinux"))

# Proot flags — LD_PRELOAD kosong (matikan termux-exec bionic) + -r absolut.
# Ini root-cause yang terpecahkan di Fase AL (SIGSYS via termux-exec).
_PROOT_BASE = [
    "env", "-u", "LD_LIBRARY_PATH", "LD_PRELOAD=",
    "proot", "-0", "-w", "/root",
    "-b", "/dev", "-b", "/proc", "-b", "/sys",
    "-r", ALMA_ROOT,
]
_ALMA_ENV = {"PATH": "/usr/local/bin:/usr/bin:/usr/sbin:/bin"}


def _proot_run(command: str, timeout: int = 300) -> dict:
    """Run a command inside AlmaLinux via proot. Real execution."""
    if not os.path.isdir(ALMA_ROOT):
        return {"ok": False, "output": "", "error": f"AlmaLinux rootfs tidak ada: {ALMA_ROOT}"}
    try:
        out = subprocess.run(
            [*_PROOT_BASE, "/usr/bin/env", f"PATH={_ALMA_ENV['PATH']}", "sh", "-c", command],
            capture_output=True, text=True, timeout=timeout,
        )
        return {
            "ok": out.returncode == 0,
            "output": (out.stdout or "")[:8000],
            "error": (out.stderr or "")[:2000],
            "returncode": out.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": "", "error": f"Timeout after {timeout}s di AlmaLinux"}
    except Exception as e:
        return {"ok": False, "output": "", "error": str(e)}


def almalinux_build(package: str, timeout: int = 300) -> dict:
    """pip install a package inside AlmaLinux (manylinux aarch64 prebuilt wheels).

    Args:
        package: nama paket pip (mis. "pydantic-core", "cryptography")
        timeout: detik (default 300)
    """
    if not package or not package.strip():
        return {"ok": False, "output": "", "error": "package kosong"}
    # Safety: hanya pip install <pkg> — blokir flag berbahaya
    pkg = package.strip()
    if any(c in pkg for c in (";", "|", "&", "$", "`", "\n")):
        return {"ok": False, "output": "", "error": "Karakter tidak aman di package name"}
    return _proot_run(f"pip install --no-input {shlex.quote(pkg)}", timeout)


def almalinux_shell(command: str, timeout: int = 120) -> dict:
    """Run an arbitrary shell command inside AlmaLinux via proot."""
    if not command or not command.strip():
        return {"ok": False, "output": "", "error": "command kosong"}
    return _proot_run(command, timeout)


def almalinux_status() -> dict:
    """AlmaLinux worker status: rootfs + python + pip versions."""
    if not os.path.isdir(ALMA_ROOT):
        return {"ok": False, "output": "", "error": f"rootfs tidak ada: {ALMA_ROOT}"}
    r = _proot_run(
        "cat /etc/os-release | head -2; python3.12 --version; pip --version | head -1",
        timeout=60,
    )
    return {"ok": r["ok"], "output": r["output"][:1000], "error": r["error"]}


def register(registry) -> None:
    """Register AlmaLinux worker tools into the PluginRegistry."""
    registry.register(
        "almalinux_build",
        "pip install package berat via AlmaLinux glibc-worker (wheel manylinux aarch64 prebuilt — detik)",
        handler=lambda package, timeout=300, **kw: almalinux_build(package, timeout),
        parameters={
            "type": "object",
            "properties": {
                "package": {"type": "string"},
                "timeout": {"type": "integer"},
            },
            "required": ["package"],
        },
        tags=["build", "wheel", "toolchain", "almalinux"],
        category="delegation",
    )
    registry.register(
        "almalinux_shell",
        "Run shell command di dalam AlmaLinux via proot (toolchain berat)",
        handler=lambda command, timeout=120, **kw: almalinux_shell(command, timeout),
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "integer"},
            },
            "required": ["command"],
        },
        tags=["shell", "toolchain", "almalinux"],
        category="delegation",
    )
    registry.register(
        "almalinux_status",
        "AlmaLinux worker status (rootfs/python/pip)",
        handler=lambda **kw: almalinux_status(),
        parameters={"type": "object", "properties": {}},
        tags=["status", "almalinux", "worker"],
        category="delegation",
    )
