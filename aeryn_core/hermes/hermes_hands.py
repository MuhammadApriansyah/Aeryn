"""V37 — Hermes Hands: delegasi kerja berat ke Hermes via CLI one-shot.

Aeryn (otak kanan) sesekali butuh TANGAN: kerja berat (build, refactor,
riset panjang) didelegasikan ke Hermes (otak kiri) lewat CLI
`hermes chat -q '<task>'`. Ini MAHAL (satu full agent run per panggilan),
jadi dibatasi:

1. Guard input — task kosong / < 10 karakter ditolak tanpa spawn.
2. Cap harian — counter JSON di Personalisasi/Database/
   hermes_hands_usage.json {date, count}; default 20/hari
   (override env AERYN_HERMES_HANDS_DAILY). Lewat cap → gagal tanpa spawn.
3. Timeout — proses di-kill saat lewat batas, ok=False.
4. Output dipotong 4000 karakter TERAKHIR (kesimpulan biasanya di ekor).

Modul ini TIDAK register ke registry daemon — wiring dilakukan orkestrator.
"""
import json
import os
import shutil
import subprocess
import time
from aeryn_core.utils.config import BASE_DIR, DATABASE_DIR

_DB_DIR = DATABASE_DIR
COUNTER_FILE = os.path.join(_DB_DIR, "hermes_hands_usage.json")

DEFAULT_MAX_PER_DAY = 20
DEFAULT_TIMEOUT_S = 240
OUTPUT_TAIL_CHARS = 4000
MIN_TASK_CHARS = 10


def _max_per_day() -> int:
    """Cap harian; override via env AERYN_HERMES_HANDS_DAILY."""
    try:
        return int(os.environ.get("AERYN_HERMES_HANDS_DAILY",
                                  str(DEFAULT_MAX_PER_DAY)))
    except ValueError:
        return DEFAULT_MAX_PER_DAY


def _today() -> str:
    return time.strftime("%Y-%m-%d")


def _load_counter() -> dict:
    try:
        with open(COUNTER_FILE) as f:
            data = json.load(f)
        if isinstance(data, dict) and "date" in data and "count" in data:
            return data
    except (OSError, ValueError):
        pass
    return {"date": _today(), "count": 0}


def _save_counter(data: dict) -> None:
    os.makedirs(os.path.dirname(COUNTER_FILE), exist_ok=True)
    tmp = COUNTER_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, COUNTER_FILE)


def _check_and_bump_cap() -> dict:
    """Cek cap harian + naikkan counter atomik. Return {'allowed': bool}."""
    data = _load_counter()
    today = _today()
    if data.get("date") != today:  # rollover tanggal ganti
        data = {"date": today, "count": 0}
    if data["count"] >= _max_per_day():
        return {"allowed": False}
    data["count"] += 1
    _save_counter(data)
    return {"allowed": True}


def ask_hermes(task: str, timeout_s: int = DEFAULT_TIMEOUT_S) -> dict:
    """Delegasikan satu task ke Hermes CLI one-shot (`hermes chat -q`).

    Return {ok, output, duration_ms} saat sukses,
    atau {ok: False, error} saat ditolak/timeout/gagal.
    """
    # 1. Guard input
    if not isinstance(task, str) or len(task.strip()) < MIN_TASK_CHARS:
        return {"ok": False,
                "error": f"task terlalu pendek/kosong (min "
                         f"{MIN_TASK_CHARS} karakter)"}

    # 1b. V38.4-SEC — task yang meminta Hermes membocorkan secrets ditolak
    # (Hermes punya akses lebih luas; jangan jadi jalur eksfiltrasi).
    low = task.lower()
    for marker in (".env", "auth.json", "api_key", "apikey", "password",
                   "token", "secret", "credential"):
        if marker in low:
            return {"ok": False,
                    "error": f"task menyinggung '{marker}' — delegasi ke "
                             f"Hermes untuk materi sensitif tidak diizinkan"}

    # 2. Cap harian — tolak TANPA spawn bila lewat
    cap = _check_and_bump_cap()
    if not cap["allowed"]:
        return {"ok": False, "error": "daily cap"}

    # 3. Spawn Hermes one-shot
    hermes_bin = shutil.which("hermes") or "hermes"
    started = time.monotonic()
    try:
        proc = subprocess.run(
            [hermes_bin, "chat", "-q", task],
            capture_output=True, text=True, timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False,
                "error": f"timeout setelah {timeout_s}s — proses dikill"}
    except FileNotFoundError:
        return {"ok": False, "error": "binary 'hermes' tidak ditemukan di PATH"}
    except Exception as e:  # noqa: BLE001 — jangan crash caller Aeryn
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    duration_ms = int((time.monotonic() - started) * 1000)

    # 4. Potong 4000 char TERAKHIR
    out = proc.stdout or ""
    truncated = len(out) > OUTPUT_TAIL_CHARS
    return {
        "ok": proc.returncode == 0,
        "output": out[-OUTPUT_TAIL_CHARS:],
        "duration_ms": duration_ms,
        "truncated": truncated,
        "exit_code": proc.returncode,
    }


ASK_HERMES_SCHEMA = {
    "type": "function",
    "function": {
        "name": "ask_hermes",
        "description": (
            "Delegasikan satu kerja berat ke Hermes (one-shot, mahal — "
            "maks 20x/hari). Task harus self-contained dan spesifik; hasil "
            "berupa teks maks 4000 karakter terakhir."),
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Deskripsi task lengkap untuk Hermes",
                },
            },
            "required": ["task"],
        },
    },
}
