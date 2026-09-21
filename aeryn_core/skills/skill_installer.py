#!/usr/bin/env python3
"""V62.9 — G5: `aeryn skill add` installer — install skill dari repo/nama bawaan.

Sumber skill: (1) katalog bawaan (built-in catalog dict), (2) folder lokal,
(3) marketplace plugin (via PluginMarketplace). Install = tulis SKILL.md ke
aeryn_core/skills/<name>/ + register ke skill_crystallization DB (tampil di
/v1/skills). Idempoten — sudah ada → skip.
Real APIs only — no test doubles.
"""

import os
import sys
import json
import sqlite3
import uuid

REPO = os.environ.get(
    "AERYN_REPO",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."),
)
REPO = os.path.abspath(REPO)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")

SKILLS_DIR = os.path.join(REPO, "aeryn_core", "skills")

# Katalog bawaan — skill siap-install (onboarding ecosystem)
BUILTIN_CATALOG = {
    "web-research": {
        "description": "Riset web: cari + rangkum + kutip sumber.",
        "trigger": "riset/cari di web/research",
    },
    "code-review": {
        "description": "Review kode: security, quality, best practices.",
        "trigger": "review kode/code review",
    },
    "daily-notes": {
        "description": "Catatan harian: jurnal, refleksi, to-do.",
        "trigger": "catatan harian/jurnal/daily notes",
    },
    "reminder-pro": {
        "description": "Reminder lanjutan: jadwal berulang, snooze, prioritas.",
        "trigger": "ingetin/reminder/jadwal",
    },
    "termux-body": {
        "description": "Akses tubuh HP: battery, sensor, notif, location.",
        "trigger": "baterai/sensor/tubuh",
    },
    "memory-graph": {
        "description": "Traverse memory graph (nerve) — RAG lintas-sesi.",
        "trigger": "nerve/graph/entity",
    },
    "pitfall-db": {
        "description": "Search pitfalls DB — known bugs + fixes.",
        "trigger": "pitfall/bug lama/solusi",
    },
    "redis-queue": {
        "description": "Job-queue redis tahan restart (push/pop/schedule).",
        "trigger": "antre job/queue/redis",
    },
    "watchdog-monitor": {
        "description": "Monitor kesehatan service + alert termux-notification.",
        "trigger": "watchdog/kesehatan/monitor",
    },
    "mcp-serve": {
        "description": "Serve kapabilitas Aeryn sebagai MCP tools.",
        "trigger": "mcp/server/kapabilitas",
    },
    "almalinux-build": {
        "description": "Build wheel/toolchain berat via AlmaLinux glibc-worker.",
        "trigger": "build/wheel/toolchain",
    },
    "multi-agent": {
        "description": "Orkestrasi multi-agent paralel (isolated contexts).",
        "trigger": "paralel/multi-agent/orchestrate",
    },
}


def _skill_db_path() -> str:
    from aeryn_core.utils.config import DATABASE_DIR
    return os.path.join(DATABASE_DIR, "skill_crystallization.db")


def _register_to_db(name: str, description: str) -> bool:
    """Register skill ke crystallized DB (tampil di /v1/skills)."""
    try:
        path = _skill_db_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path)
        try:
            exists = conn.execute(
                "SELECT 1 FROM crystallized_skills WHERE name=?", (name,)
            ).fetchone()
            if exists:
                return False
            conn.execute(
                "INSERT INTO crystallized_skills (id,name,description,pattern_id,tool_definition,is_active,created_at) "
                "VALUES (?,?,?,?,?,?,datetime('now'))",
                (uuid.uuid4().hex[:8], name, description, "installed", json.dumps({"name": name}), 1),
            )
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception:
        return False


def skill_add(name: str) -> dict:
    """Install satu skill: katalog bawaan / folder lokal / marketplace."""
    if not name or not name.strip():
        return {"ok": False, "error": "nama skill kosong"}
    name = name.strip().lower().replace(" ", "-")

    # 1) Katalog bawaan
    if name in BUILTIN_CATALOG:
        meta = BUILTIN_CATALOG[name]
        skill_dir = os.path.join(SKILLS_DIR, name)
        os.makedirs(skill_dir, exist_ok=True)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.exists(skill_md):
            with open(skill_md, "w") as f:
                f.write(
                    f"# {name}\n\n## Description\n{meta['description']}\n\n"
                    f"## Trigger Keywords\n- {meta['trigger']}\n\n"
                    f"## Behavior Contract\n- Installed via `aeryn skill add {name}`\n"
                    f"- Sumber: katalog bawaan Aeryn\n"
                )
        registered = _register_to_db(name, meta["description"])
        return {
            "ok": True,
            "skill": name,
            "source": "builtin",
            "registered": registered,
            "path": skill_md,
        }

    # 2) Folder lokal (path ada)
    local = os.path.join(SKILLS_DIR, name)
    if os.path.isdir(local) and os.path.exists(os.path.join(local, "SKILL.md")):
        with open(os.path.join(local, "SKILL.md")) as f:
            head = f.read()[:200]
        registered = _register_to_db(name, head.split("\n")[0])
        return {"ok": True, "skill": name, "source": "local", "registered": registered, "path": local}

    # 3) Marketplace (butuh DB — skip jika env tidak ada, jangan error cryptic)
    if not os.environ.get("AERYN_DB") and not os.environ.get("NEON_DATABASE_URL"):
        return {
            "ok": False,
            "error": f"skill '{name}' tidak ada di katalog bawaan — "
                     f"katalog: {', '.join(sorted(BUILTIN_CATALOG.keys()))}",
        }
    try:
        from aeryn_core.platform.plugin_marketplace import get_plugin_marketplace
        mp = get_plugin_marketplace()
        results = mp.search(name, limit=1) if hasattr(mp, "search") else []
        if results:
            plugin = results[0]
            skill_dir = os.path.join(SKILLS_DIR, name)
            os.makedirs(skill_dir, exist_ok=True)
            with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
                f.write(f"# {name}\n\n## Description\n{plugin.get('description', '')}\n")
            registered = _register_to_db(name, plugin.get("description", name))
            return {"ok": True, "skill": name, "source": "marketplace", "registered": registered}
    except Exception as e:
        return {"ok": False, "error": f"marketplace: {str(e)[:150]}"}

    return {
        "ok": False,
        "error": f"skill '{name}' tidak ada — katalog: {', '.join(sorted(BUILTIN_CATALOG)[:8])}...",
    }


def skill_list() -> dict:
    """List skill ter-install + katalog yang tersedia."""
    installed = []
    if os.path.isdir(SKILLS_DIR):
        for d in sorted(os.listdir(SKILLS_DIR)):
            if os.path.exists(os.path.join(SKILLS_DIR, d, "SKILL.md")):
                installed.append(d)
    return {"installed": installed, "catalog": sorted(BUILTIN_CATALOG.keys())}


def register(registry) -> None:
    """Register skill tools ke PluginRegistry."""
    registry.register(
        "skill_add",
        "Install skill (katalog bawaan / lokal / marketplace)",
        handler=lambda name, **kw: skill_add(name),
        parameters={
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
        tags=["skill", "install", "ecosystem"],
        category="admin",
    )
    registry.register(
        "skill_list",
        "List skill ter-install + katalog tersedia",
        handler=lambda **kw: skill_list(),
        parameters={"type": "object", "properties": {}},
        tags=["skill", "list", "ecosystem"],
        category="admin",
    )
