"""V61.2 — Observability dashboard: agregasi satu panggilan (#7).

Konsolidasi health (app + 5 subsistem), PG status, metrik request,
error terbaru, cron, dan facts bitemporal — untuk satu layar dashboard.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/obs/summary")
def obs_summary(window_hours: int = 24):
    """Dashboard observability — semua sinyal penting dalam satu respons."""
    import json

    out = {"app": {}, "subsystems": {}, "pg": {}, "requests": {},
           "errors": [], "cron": {"total": 0, "active": 0},
           "facts": 0, "generated_at": None}
    from datetime import datetime
    out["generated_at"] = datetime.utcnow().isoformat()

    # App health
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:3010/health", timeout=3) as r:
            out["app"] = json.loads(r.read())
    except Exception as e:  # noqa: BLE001
        out["app"] = {"status": "down", "error": str(e)[:80]}

    # Subsystem health (probe nyata)
    for name, ep in (("memory", "/v1/memory/health"), ("engine", "/v1/engine/health"),
                     ("safety", "/v1/safety/health"), ("agents", "/v1/agents/health"),
                     ("platform", "/v1/platform/health")):
        try:
            import urllib.request
            with urllib.request.urlopen("http://127.0.0.1:3010" + ep, timeout=3) as r:
                out["subsystems"][name] = json.loads(r.read())
        except Exception as e:  # noqa: BLE001
            out["subsystems"][name] = {"status": "down", "error": str(e)[:60]}

    # PG status (via pg_isready — real, tanpa dependency driver)
    try:
        import subprocess
        r = subprocess.run(["/usr/lib/postgresql/17/bin/pg_isready",
                            "-h", "127.0.0.1", "-p", "5432"],
                           capture_output=True, text=True, timeout=5)
        out["pg"] = {"status": "up" if r.returncode == 0
                     else "down", "detail": (r.stdout or r.stderr).strip()[:60]}
    except Exception as e:  # noqa: BLE001
        out["pg"] = {"status": "unknown", "error": str(e)[:60]}

    # Metric request (dari request_logs / logging/stats)
    try:
        import urllib.request
        with urllib.request.urlopen(
                f"http://127.0.0.1:3010/v1/logging/stats?window_hours={window_hours}",
                timeout=4) as r:
            out["requests"] = json.loads(r.read())
    except Exception as e:  # noqa: BLE001
        out["requests"] = {"error": str(e)[:60]}

    # Error terbaru
    try:
        import urllib.request
        with urllib.request.urlopen(
                f"http://127.0.0.1:3010/v1/logging/recent?limit=8&min_status=400",
                timeout=4) as r:
            out["errors"] = json.loads(r.read()).get("recent", [])
    except Exception as e:  # noqa: BLE001
        out["errors"] = []

    # Facts + cron count
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:3010/v1/facts/entities", timeout=3) as r:
            ents = json.loads(r.read()).get("entities", [])
            out["facts"] = sum(e.get("facts", 0) for e in ents)
    except Exception:  # noqa: BLE001
        out["facts"] = -1
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:3010/v1/cron/jobs", timeout=3) as r:
            jobs = json.loads(r.read()).get("jobs", [])
            out["cron"]["total"] = len(jobs)
            out["cron"]["active"] = sum(1 for j in jobs if j.get("enabled", True))
    except Exception:  # noqa: BLE001
        pass
    return out