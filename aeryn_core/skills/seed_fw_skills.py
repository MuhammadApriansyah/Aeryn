"""V61.4 — FW4: Ecosystem seed tambahan (8 skills baru, idempoten).

Menambah skills FW-era ke crystallized_skills: redis-queue, watchdog,
mcp-server, almalinux-worker, memory-graph, pitfall-db, self-modify,
termux-body. Semua kapabilitas NYATA & terverifikasi (no test doubles).
Idempoten: tidak dobel bila nama sudah ada.
"""
import os
import sys
import json
import sqlite3
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _skill_db_path():
    from aeryn_core.utils.config import DATABASE_DIR
    return os.path.join(DATABASE_DIR, "skill_crystallization.db")


SKILLS = [
    {
        "name": "Redis Job Queue",
        "description": "Job-queue redis tahan restart (push/pop/worker daemon runit).",
        "tool_def": {"name": "redis_queue", "trigger": "antre job/queue/redis", "endpoint": "redis://127.0.0.1:6379/aeryn:jobs"},
    },
    {
        "name": "Watchdog Monitoring",
        "description": "Monitor api/pg/redis + alert termux-notification + catat bitemporal facts.",
        "tool_def": {"name": "watchdog", "trigger": "watchdog/kesehatan/monitor", "endpoint": "file://~/tmp/aeryn-watchdog.log"},
    },
    {
        "name": "MCP Server",
        "description": "Serve kapabilitas Aeryn sebagai MCP tools (streamable-http, official SDK).",
        "tool_def": {"name": "mcp_server", "trigger": "mcp/server/kapabilitas", "endpoint": "http://127.0.0.1:8090/mcp"},
    },
    {
        "name": "AlmaLinux Worker",
        "description": "glibc-worker via proot: wheel manylinux aarch64 prebuilt + toolchain berat.",
        "tool_def": {"name": "almalinux_worker", "trigger": "build/wheel/toolchain berat", "endpoint": "proot://~/almalinux"},
    },
    {
        "name": "Memory Graph Traverse",
        "description": "Traverse memory graph (nerve) sekitar entity — RAG lintas-sesi.",
        "tool_def": {"name": "graph_traverse", "trigger": "nerve/graph/entity", "endpoint": "tool://graph_traverse"},
    },
    {
        "name": "Pitfall Database",
        "description": "Search pitfalls DB — known bug patterns + fixes (jangan re-diagnose).",
        "tool_def": {"name": "pitfall_search", "trigger": "pitfall/bug lama/solusi", "endpoint": "tool://pitfall_search"},
    },
    {
        "name": "Self Modify",
        "description": "Aeryn memodifikasi dirinya sendiri (goal-pursuit + self-verify + drift guard).",
        "tool_def": {"name": "self_modify", "trigger": "self-modify/ubah diri", "endpoint": "/v1/goals"},
    },
    {
        "name": "Termux Body",
        "description": "Akses tubuh HP (battery/sensor/notif/location) via termux-api.",
        "tool_def": {"name": "battery", "trigger": "baterai/sensor/tubuh", "endpoint": "tool://battery"},
    },
]


def seed():
    path = _skill_db_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    added = 0
    try:
        for s in SKILLS:
            exists = conn.execute(
                "SELECT 1 FROM crystallized_skills WHERE name=?",
                (s["name"],)).fetchone()
            if exists:
                continue
            conn.execute(
                "INSERT INTO crystallized_skills (id,name,description,pattern_id,tool_definition,is_active,created_at) "
                "VALUES (?,?,?,?,?,?,datetime('now'))",
                (uuid.uuid4().hex[:8], s["name"], s["description"], "seeded",
                 json.dumps(s["tool_def"]), 1))
            added += 1
        conn.commit()
    finally:
        conn.close()
    return {"added": added, "total_known": len(SKILLS), "path": path}


if __name__ == "__main__":  # pragma: no cover
    res = seed()
    print(f"Seeded {res['added']} skills (of {res['total_known']}) into {res['path']}")
