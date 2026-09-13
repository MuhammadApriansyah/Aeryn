"""Seed crystallized_skills dengan kapabilitas NYATA Aeryn (idempoten).

Supaya /v1/skills (modul Skills di work console) menampilkan entri sejati —
bukan kosong — kita daftarkan kapabilitas Aeryn yang benar-benar ada &
terverifikasi (memori, tool, bitemporal, evolution, harness, cron, embedding,
auth, session). Setiap entri punya tool_definition JSON konsisten dgn skill.
Idempoten: tidak dobel bila nama sudah ada.
"""
import os
import sys
import json
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _skill_db_path():
    # Hindari import 'aeryn_core.platform' (menimpa stdlib 'platform' saat
    # dijalankan standalone). Ambil DATABASE_DIR langsung dari utils.config.
    from aeryn_core.utils.config import DATABASE_DIR
    return os.path.join(DATABASE_DIR, "skill_crystallization.db")


SKILLS = [
    {
        "name": "Memory Recall",
        "description": "Recall & entity memory Aeryn (vault, entities, semantic).",
        "tool_def": {"name": "memory_recall", "trigger": "ingat/lupa/rekal memori", "endpoint": "/v1/memory/entities"},
    },
    {
        "name": "Tool Execution",
        "description": "Jalankan tool native (fs, terminal, web_search, web_fetch, python).",
        "tool_def": {"name": "tool_execute", "trigger": "jalankan tool", "endpoint": "/v1/tools/execute"},
    },
    {
        "name": "Knowledge Graph",
        "description": "Bitemporal knowledge graph (fakt + audit trail).",
        "tool_def": {"name": "knowledge_graph", "trigger": "knowledge graph/fakta", "endpoint": "/v1/facts"},
    },
    {
        "name": "Skill Evolution",
        "description": "Evaluasi kandidat skill -> ACCEPT/REFINE/REJECT (self-improvement).",
        "tool_def": {"name": "skill_evolution", "trigger": "evaluasi skill", "endpoint": "/v1/evolution/evaluate"},
    },
    {
        "name": "Harness Evaluation",
        "description": "Auto harness loop: skor batch tugas + tuning feedback.",
        "tool_def": {"name": "harness_eval", "trigger": "evaluasi harness", "endpoint": "/v1/harness/eval"},
    },
    {
        "name": "Cron Scheduler",
        "description": "Jadwal berulang (cron) dengan persistensi PG + webhook action.",
        "tool_def": {"name": "cron_jobs", "trigger": "cron/jadwal berulang", "endpoint": "/v1/cron/jobs"},
    },
    {
        "name": "Neural Embedding",
        "description": "Embedding neural 384-dim via Termux (all-MiniLM-L6-v2).",
        "tool_def": {"name": "neural_embedding", "trigger": "embedding/vector", "endpoint": ":8081/embed"},
    },
    {
        "name": "Auth & Identity",
        "description": "Autentikasi pengguna (register/login) via PostgreSQL/RBAC.",
        "tool_def": {"name": "auth_identity", "trigger": "login/auth", "endpoint": "/v1/auth/login"},
    },
    {
        "name": "Session Management",
        "description": "Kelola sesi percakapan (list/resume/hapus).",
        "tool_def": {"name": "session_mgmt", "trigger": "sesi percakapan", "endpoint": "/v1/sessions"},
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
            import uuid
            conn.execute(
                "INSERT INTO crystallized_skills (id,name,description,pattern_id,tool_definition,is_active,created_at) "
                "VALUES (?,?,?,?,?,?,datetime('now'))",
                (uuid.uuid4().hex[:8], s["name"], s["description"], "seeded",
                 json.dumps(s["tool_def"]), 1))
            added += 1
        conn.commit()
    finally:
        conn.close()
    return {"added": added, "path": path}


if __name__ == "__main__":  # pragma: no cover
    res = seed()
    print(f"Seeded {res['added']} skills into {res['path']}")