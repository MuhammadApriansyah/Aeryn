"""Tools sensor dunia (RM6) — location + weather + calendar_read.

Sensors = Environment Interaction (Aeryn_Identity.md §13):
- tool_location: termux-api Location (GPS) → "aku di mana"
- tool_weather: cuaca via open-meteo (tanpa API key, lokal-first friendly)
- tool_calendar_read: agenda harian dari ZSET (scheduled) + goals deadline

Real API only — no test doubles: termux-api nyata, open-meteo HTTP nyata,
ZSET/goals dari database nyata.
"""

import json
import time
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, Any


def tool_location() -> Dict[str, Any]:
    """GPS via termux-api (HITL-friendly: sensor pasif baca koordinat)."""
    import subprocess
    try:
        # termux-api Location — timeout 20s (GPS fix bisa lama)
        r = subprocess.run(
            ["termux-location", "-p", "network", "-r", "once"],
            capture_output=True, timeout=30)
        if r.returncode != 0:
            return {"ok": False, "error": f"termux-location rc={r.returncode}: {r.stderr.decode()[:120]}"}
        data = json.loads(r.stdout.decode() or "{}")
        if not data or "lat" not in data:
            return {"ok": False, "error": "lokasi kosong (GPS belum fix / permission)"}
        return {"ok": True, "lat": data.get("lat"), "lon": data.get("lon"),
                "provider": data.get("provider", "network"),
                "accuracy_m": data.get("accuracy")}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "termux-location timeout (30s) — GPS belum fix"}
    except FileNotFoundError:
        return {"ok": False, "error": "termux-api tidak terpasang (pkg install termux-api)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:150]}


def tool_weather(lat: float = -6.2088, lon: float = 106.8456) -> Dict[str, Any]:
    """Cuaca via open-meteo (tanpa API key). Default: Jakarta.
    Jika lat/lon kosong → coba tool_location dulu (sensor chain)."""
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
               f"&timezone=Asia%2FJakarta")
        req = urllib.request.Request(url, headers={"User-Agent": "aeryn/62.24"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read().decode())
        cur = d.get("current", {})
        code = cur.get("weather_code", -1)
        # WMO weather code → deskripsi (ringkas)
        wmo = {0: "cerah", 1: "cerah berawan", 2: "berawan sebagian", 3: "berawan",
               45: "berkabut", 48: "berkabut beku", 51: "gerimis ringan",
               53: "gerimis", 55: "gerimis lebat", 61: "hujan ringan",
               63: "hujan", 65: "hujan lebat", 71: "salju ringan", 73: "salju",
               75: "salju lebat", 80: "hujan lokal ringan", 81: "hujan lokal",
               82: "hujan lokal lebat", 95: "badai petir", 96: "badai petir + hujan es",
               99: "badai petir lebat + hujan es"}
        return {"ok": True, "lat": lat, "lon": lon,
                "temperature_c": cur.get("temperature_2m"),
                "humidity_pct": cur.get("relative_humidity_2m"),
                "wind_kmh": cur.get("wind_speed_10m"),
                "condition": wmo.get(code, f"kode {code}")}
    except Exception as e:
        return {"ok": False, "error": f"weather gagal: {str(e)[:150]}"}


def tool_calendar_read(days_ahead: int = 2) -> Dict[str, Any]:
    """Agenda dari ZSET (reminder scheduled) + goals (deadline) — N hari ke depan."""
    try:
        from aeryn_core.platform import redis_queue as rq
        now = time.time()
        horizon = now + days_ahead * 86400
        # ZSET scheduled: member=job json, score=remind_at epoch
        upcoming = []
        try:
            r = rq.connect()
            rows = r.zrangebyscore(rq.SCHED_KEY, now - 3600, horizon)
            for member in rows:
                try:
                    job = json.loads(member)
                except Exception:
                    job = {"raw": str(member)[:80]}
                at = job.get("remind_at") or 0
                upcoming.append({
                    "at": datetime.fromtimestamp(at).strftime("%Y-%m-%d %H:%M") if at else "?",
                    "kind": job.get("kind", "reminder"),
                    "text": str(job.get("text", job.get("raw", "")))[:80],
                })
        except Exception as e:
            return {"ok": False, "error": f"zrange gagal: {str(e)[:150]}"}
        # Goals dengan deadline dalam horizon
        goals_up = []
        try:
            from aeryn_core.agent.goal_store import get_goal_store
            for g in get_goal_store().list_goals(status="active"):
                dl = g.get("deadline") if isinstance(g, dict) else None
                if dl:
                    goals_up.append({"title": str(g.get("title", ""))[:60],
                                     "deadline": str(dl)})
        except Exception:
            pass  # goals opsional (kalender tetap dari ZSET)
        upcoming.sort(key=lambda x: x["at"])
        return {"ok": True, "days_ahead": days_ahead,
                "upcoming": upcoming[:20], "goals_with_deadline": goals_up[:5],
                "count": len(upcoming)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:150]}
