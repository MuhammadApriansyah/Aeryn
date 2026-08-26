"""V37.5-SEC — SecurityKernel: lapisan keamanan terpusat (defense in depth).

Semua tool yang menyentuh file/sumber daya sensitif WAJIB melewati kernel
ini. Prinsip:
1. SECRET ZONES — path yang selalu dilindungi, di mana pun lokasinya
   (termasuk DI DALAM sandbox: .env, memori pribadi, state internal).
2. SOURCE IMMUTABILITY — kode sumber & konfigurasi runtime tidak boleh
   ditimpa lewat tool agent.
3. PATH VALIDATION — realpath + anti-traversal untuk semua path argumen.
4. Fail-closed: ragu → tolak.
"""
import os

# Direktori/file yang TIDAK BOLEH dibaca/tulis oleh agent via tool,
# sekalipun berada di dalam sandbox roots.
SECRET_BASENAMES = {
    ".env", ".env.local", ".env.production",
    "core_memory.json", "social.json",
    "parity_ledger.json", "hermes_hands_usage.json",
    "auth.json", "credentials.json", "*.pem", "*.key",
}

# V38.8 — episode log berisi goal SEMUA user (privacy lintas-user):
# fs_read mentah ke file ini = user A bisa baca pertanyaan user B.
SECRET_BASENAMES.add("episodes.jsonl")

# V38.7 — suffix audit/log juga dilindungi (append-only trail tidak boleh
# dibaca-dimodifikasi via tool agent; keaslian jejak = prasyapat audit)
PROTECTED_SUFFIXES = (".audit.jsonl",)

SOURCE_SUFFIXES = (".py", ".js", ".ts", ".rs", ".toml", ".yaml", ".yml")

# Sub-direktori source code (relatif ke sandbox root) yang tidak boleh
# ditulis via tool — hanya git/CI/orkestrator yang boleh mengubahnya.
WRITE_PROTECTED_DIRS = ("aeryn_core", "scripts", "tests", "src")


def _realpath(p: str) -> str:
    return os.path.realpath(os.path.expanduser(p))


def _basename_matches(name: str, pattern: str) -> bool:
    if pattern.startswith("*"):
        return name.endswith(pattern[1:])
    return name == pattern


def check_path(path: str, mode: str = "read",
               sandbox_roots: list = None) -> tuple:
    """Validasi satu path. Returns (ok, reason).

    mode: 'read' | 'write'. Urutan cek fail-closed:
      1. secret basenames → tolak (read & write)
      2. source dirs utk write → tolak
      3. bila sandbox_roots diberikan → path wajib di dalamnya
    """
    if not path or not isinstance(path, str):
        return False, "path kosong"
    rp = _realpath(path)
    base = os.path.basename(rp).lower()
    for pat in SECRET_BASENAMES:
        if _basename_matches(base, pat):
            return False, f"file sensitif '{base}' dilindungi SecurityKernel"
    # V38.7 — audit trail dilindungi (baca & tulis): jejak harus asli
    for suf in PROTECTED_SUFFIXES:
        if base.endswith(suf):
            return False, (f"file audit '{base}' dilindungi SecurityKernel "
                           f"(jejak tidak boleh diubah agent)")
    # V38.8 — direktori sessions/ (riwayat privat per-user) tidak boleh
    # dibaca melintas via path direktori
    for part in rp.split(os.sep):
        if part == "sessions" and mode == "read":
            return False, ("direktori 'sessions' berisi riwayat privat "
                           "per-user — akses lintas user diblokir")
        if part == "episodes" and mode == "read":
            return False, ("direktori 'episodes' berisi log gabungan semua "
                           "user — akses langsung diblokir")
    if mode == "write":
        for d in WRITE_PROTECTED_DIRS:
            parts = rp.split(os.sep)
            if d in parts:
                return False, (f"'{d}/' write-protected: ubah lewat git "
                               f"(orkestrator), bukan tool agent")
    if sandbox_roots:
        inside = any(
            rp == root or rp.startswith(root + os.sep)
            for root in (_realpath(r) for r in sandbox_roots))
        if not inside:
            return False, f"path di luar sandbox: {rp}"
    return True, ""


def make_secure_terminal(sandbox_roots):
    """Wrapper terminal: validasi path argumen + cwd via kernel."""
    from aeryn_core.terminal_tool import make_terminal
    inner = make_terminal(sandbox_roots)

    def secure_terminal(command: str, cwd: str = None):
        parts = command.strip().split()
        # cek setiap token (termasuk yang mulai '-': bisa flag dengan nilai
        # path seperti --output=/x atau -fprint/etc/x) dan pasangan flag
        # yang butuh argumen file.
        tokens = parts[1:] if parts else []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            candidate = None
            if "=" in tok and tok.startswith("-"):
                candidate = tok.split("=", 1)[1]  # --output=/path/evil
            elif tok.startswith("-") and not tok.startswith("--"):
                # flag pendek: nilai path bisa menempel (-fprint/etc/x)
                # atau di token berikutnya (-o /path/x)
                if len(tok) > 2 and ("/" in tok):
                    candidate = tok[2:] if not tok[2:].startswith("/") else tok[2:]
                    if not candidate.startswith("/"):
                        candidate = "/" + candidate  # -fprint/etc/x -> /etc/x
                else:
                    nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
                    if nxt and (nxt.startswith(("/", "~")) or "/" in nxt):
                        candidate = nxt
                        i += 1
            elif not tok.startswith("-"):
                candidate = tok
            if candidate:
                ok, reason = check_path(candidate, "read", sandbox_roots)
                if not ok:
                    return {"error": f"SecurityKernel: {reason}"}
            i += 1
        if cwd:
            ok, reason = check_path(cwd, "read", sandbox_roots)
            if not ok:
                return {"error": f"SecurityKernel: {reason}"}
        return inner(command, cwd)
    return secure_terminal
