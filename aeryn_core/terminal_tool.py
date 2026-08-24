"""V27.2 — Terminal tool tier `power`: exec perintah dalam sandbox ketat.

Lapisan keamanan (meniru tool `terminal` Hermes tapi jauh lebih sempit):
1. WHITELIST command — hanya utilitas baca-am yang diizinkan eksplisit
2. Tidak ada shell metacharacter (;, |, &&, `, $(), redirect) → anti chain-injection
3. Working directory terkunci di sandbox roots
4. Timeout + output cap
5. Governance gate menilai SEBELUM eksekusi (tier power = track record ketat)
"""
import os
import subprocess

# Whitelist: read-only utilities yang aman untuk agen fase awal
WHITELIST = {
    "ls": ["ls"],
    "cat": ["cat"],
    "head": ["head"],
    "tail": ["tail"],
    "wc": ["wc"],
    "grep": ["grep"],
    "find": ["find"],
    "pwd": ["pwd"],
    "git status": ["git", "status"],
    "git log": ["git", "log", "--oneline", "-20"],
    "git diff": ["git", "diff", "--stat"],
}

SHELL_META = set(";|&`><$()\n\r")

MAX_OUTPUT = 20_000
DEFAULT_TIMEOUT = 15


def make_terminal(sandbox_roots):
    """Factory terminal tool — closure menyimpan roots yang diizinkan."""
    allowed = [os.path.expanduser(r) for r in sandbox_roots]

    def terminal(command: str, cwd: str = None):
        # 1. Parse command utama
        parts = command.strip().split()
        if not parts:
            return {"error": "empty command"}

        base = " ".join(parts[:2]) if command.startswith("git ") else parts[0]
        if base not in WHITELIST and parts[0] not in WHITELIST:
            return {"error": f"command '{parts[0]}' tidak di whitelist. "
                             f"Diizinkan: {sorted(WHITELIST)}"}

        # 2. Anti shell-injection: tolak metacharacter
        bad = [ch for ch in command if ch in SHELL_META]
        if bad:
            return {"error": f"karakter shell dilarang: {set(bad)} — "
                             f"satu command sederhana saja"}

        # 3. cwd harus di dalam sandbox
        workdir = os.path.realpath(os.path.expanduser(cwd or allowed[0]))
        if not any(workdir == os.path.realpath(r) or workdir.startswith(
                os.path.realpath(r) + os.sep) for r in allowed):
            return {"error": f"cwd '{workdir}' di luar sandbox roots {allowed}"}

        # 4. Eksekusi tanpa shell, dengan timeout & output cap
        try:
            argv = _build_argv(command)
            proc = subprocess.run(argv, cwd=workdir, shell=False,
                                  capture_output=True, text=True,
                                  timeout=DEFAULT_TIMEOUT)
            out = proc.stdout[:MAX_OUTPUT]
            err = proc.stderr[:2000]
            return {"exit_code": proc.returncode,
                    "stdout": out,
                    "stderr": err,
                    "truncated": len(proc.stdout) > MAX_OUTPUT}
        except subprocess.TimeoutExpired:
            return {"error": f"timeout {DEFAULT_TIMEOUT}s"}
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}

    return terminal


def _build_argv(command: str) -> list:
    """Bangun argv tanpa shell. Untuk git subcommand sisipkan flag whitelist."""
    parts = command.split()
    if parts[0] == "git":
        sub = " ".join(parts[:2])
        base = WHITELIST.get(sub)
        if base:
            return base + parts[2:]
        return parts
    if command.startswith("ls"):
        return ["ls", "-la"] + parts[1:] if "-la" not in parts else parts
    return parts


TERMINAL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "terminal",
        "description": (
            "Jalankan perintah baca-am dalam sandbox (whitelist: ls, cat, head, "
            "tail, wc, grep, find, pwd, git status/log/diff). Tanpa shell "
            "metacharacter. cwd harus di folder sandbox."),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cwd": {"type": "string",
                        "description": "folder kerja (default: root sandbox)"},
            },
            "required": ["command"],
        },
    },
}
