"""Multimodal Input (RM9) — voice STT + gambar via sensor/gateway.

Sesuai Aeryn_Identity.md §15 (Multimodal Input) + §13 (Environment
Interaction):
- tool_voice_input: termux-api speech-to-text (STT via mic HP — Termux:API
  app, tanpa pkg tambahan, tanpa cloud dependency)
- tool_image_capture: termux-api camera (foto via kamera HP — multimodal
  input sensor)
- tool_image_describe: gambar → deskripsi (via LM vision bila tersedia,
  fallback error eksplisit)

Real API only — no test doubles: termux-api nyata + LM nyata.
"""

import json
import subprocess
import base64
import os
from typing import Dict, Any


def tool_voice_input(timeout_s: int = 15) -> Dict[str, Any]:
    """Voice → teks via termux-speech-to-text (mic HP, sensor lokal).

    Butuh izin RECORD_AUDIO di Termux:API. Return teks yang didengar.
    """
    try:
        r = subprocess.run(["termux-speech-to-text"], capture_output=True,
                           timeout=timeout_s + 15)
        if r.returncode != 0:
            err = r.stderr.decode()[:150]
            return {"ok": False, "error": f"speech-to-text rc={r.returncode}: {err}"}
        text = (r.stdout.decode() or "").strip()
        if not text or text == "}":
            return {"ok": False, "error": "tidak ada suara terdeteksi (mic input kosong)"}
        return {"ok": True, "text": text[:500], "source": "termux-speech-to-text"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"speech-to-text timeout ({timeout_s+15}s)"}
    except FileNotFoundError:
        return {"ok": False, "error": "termux-api tidak terpasang (pkg install termux-api)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:150]}


def tool_image_capture(path: str = "") -> Dict[str, Any]:
    """Foto via kamera HP (termux-api camera) — multimodal input sensor.

    Butuh izin CAMERA di Termux:API. Path default: Personalisasi/Traces/.
    """
    if not path:
        path = os.path.expanduser(
            "~/aeryn-core-agent/Personalisasi/Traces/capture.jpg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        r = subprocess.run(["termux-camera-photo", "-c", "0", path],
                           capture_output=True, timeout=30)
        if r.returncode != 0:
            return {"ok": False,
                    "error": f"camera rc={r.returncode}: {r.stderr.decode()[:120]}"}
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return {"ok": False, "error": "foto kosong (kamera gagal / izin)"}
        return {"ok": True, "path": path, "size": os.path.getsize(path)}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "camera timeout (30s)"}
    except FileNotFoundError:
        return {"ok": False, "error": "termux-api tidak terpasang (pkg install termux-api)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:150]}


def tool_image_describe(path: str, question: str = "") -> Dict[str, Any]:
    """Gambar → deskripsi via LM vision (provider fallback chain).

    Bila provider tidak support vision → error eksplisit (bukan jawaban
    hardcoded). Membaca file nyata + LM nyata.
    """
    if not path or not os.path.exists(path):
        return {"ok": False, "error": f"file tidak ada: {path}"}
    if os.path.getsize(path) > 5_000_000:
        return {"ok": False, "error": "file > 5MB — kompres dulu"}
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
    except Exception as e:
        return {"ok": False, "error": f"read gagal: {str(e)[:120]}"}

    from aeryn_core.utils.llm_client import AerynLLMClient
    llm = AerynLLMClient()
    content = [
        {"type": "text", "text": question or "Deskripsikan gambar ini secara ringkas."},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
    ]
    try:
        resp = llm.chat([{"role": "user", "content": content}],
                        session_id="multimodal:describe", max_tokens=500)
        # chat() async — jalankan via asyncio.run (MainThread tanpa loop)
        import asyncio as _asyncio
        if _asyncio.iscoroutine(resp):
            resp = _asyncio.run(resp)
        out = resp.get("content") or ""
        prov = resp.get("provider", "")
        if prov in ("none", ""):
            return {"ok": False, "error": f"vision gagal: {out[:150]}"}
        return {"ok": True, "path": path, "description": out[:1000],
                "provider": prov}
    except Exception as e:
        return {"ok": False, "error": f"vision error: {str(e)[:150]}"}
