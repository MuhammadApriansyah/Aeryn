"""Browser/Computer Interaction (RM10) — drive browser dengan permission.

Sesuai Aeryn_Identity.md §15 (Browser/Computer Interaction) + §13 (autonomy
user-governed — HITL):
- tool_browser_open: buka URL di browser HP (termux-open-url — user melihat
  sendiri; HITL-friendly: aksi terlihat, user bisa tutup)
- tool_browser_read: baca halaman web via requests + ekstraksi teks ringkas
  (headless-friendly, tanpa pkg tambahan — untuk agent baca konteks)
- tool_computer_status: status environment HP (battery + lokasi izin + service)

Selenium/playwright pkg tidak terpasang di Termux — BrowserSession module
yang ada butuh Seledroid APP; interaksi browser di HP dilakukan via
termux-open (user-visible) + read via requests (headless). Error eksplisit
bila backend tidak tersedia (bukan jawaban hardcoded).

Real API only — no test doubles.
"""

import json
import re
import urllib.request
import urllib.robotparser
from typing import Dict, Any
from urllib.parse import urlparse


def tool_browser_open(url: str) -> Dict[str, Any]:
    """Buka URL di browser HP (termux-open-url) — user-visible (HITL)."""
    if not url or not url.startswith(("http://", "https://")):
        return {"ok": False, "error": "url harus http(s):// — bukan scheme lain"}
    import subprocess
    try:
        r = subprocess.run(["termux-open-url", url], capture_output=True, timeout=15)
        if r.returncode != 0:
            return {"ok": False,
                    "error": f"termux-open-url rc={r.returncode}: {r.stderr.decode()[:120]}"}
        return {"ok": True, "url": url, "note": "dibuka di browser HP (user-visible)"}
    except FileNotFoundError:
        return {"ok": False, "error": "termux-api tidak terpasang (pkg install termux-api)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:150]}


def tool_browser_read(url: str, max_chars: int = 3000) -> Dict[str, Any]:
    """Baca halaman web → teks ringkas (requests + regex strip HTML).

    Robot.txt dihormati (politeness — local-first friendly). Error eksplisit.
    """
    if not url or not url.startswith(("http://", "https://")):
        return {"ok": False, "error": "url harus http(s)://"}
    # robots.txt politeness
    try:
        parsed = urlparse(url)
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
        rp.read()
        if not rp.can_fetch("aeryn/62.24", url):
            return {"ok": False, "error": "robots.txt melarang fetch URL ini (politeness)"}
    except Exception:
        pass  # robots.txt tidak bisa dibaca — lanjut (best-effort politeness)
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "aeryn/62.24 (personal assistant; +https://github.com/MuhammadApriansyah/Aeryn.git)"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        # strip HTML → teks
        html = re.sub(r"<script.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = title_m.group(1).strip()[:120] if title_m else ""
        if not text:
            return {"ok": False, "error": "halaman kosong (JS-rendered? butuh backend headless)"}
        return {"ok": True, "url": url, "title": title,
                "text": text[:max_chars], "length": len(text)}
    except Exception as e:
        return {"ok": False, "error": f"read gagal: {str(e)[:150]}"}


def tool_computer_status() -> Dict[str, Any]:
    """Status environment HP: battery + service count + RAM (self-monitoring)."""
    import subprocess
    out: Dict[str, Any] = {"ok": True}
    # battery (termux-api)
    try:
        r = subprocess.run(["termux-battery-status"], capture_output=True, timeout=10)
        if r.returncode == 0:
            b = json.loads(r.stdout.decode() or "{}")
            out["battery"] = {"pct": b.get("percentage"),
                              "status": b.get("status"),
                              "plugged": b.get("plugged")}
    except Exception as e:
        out["battery"] = {"error": str(e)[:100]}
    # service count (runit)
    try:
        r = subprocess.run(
            ["sh", "-c", "ls $PREFIX/var/service | wc -l"], capture_output=True, timeout=5)
        out["services"] = int(r.stdout.decode().strip() or 0)
    except Exception:
        out["services"] = None
    # RAM (free)
    try:
        r = subprocess.run(["sh", "-c", "free -m | awk 'NR==2{print $7}'"],
                           capture_output=True, timeout=5)
        out["ram_free_mb"] = int(r.stdout.decode().strip() or 0)
    except Exception:
        out["ram_free_mb"] = None
    return out
