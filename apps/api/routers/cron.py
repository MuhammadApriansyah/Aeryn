"""V61.1 — Cron scheduler HTTP API (fitur Hermes: jadwal berulang)."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class CronJobIn(BaseModel):
    name: str
    schedule: str            # cron 5-field, mis. "0 9 * * *"
    url: str                 # action: HTTP webhook tujuan
    method: str = "POST"
    payload: dict = {}


@router.post("/cron/jobs")
async def cron_create(body: CronJobIn):
    from aeryn_core.job_queue.scheduler import get_scheduler
    s = get_scheduler()
    jid = s.add_job(body.name, body.schedule, body.url,
                    method=body.method, payload=body.payload)
    s.start()
    return {"status": "created", "id": jid}


@router.get("/cron/jobs")
async def cron_list():
    from aeryn_core.job_queue.scheduler import get_scheduler
    return {"jobs": get_scheduler().list_jobs()}


@router.patch("/cron/jobs/{jid}")
async def cron_toggle(jid: str, enabled: bool):
    from aeryn_core.job_queue.scheduler import get_scheduler
    get_scheduler().toggle(jid, enabled)
    return {"status": "ok", "id": jid, "enabled": enabled}


@router.delete("/cron/jobs/{jid}")
async def cron_delete(jid: str):
    from aeryn_core.job_queue.scheduler import get_scheduler
    get_scheduler().delete_job(jid)
    return {"status": "deleted", "id": jid}


@router.get("/cron/jobs/{jid}/runs")
async def cron_runs(jid: str, limit: int = 20):
    from aeryn_core.job_queue.scheduler import get_scheduler
    return {"runs": get_scheduler().get_runs(jid, limit)}