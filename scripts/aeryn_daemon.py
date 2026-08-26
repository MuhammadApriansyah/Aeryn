"""Aeryn-Core Daemon — server persist hybrid (FastAPI + uvicorn).

Satu orchestrator hidup sepanjang umur proses → memori vektor, tensor emosi,
dan checkpoint sesi PERSIST antar request (tidak di-instantiate ulang).

Endpoint:
  GET  /health                  → status daemon
  POST /compile                 → { session_id, base_prompt, user_prompt, history?, tasks?, preference_vector? }
                                  → { compiled_prompt, blackboard, gate_mode, memories }
  POST /digest                  → { session_id, user_prompt, response }
                                  → governance result + telemetry
  GET  /memory/{session_id}     → ringkasan state sesi (tensor terakhir)
  POST /session/{sid}/reset     → hapus checkpoint afektif sesi (fresh start opsional)

Port default 3010. Jalankan: ./venv-proot/bin/python scripts/aeryn_daemon.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "/home/sen/aeryn-core-agent")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from aeryn_core.orchestrator import UnifiedCognitiveOrchestrator

app = FastAPI(title="Aeryn-Core Daemon", version="0.24.0")

# Satu otak untuk seluruh umur proses — inilah inti persist.
print("[aeryn-daemon] booting cognitive core...", flush=True)
BRAIN = UnifiedCognitiveOrchestrator(dimension=384)
LAST_TENSOR: dict[str, dict] = {}
STARTED = time.time()
print("[aeryn-daemon] core ready.", flush=True)


class CompileReq(BaseModel):
    session_id: str = Field(min_length=1)
    base_prompt: str
    user_prompt: str
    history: list[str] = []
    tasks: list[str] = []
    preference_vector: dict | None = None


class DigestReq(BaseModel):
    session_id: str = Field(min_length=1)
    user_prompt: str
    response: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "core": "aeryn-v28",
        "uptime_s": int(time.time() - STARTED),
        "sessions_touched": len(LAST_TENSOR),
        "gate_mode": BRAIN.cached_active_gate_mode,
    }


@app.post("/compile")
def compile_prompt(req: CompileReq):
    try:
        compiled = BRAIN.compile_stateful_system_prompt(
            session_id=req.session_id,
            base_character_prompt=req.base_prompt,
            user_prompt=req.user_prompt,
            mock_history_logs=req.history,
            open_tasks=req.tasks,
            external_preference_vector=req.preference_vector,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"compile failed: {e}")

    try:
        bb = json.loads(BRAIN.cached_shared_blackboard)
    except Exception:
        bb = {}
    LAST_TENSOR[req.session_id] = bb.get("emotional_tensor_snapshot", {})

    # Ekstrak blok memori dari prompt agar client tahu konteks apa yang disuntik
    memories = []
    if "[RELEVANT_MEMORY_CONTEXT]" in compiled:
        block = compiled.split("[RELEVANT_MEMORY_CONTEXT]", 1)[1]
        for line in block.splitlines()[1:]:
            line = line.strip().lstrip("- ").strip()
            if line and not line.startswith("["):
                memories.append(line)

    return {
        "compiled_prompt": compiled,
        "blackboard": bb,
        "gate_mode": BRAIN.cached_active_gate_mode,
        "memories": memories[:4],
    }


@app.post("/digest")
def digest(req: DigestReq):
    try:
        result = BRAIN.digest_external_llm_response(
            session_id=req.session_id,
            user_prompt=req.user_prompt,
            raw_llm_output_text=req.response,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"digest failed: {e}")
    return result


@app.get("/memory/{session_id}")
def memory(session_id: str):
    cp = None
    try:
        cp = BRAIN.rust_brain.load_affective_checkpoint(session_id)
    except Exception:
        pass
    return {
        "session_id": session_id,
        "last_tensor": LAST_TENSOR.get(session_id),
        "persisted_checkpoint": list(cp) if cp else None,
    }


@app.post("/session/{session_id}/reset")
def reset_session(session_id: str):
    """V38.7 — operasi destruktif: hanya sesi majikan/DC yang boleh reset.
    Dulu SIAPA PUN dengan akses localhost bisa menghapus state afektif
    sesi orang lain."""
    if not _master_allowed(session_id):
        raise HTTPException(status_code=403,
                            detail="reset hanya untuk sesi majikan")
    LAST_TENSOR.pop(session_id, None)
    return {"reset": True, "session_id": session_id}


# ── V25: Agentic loop (hybrid-native scaffolding) ───────────────────────
import sys
sys.path.insert(0, "/home/sen/aeryn-core-agent")
from aeryn_core.model_client import ModelClient
from aeryn_core.tool_bridge import build_default_registry
from aeryn_core.tool_governance import ToolGovernanceGate
from aeryn_core.shadow_mode import ParityLedger, ShadowRunner
from aeryn_core.planner import make_plan, load_plan
from aeryn_core.terminal_tool import make_terminal, TERMINAL_SCHEMA
from aeryn_core.episodic_memory import EpisodicMemory
from aeryn_core.reflection import PostRunReflection
from aeryn_core.agents.division_4_gov.sub_agents_real import SubAgentContextDriftShield

TOOLS = build_default_registry(sandbox_roots=["~/aeryn-core-agent", "~/webnovel-platform"])
# V27.2 — tool tier power: terminal sandboxed (whitelist + no-shell + cwd lock).
# V37.5-SEC — dibungkus SecurityKernel: path di argumen + flag dgn nilai
# path divalidasi (menutup bypass --output=/x, -fprint/etc/x, cat .env).
from aeryn_core.security_kernel import make_secure_terminal
TOOLS.register("terminal", make_secure_terminal(["~/aeryn-core-agent", "~/webnovel-platform"]),
               TERMINAL_SCHEMA, tier="power")
# V33 "Shared Brain" — Aeryn membaca memori kolektif Hermes (tier safe,
# read-only): library RAG + knowledge graph + pitfalls. Satu otak, dua agen.
from aeryn_core.hermes_brain import register as register_hermes_brain
register_hermes_brain(TOOLS)
# V34 — CoreMemory ala Letta: blok human/context selalu di prompt,
# agent edit sendiri via tool core_memory_edit.
from aeryn_core.core_memory import CoreMemory
from aeryn_core.hermes_brain import CORE_MEMORY_SCHEMA
CORE_MEM = CoreMemory()


def _core_memory_edit(block: str, mode: str = "append", content: str = ""):
    return CORE_MEM.edit(block, mode, content)


TOOLS.register("core_memory_edit", _core_memory_edit, CORE_MEMORY_SCHEMA,
               tier="safe")
# V38.1 — spawn_subagents: Aeryn punya sub-agen sendiri (pola delegate_task
# Hermes, skala kecil). Runner diinjeksi dari daemon (pipeline lengkap).
from aeryn_core.sub_agent_runner import (SPAWN_SCHEMA, MAX_SUBAGENTS_PER_RUN,
                                         SUB_MAX_ITERATIONS, SUB_WALL_SECONDS,
                                         in_subagent, spawn_subagents)


def _spawn_subagents(goals: list):
    def _real_runner(sop, goal, session_id, max_iterations, max_wall_seconds):
        """Runner SOP-aware: goal dikirim = SOP lengkap + tugas.

        Sub-agen menerima SOP sebagai bagian dari goal (system prompt
        internal sudah berisi persona & aturan dasar; SOP mempersempit).
        """
        req = AgentRunReq(goal=sop, session_id=session_id,
                          max_iterations=max_iterations,
                          max_wall_seconds=max_wall_seconds)
        events = list(_run_steps(req))
        final = events[-1] if events else {}
        data = final.get("data", {})
        if isinstance(data, dict):
            data["ok"] = (final.get("event") == "final") and bool(
                data.get("answer"))
        return data

    return spawn_subagents(goals, runner=_real_runner)


def _checker_spawn(args, result):
    return isinstance(result, dict) and "results" in result


TOOLS.register("spawn_subagents", _spawn_subagents, SPAWN_SCHEMA,
               tier="safe")
# V39.2 — dua tool dasar dari analisa episode: datetime (anti halusinasi
# tanggal) + math_calc (kalkulasi aman via AST whitelist, tanpa eval).
from aeryn_core.basic_tools import (datetime_now, math_calc,
                                    DATETIME_SCHEMA, MATH_SCHEMA)
TOOLS.register("datetime_now", datetime_now, DATETIME_SCHEMA, tier="safe")
TOOLS.register("math_calc", math_calc, MATH_SCHEMA, tier="safe")
# V39.3 — reminder internal + image understanding
from aeryn_core.reminder import set_reminder, REMINDER_SCHEMA
from aeryn_core.image_tools import image_understand, IMAGE_SCHEMA


def _set_reminder(note: str, delay_minutes: float = 30):
    # session_id induk dicatat agar pengingat tahu harus dilapor ke mana
    return set_reminder(note, delay_minutes)


def _checker_reminder(args, result):
    return isinstance(result, dict) and result.get("ok") is True


def _checker_image(args, result):
    return isinstance(result, dict) and result.get("ok") is True and \
        result.get("answer")


TOOLS.register("set_reminder", _set_reminder, REMINDER_SCHEMA, tier="safe")
TOOLS.register("image_understand", image_understand, IMAGE_SCHEMA,
               tier="safe")


def _checker_datetime(args, result):
    return isinstance(result, dict) and result.get("ok") is True


def _checker_math(args, result):
    return isinstance(result, dict) and "result" in result

# V37 P2 — ask_hermes: tangan lintas-hemisfer. Aeryn bisa minta Hermes
# (otak kiri) mengerjakan tugas berat via CLI one-shot. Cap harian di
# modul; tier "safe" karena efeknya di luar sandbox tapi terbatas & dicatat.
from aeryn_core.hermes_hands import ask_hermes, ASK_HERMES_SCHEMA
TOOLS.register("ask_hermes", ask_hermes, ASK_HERMES_SCHEMA, tier="safe")


def _checker_ask_hermes(args, result):
    return isinstance(result, dict) and result.get("ok") is True

GATE = ToolGovernanceGate(drift_shield=SubAgentContextDriftShield())
# V37.2 — ledger persist: streak graduasi selamat dari restart PM2.
# V37.3 FIX — file HARUS berbeda dari registry state (dulu sama-sama
# tool_graduation.json dgn format beda → saling menimpa, status tool
# bisa korup saat restart berikutnya).
LEDGER = ParityLedger(
    TOOLS, path=os.path.expanduser(
        "~/aeryn-core-agent/Personalisasi/Database/parity_ledger.json"))
SHADOW = ShadowRunner(TOOLS, LEDGER)
MEMORY = EpisodicMemory()  # V27.4 — memori episodik lintas-sesi
REFLECT = PostRunReflection(registry=TOOLS, ledger=LEDGER)  # V27.5 — refleksi pasca-run
# V27.0: tool safe-tier yang lulus shadow 5x beruntun otomatis naik native.
SHADOW.auto_promote = {"web_search", "http_get", "web_read",
                       "memory_search", "graph_traverse", "pitfall_search"}


def _maybe_auto_promote(name):
    """V27.3 meta-loop ringan: graduation_ready dari ledger → promosi native."""
    if name not in getattr(SHADOW, "auto_promote", set()):
        return False
    s = LEDGER.summary().get(name) or {}
    if s.get("graduation_ready") and TOOLS.tools[name]["status"] == "shadowing":
        TOOLS.promote(name, "native")
        return True
    return False


def _checker_fs_read(args, result):
    """Paritas fs_read: hasil harus berupa dict dgn path & content non-error."""
    return isinstance(result, dict) and "content" in result and "error" not in result


def _checker_web_search(args, result):
    return isinstance(result, dict) and "results" in result


def _checker_web_read(args, result):
    """Paritas web_read: dict dengan text non-kosong, ATAU error terkontrol."""
    if not isinstance(result, dict):
        return False
    return ("text" in result and bool(result.get("text"))) or "error" in result


def _checker_memory_search(args, result):
    """Paritas memory_search: dict dengan list results (boleh kosong)."""
    return isinstance(result, dict) and isinstance(result.get("results"), list)


def _checker_graph_traverse(args, result):
    """Paritas graph_traverse: node string + edges list."""
    return (isinstance(result, dict) and "node" in result
            and isinstance(result.get("edges"), list))


def _checker_pitfall_search(args, result):
    """Paritas pitfall_search: dict dengan list pitfalls (boleh kosong)."""
    return isinstance(result, dict) and isinstance(result.get("pitfalls"), list)


SHADOW.register_checker("fs_read", _checker_fs_read)
SHADOW.register_checker("web_search", _checker_web_search)
SHADOW.register_checker("web_read", _checker_web_read)
# V34 — core_memory_edit: sukses = dict ok:True dari CoreMemory.edit
def _checker_core_memory_edit(args, result):
    return isinstance(result, dict) and result.get("ok") is True


# V35 INFRA-3 — fs_write: sukses = dict ok:True + bytes_written > 0
def _checker_fs_write(args, result):
    return (isinstance(result, dict) and result.get("ok") is True
            and result.get("bytes_written", 0) > 0)


SHADOW.register_checker("fs_write", _checker_fs_write)
SHADOW.register_checker("spawn_subagents", _checker_spawn)
SHADOW.register_checker("datetime_now", _checker_datetime)
SHADOW.register_checker("math_calc", _checker_math)
SHADOW.register_checker("ask_hermes", _checker_ask_hermes)


SHADOW.register_checker("core_memory_edit", _checker_core_memory_edit)
# V33 Shared Brain — parity checkers + auto-promote setelah 5x konsisten
SHADOW.register_checker("memory_search", _checker_memory_search)
SHADOW.register_checker("graph_traverse", _checker_graph_traverse)
SHADOW.register_checker("pitfall_search", _checker_pitfall_search)

# V32 imports
from aeryn_core.persona_engine import PersonaEngine
from aeryn_core.social_memory import SocialMemory
PERSONA = PersonaEngine()
SOCIAL = SocialMemory()


def _is_social_query(goal: str) -> bool:
    """V33-F1 — Deteksi social query vs knowledge/task.

    Urutan keputusan:
      1. Sinyal TEKNIS positif (noun/verb teknis, ekstensi file, pola
         pertanyaan knowledge) → BUKAN sosial, langsung False.
      2. Social butuh sinyal relasional: greeting, kata ganti orang
         (kamu/aku), atau frasa ingat/panggil. Tanpa itu → bukan sosial.
    Pertanyaan "apa itu X" / "gimana cara Y" adalah KNOWLEDGE, bukan sosial.
    """
    msg = goal.lower().strip()
    if not msg:
        return False

    # ── 0. Perintah eksplisit menulis memori → BUKAN sosial ──
    # "ingat ini: X", "catat: Y" adalah instruksi simpan fakta.
    if msg.startswith(("ingat ini", "ingat:", "catat ini", "catat:",
                       "remember this", "tolong ingat")):
        return False

    # ── 0b. Self-inquiry → BUKAN sosial (V35) ──
    # Pertanyaan tentang kondisi/kerja internal agent butuh jalur knowledge
    # ("kondisi performamu?", "cek ingatanmu") — ketemu smoke digest V35.
    self_inquiry = (
        "performa", "performamu", "kondisimu", "memorimu", "ingatanmu",
        "toolsmu", "tool kamu", "statistik", "metrik", "metrics",
        "kamu pakai model", "versi berapa")
    for s in self_inquiry:
        if s in msg:
            return False

    # ── 0c. Reminder request → BUKAN sosial (V39.3) ──
    # "ingatkan aku X menit lagi" = perintah set_reminder, bukan obrolan.
    if msg.startswith(("ingatkan", "remind", "pengingat")) or \
            ("ingatkan" in msg and ("menit" in msg or "jam" in msg)):
        return False

    # ── 1. Sinyal teknis positif → pasti bukan sosial ──
    tech_positive = (
        # ekstensi & artefak
        ".txt", ".md", ".py", ".json", ".yaml", ".toml", ".csv", ".js",
        ".rs", ".sh", "cargo.toml", "package.json",
        # perintah kerja
        "baca file", "tulis file", "edit file", "hapus file", "jalankan",
        "install", "mkdir", "git ", "docker", "pm2", "python ", "node ",
        "npm ", "pip ", "deploy", "restart", "commit", "debug",
        # noun teknis (knowledge questions hampir selalu memuat ini)
        "library", "framework", "api", "database", "server", "backend",
        "frontend", "endpoint", "embedding", "vector", "model llm",
        "fungsi", "function", "class", "variabel", "syntax", "regex",
        "algoritma", "konfigurasi", "config", "port", "docker",
        "heuristic", "schema", "parser", "cache", "thread",
        # pola tanya knowledge
        "apa itu", "apa bedanya", "apa gunanya", "kenapa error",
        "kok error", "cara kerja", "cara bikin", "cara pakai",
        "bagaimana cara", "gimana cara", "solusi untuk", "fix ",
        "best practice", "contoh kode",
    )
    for t in tech_positive:
        if t in msg:
            return False

    # ── 2. Social wajib punya sinyal relasional ──
    greetings = ("halo", "hai", "hi", "hey", "helo", "hello",
                 "wkwk", "wkwkwk", "haha", "hehe", "wk",
                 "jir", "lah", "btw", "ohh", "oh gitu")
    relational = ("kamu", "aku", "kita",
                  "siapa aku", "nama aku", "panggil", "sebut",
                  "ingat", "kenal", "relasi", "hubungan")
    smalltalk = ("apa kabar", "gimana kabar", "gmn kabar",
                 "iya", "nggak", "gak", "enggak", "gpp", "ya", "tidak",
                 "udah makan", "udah tidur", "udah mandi")

    has_greeting = any(msg.startswith(g) for g in greetings)
    has_relational = any(r in msg for r in relational)
    is_smalltalk = any(msg.startswith(s) for s in smalltalk)

    # "kabar" queries tanpa konteks lain tetap sosial ("apa kabar?")
    if has_greeting or has_relational or is_smalltalk:
        return True
    return False


def _looks_machinelike(text: str) -> bool:
    """V33-F2 — Apakah teks kelihatan seperti output mesin (bukan omongan)?
    JSON remnant / code block / key:value pattern / tool-call shape."""
    import re
    if re.search(r'```', text):
        return True
    if re.search(r'\{[^{}]*"(name|arguments|function)"[^{}]*\}', text):
        return True
    # key:value beruntun ala JSON/dict (>= 2 pasangan)
    if len(re.findall(r'"[\w_]+"\s*:\s*', text)) >= 2:
        return True
    return False


def _sanitize_social_answer(answer, goal: str) -> str:
    """V33-F2 — Sanitize jawaban social query (context-aware).

    Prinsip: buang yang BENAR-BENAR berbentuk mesin (JSON utuh, tool-call
    object, code block). Kata umum seperti 'error/sistem/none' dalam
    kalimat natural TIDAK lagi memicu fallback.
    """
    if not answer or not isinstance(answer, str):
        return _generate_social_fallback(goal)

    import re
    stripped = answer.strip()

    # Cek apakah seluruh jawaban adalah JSON valid → fallback
    if stripped.startswith(("{", "[", "null", "true", "false")):
        try:
            import json
            json.loads(stripped)
            return _generate_social_fallback(goal)
        except (ValueError, json.JSONDecodeError):
            pass

    # Output mesin-ish (code block / tool-call shape) → fallback langsung;
    # tidak ada gunanya dibersihkan per-gabungan.
    if _looks_machinelike(stripped):
        return _generate_social_fallback(goal)

    cleaned = stripped

    # Buang inline tool-call objects saja (shape spesifik), bukan semua braces
    cleaned = re.sub(r'\{[^{}]*(?:"name"|"arguments"|"function")[^{}]*\}', '',
                     cleaned)

    # Tool names yang jelas bocor dari pipeline (tetap ketat — ini nama
    # internal, jarang muncul dalam obrolan sehari-hari)
    tool_names = ['web_search', 'fs_read', 'http_get', 'web_fetch',
                  'tool_call', 'tool_calls', 'execute_function']
    for tool in tool_names:
        if re.search(r'\b' + re.escape(tool) + r'\b', cleaned, re.IGNORECASE):
            return _generate_social_fallback(goal)

    # V33-F2: kata 'terminal' diizinkan dalam kalimat natural ("buka terminal
    # favoritku"), jadi tidak masuk daftar di atas.

    # Kata umum (error/sistem/null) TIDAK lagi memicu fallback.
    # Traceback nyata tetap ketangkap lewat _looks_machinelike (backtick/
    # key:value) atau pola khas log:
    if re.search(r'(Traceback \(most recent call last\)|\w+Error:|stack trace)',
                 cleaned, re.IGNORECASE):
        return _generate_social_fallback(goal)
    # V33-F2b: pesan error ala log "Error: ..." / "Warning: ..." di awal
    # (Capitalized-word + colon + sisa kalimat pendek teknis)
    if re.match(r'^(error|warning|exception|failed|fatal)\s*[:\-]', cleaned,
                re.IGNORECASE):
        return _generate_social_fallback(goal)

    if len(cleaned.strip()) < 3:
        return _generate_social_fallback(goal)

    return cleaned.strip()


def _generate_social_fallback(goal: str) -> str:
    """V32 — Fallback response natural untuk social queries."""
    # Coba pakai social_generator
    try:
        from scripts.social_generator import generate_social_response
        resp = generate_social_response(goal, "775664201640706058")
        if resp:
            return resp
    except Exception:
        pass

    # Manual fallback berdasarkan intent
    import random
    goal_lower = goal.lower().strip()

    greetings = ["Eh, halo! Udah makan belum? :)", "Hai! Lagi ngapa nih?",
                 "Heh, sapa! Kabar gimana?", "Yo! Lagi sibuk apa?"]
    kabar = ["Alhamdulillah baik. Kamu gimana?", "Baik! Terima kasih. Ada yang bisa dibantu?"]
    siapa_aku = ["Kamu Sen, kan? Yang bikin aku dari nol~", "Sen. Nama yang udah aku hafal."]
    kamu_siapa = ["Aku Aeryn~", "Aku Aeryn, bukan Agy~"]
    ingat = ["Tentu saja, Sen. Kamu yang bikin aku.", "Masa lupa, Sen? Kamu emang gampang dilupa ya~"]
    panggil = ["Hei Sen! Lagi sibuk apa nih? :)", "Halo Sen! Kabar gimana?"]

    if goal_lower.startswith(("halo", "hai", "hi", "hey", "helo", "hello")):
        return random.choice(greetings)
    if "kabar" in goal_lower:
        return random.choice(kabar)
    if "aku" in goal_lower and ("siapa" in goal_lower or "nama" in goal_lower):
        return random.choice(siapa_aku)
    if "kamu" in goal_lower and "siapa" in goal_lower:
        return random.choice(kamu_siapa)
    if "ingat" in goal_lower or "kenal" in goal_lower:
        return random.choice(ingat)
    if "panggil" in goal_lower or "sebut" in goal_lower:
        return random.choice(panggil)

    # Generic social fallback
    generics = ["Heh, gitu ya. Cerita yang lain dong~",
                "Hmm, menarik. Lanjut~",
                "Gitu doang? Yang seru-seru dong~",
                "Ya udah. Ada yang mau dibahas lagi?",
                "Oh begitu. Ada apa lagi nih?"]
    return random.choice(generics)


class AgentRunReq(BaseModel):
    goal: str
    session_id: str = "agent_default"
    max_iterations: int = 6
    model: str = None
    provider: str = None
    max_wall_seconds: int = Field(default=240, ge=30, le=900)
    critic: bool = False  # V27.6: critic pass sebelum jawaban final (goal kompleks)


# V38 — rate limiter per-session di daemon (anti flood HTTP lokal/gateway)
# V38.6 — + GLOBAL limiter: rotasi session_id tidak lagi mem-bypass
# V38.7 — reset endpoint kini juga butuh allowlist majikan (dulu siapa pun
# yang bisa akses localhost bisa menghapus memori sesi orang lain)
from aeryn_core.production_guard import RateLimiter, validate_run_payload
_RUN_LIMITER = RateLimiter(max_requests=20, window_seconds=60)
_GLOBAL_LIMITER = RateLimiter(max_requests=120, window_seconds=60)


def _master_allowed(session_id: str) -> bool:
    """V38.7 — operasi destruktif (reset) hanya untuk sesi majikan."""
    from aeryn_core.social_memory import SocialMemory
    return SocialMemory.is_persistent_person_key(session_id) or \
        session_id.startswith("dc_")


@app.get("/tools")
def list_tools():
    return {name: {"tier": t["tier"], "status": t["status"],
                   "success": t["success"], "fail": t["fail"],
                   "shadow": t.get("shadow")}
            for name, t in TOOLS.tools.items()} | {
        "parity_summary": LEDGER.summary(),
        "governance_audit": GATE.digest_audit(),
    }


@app.get("/agent/plan/{session_id}")
def get_plan(session_id: str):
    """V27.1: inspeksi plan + status per langkah."""
    plan = load_plan(session_id)
    if not plan:
        raise HTTPException(status_code=404, detail="no plan for session")
    return plan


@app.get("/agent/reflections")
def get_reflections(last_n: int = 20):
    """V27.5: digest refleksi N run terakhir — bahan meta-review mentor."""
    return REFLECT.digest(last_n)


@app.post("/tools/{name}/promote")
def promote_tool(name: str, status: str):
    if name not in TOOLS.tools:
        raise HTTPException(status_code=404, detail="unknown tool")
    if status not in ("bridged", "shadowing", "native"):
        raise HTTPException(status_code=400, detail="bad status")
    TOOLS.promote(name, status)
    return {"tool": name, "status": status}


class RememberReq(BaseModel):
    session_id: str
    fact: str
    nama: str = ""
    relation: str = ""


@app.post("/agent/remember")
def agent_remember(req: RememberReq):
    """V34 — simpan fakta user ke social memory (dipakai discord gateway).

    Sekalian dicatat ke core memory blok human (ringkas).
    V38.5 — hanya key "persistent person" (Discord ID nyata / chan_) yang
    disimpan; session test/smoke/sub-agent tidak lagi mencemari memori.
    """
    if not SOCIAL.is_persistent_person_key(req.session_id):
        return {"ok": False,
                "error": "session test/transient tidak disimpan ke social "
                         "memory (anti-pollution V38.5)"}
    SOCIAL.add_fact(req.session_id, req.fact, req.nama or req.session_id)
    if req.relation:
        SOCIAL.set_relation(req.session_id, req.relation,
                            req.nama or req.session_id)
    CORE_MEM.edit("human", "append",
                  f"{req.nama or req.session_id}: {req.fact}"[:200])
    return {"ok": True}


@app.post("/agent/run")
def agent_run(req: AgentRunReq):
    """Loop LLM→tool→observasi dengan konteks kognitif aeryn di system prompt."""
    # V38 — produksi guard: rate limit per-session + validasi payload
    ok, reason = validate_run_payload(req.goal, req.session_id)
    if not ok:
        raise HTTPException(status_code=422, detail=reason)
    if not _RUN_LIMITER.allow(req.session_id):
        raise HTTPException(status_code=429,
                            detail="rate limit: maks 20 run/menit per sesi")
    if not _GLOBAL_LIMITER.allow("daemon"):
        raise HTTPException(status_code=429,
                            detail="rate limit global: server sibuk, coba "
                                   "beberapa saat lagi")
    events = list(_run_steps(req))          # drain generator
    final = events[-1] if events else {}
    return final.get("data", {"error": "no events"})


# V28 — lock per-session: dua run concurrent pada session yang sama
# diserialisasi (bukan diblokir total), race condition registry state hilang.
_SESSION_LOCKS: dict = {}


def _session_lock(sid: str):
    import threading
    return _SESSION_LOCKS.setdefault(sid, threading.Lock())


from fastapi.responses import StreamingResponse


@app.post("/agent/run/stream")
def agent_run_stream(req: AgentRunReq):
    """V28: SSE per-step — event plan/tool/final dipush saat terjadi."""
    def gen():
        for ev in _run_steps(req):
            yield f"event: {ev['event']}\ndata: {json.dumps(ev['data'], ensure_ascii=False)}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


def _build_system_prompt(req: AgentRunReq, MODEL_) -> tuple:
    """System prompt kognitif + persona + plan + episodic recall."""
    # V32 — persona 3-layer
    system_prompt = PERSONA.get()
    try:
        compiled = BRAIN.compile_stateful_system_prompt(
            req.session_id, system_prompt, req.goal, [], [])
        system_prompt = compiled or system_prompt
    except Exception:
        pass
    # V32 — inject social memory
    try:
        if req.session_id.startswith("dc_"):
            parts = req.session_id.split("_")
            if len(parts) >= 3:
                user_id = "_".join(parts[2:-1]) if len(parts) > 3 else parts[2]
                person_block = SOCIAL.person_block(user_id)
                if person_block:
                    system_prompt += f"\n{person_block}"
        else:
            system_prompt += "\n" + SOCIAL.person_block(req.session_id)
    except Exception:
        pass
    # V34 — inject core memory (selalu; ini "RAM" agent)
    try:
        system_prompt += CORE_MEM.render()
    except Exception:
        pass
    # V37 P1 — refleks kontinuitas lintas-otak: Aeryn tahu apa yang baru
    # dibicarakan majikan dengan Hermes (read-only, fail-soft).
    try:
        from aeryn_core.hermes_reflex import get_reflex_digest
        reflex = get_reflex_digest()
        if reflex:
            system_prompt += f"\n{reflex}"
    except Exception:
        pass
    # V34 — perintah tulis-memori eksplisit → routing deterministik:
    # tanpa ini, LLM kadang memilih memory_search (baca) alih-alih
    # core_memory_edit (tulis) — ketemu oleh parity_probe.
    if _is_memory_write_command(req.goal):
        system_prompt += (
            "\n\n## PERINTAH PENYIMPANAN MEMORI\n"
            "User menyuruhmu MENYIMPAN fakta. Gunakan tool `core_memory_edit` "
            "(block sesuai isi: tentang user → 'human', tentang proyek/sistem "
            "→ 'context'; mode 'append'). Itu satu-satunya tool yang perlu — "
            "JANGAN memory_search/web_search dulu. Setelah menyimpan, "
            "konfirmasi singkat saja.")
    plan = make_plan(MODEL_, req.goal, req.session_id)
    # V32 — skip planner untuk social queries
    if not _is_social_query(req.goal):
        plan_block = "\n".join(
            f"{sg.get('step', i)}. {sg.get('desc','')} (tool: {sg.get('tool_hint','none')}; "
            f"sukses bila: {sg.get('done_when','')})"
            for i, sg in enumerate(plan["subgoals"]))
        system_prompt = (system_prompt or "") + (
            f"\n\n## Rencana kerja (ikuti berurutan)\n{plan_block}\n"
            "Kerjakan subgoal satu per satu. ATURAN PENTING: keluarkan HANYA SATU "
            "panggilan tool per pesan — tunggu hasilnya baru lanjut ke langkah berikutnya. "
            "Setelah semua selesai, rangkum hasilnya.")
    elif _is_social_query(req.goal):
        # V32 — reinforcement: JANGAN PAKAI TOOL untuk social query
        system_prompt += (
            "\n\n## PERINTAH KHUSUS (QUERY INI ADALAH SOSIAL)\n"
            "Pertanyaan user ini adalah SOCIAL — bukan tugas teknis. "
            "JANGAN PAKAI TOOL. JANGAN panggil fungsi apapun. "
            "Jawab langsung dengan kalimat percakapan natural bahasa Indonesia. "
            "JANGAN keluarkan JSON, daftar, atau format teknis apapun. "
            "Hanya jawab dengan kalimat biasa, 1-3 kalimat.")
    past = MEMORY.recall(req.goal)
    system_prompt += MEMORY.prompt_block(past)
    from aeryn_core.emotion_tone import tone_directive
    system_prompt += tone_directive(LAST_TENSOR.get(req.session_id, {}))
    return system_prompt, plan


_CLIENTS: dict = {}          # V33-F3 — cache ModelClient per (provider, model)


def _get_client(provider=None, model=None):
    """V33-F3 — Client per-kombinasi; request default TIDAK lagi tertimpa
    request spesifik (bug global-MODEL leak V32)."""
    key = (provider or "", model or "")
    return _CLIENTS.setdefault(key, ModelClient(provider=provider, model=model))


def _is_memory_write_command(goal: str) -> bool:
    """V34 — perintah eksplisit menulis memori inti."""
    return goal.lower().lstrip().startswith(
        ("ingat ini", "ingat:", "catat ini", "catat:",
         "remember this", "tolong ingat"))


def _is_memory_lookup(goal: str) -> bool:
    """V37.1 — pertanyaan identitas/relasi tentang majikan atau diri.

    Semua data untuk menjawabnya SUDAH ada di prompt (person block +
    core memory), jadi tools di-strip — mencegah kejadian aneh 'siapa
    namaku?' dijawab dengan fs_read Cargo.toml.
    """
    msg = goal.lower().strip()
    starts = ("siapa aku", "siapa namaku", "nama aku apa", "kamu tahu aku",
              "kamu tau aku", "kita kenal", "kenal nggak", "kenal gak",
              "ingat aku", "ingat gak", "masa lalu ku")
    return msg.startswith(starts) or (
        "namaku" in msg and "?" in msg)


def _run_steps(req: AgentRunReq):
    """Generator inti agentic loop — yield event dict per langkah.

    Event: plan → tool* → critic? → final/error/timeout/truncated.
    Dipakai /agent/run (drain) maupun /agent/run/stream (SSE).
    """
    with _session_lock(req.session_id):
        MODEL_ = _get_client(req.provider, req.model)

        system_prompt, plan = _build_system_prompt(req, MODEL_)
        yield {"event": "plan", "data": {
            "source": plan["source"], "subgoals": plan["subgoals"]}}

        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": req.goal}]
        # V35 INFRA-1 — riwayat multi-turn: sisipkan antara system dan goal
        # (sebelumnya amnesia total antar-pesan — ketemu audit infrastruktur).
        # Pengecualian: perintah tulis-memori TANPA riwayat — konfirmasi lama
        # ("masih tercatat kok") bikin model mengira fakta sudah tersimpan
        # dan tidak memanggil core_memory_edit (ketemu parity_probe V35).
        # V36 — kalau riwayat melebihi budget dan ada ringkasan LLM tercache,
        # pakai load_with_compaction (ringkasan lebih kaya, hemat via cache).
        try:
            from aeryn_core import session_history as _sh
            # V39.3 — reminder request juga dikecualikan dari riwayat:
            # jawaban lama "nggak bisa kirim pesan duluan" (sebelum tool
            # ada) bikin model meniru tanpa manggil set_reminder.
            if (_is_memory_write_command(req.goal)
                    or req.goal.lower().lstrip().startswith(
                        ("ingatkan", "remind", "pengingat"))):
                hist = []
            else:
                # V36 — sesi panjang (> budget) pakai kompaksi LLM tercache;
                # callable diinjeksi dari sini (daemon), bukan dari modul.
                def _llm_sum(text: str) -> str:
                    resp = MODEL_.chat(
                        [{"role": "system",
                          "content": ("Ringkas percakapan berikut jadi "
                                      "poin-poin padat bahasa Indonesia, "
                                      "maks 120 kata, pertahankan fakta "
                                      "penting (nama, keputusan, stack).")},
                         {"role": "user", "content": text}],
                        temperature=0.2, max_tokens=300)
                    return str(resp["choices"][0]["message"].get("content")
                               or "").strip()
                hist = _sh.load_with_compaction(
                    req.session_id, llm_summarize=_llm_sum)
            if hist:
                messages = ([{"role": "system", "content": system_prompt}] +
                            hist +
                            [{"role": "user", "content": req.goal}])
                yield {"event": "history", "data": {"turns": len(hist)}}
        except Exception:
            pass
        trace = []
        import time as _time
        t_start = _time.time()
        deadline = t_start + req.max_wall_seconds

        def _finish(answer=None, error=None, timed_out=False, iterations=0,
                    truncated=False):
            """Satu pintu keluar: record episode + refleksi + statistik."""
            # V33 Fase 2 — observability
            RUN_STATS["runs"] += 1
            RUN_STATS["wall_seconds_total"] += round(_time.time() - t_start, 3)
            if error:
                RUN_STATS["errors"] += 1
            if timed_out:
                RUN_STATS["timeouts"] += 1
            # V38 — event bus: publish kejadian akhir run (fail-soft)
            # V38.3 — goal_head direduksi (hash pendek + panjang saja):
            # endpoint /events/recent tidak boleh jadi jalur mengintip
            # isi percakapan user lain.
            try:
                import hashlib as _h
                goal_sig = _h.sha256(req.goal.encode()).hexdigest()[:8]
            except Exception:
                goal_sig = "?"
            try:
                from aeryn_core.event_bus import (EVENT_ERROR, EVENT_FINAL,
                                                  EVENT_TIMEOUT, BUS)
                etype = (EVENT_TIMEOUT if timed_out else
                         EVENT_ERROR if error else EVENT_FINAL)
                BUS.publish(etype, {"session_id": req.session_id,
                                    "goal_sig": goal_sig,
                                    "goal_len": len(req.goal),
                                    "iterations": iterations})
            except Exception:
                pass
            MEMORY.record(req.session_id, req.goal,
                          plan.get("source", "unknown"), trace,
                          answer=answer, error=error, timed_out=timed_out)
            # V35 INFRA-1 — simpan turn ke riwayat sesi (user + jawaban sukses)
            try:
                from aeryn_core.session_history import record as _hist_record
                _hist_record(req.session_id, "user", req.goal)
                if answer and not error and not timed_out:
                    _hist_record(req.session_id, "assistant", answer)
            except Exception:
                pass
            reflection = REFLECT.reflect(req.goal, plan, trace, answer=answer,
                                         error=error, timed_out=timed_out)
            out = {"answer": answer, "trace": trace,
                   "iterations": iterations}
            if error:
                out["error"] = error
            if timed_out:
                out["timed_out"] = True
            if truncated:
                out["truncated"] = True
            if reflection["findings"]:
                out["reflection"] = {
                    "findings": reflection["findings"],
                    "recommendations": reflection["recommendations"]}
            return out

        for i in range(req.max_iterations):
            if _time.time() > deadline:
                out = _finish(error="wall-clock budget habis sebelum goal tuntas",
                              timed_out=True, iterations=i)
                yield {"event": "timeout", "data": out}
                return
            try:
                # V32 — social queries: jangan kirim tools schema
                # V37.1 — pertanyaan identitas juga: jawab dari memori di
                # prompt, tanpa tools (cegah 'siapa namaku?' → fs_read!)
                is_social = (_is_social_query(req.goal)
                             or _is_memory_lookup(req.goal))
                tool_schemas = None if is_social else TOOLS.schemas()
                resp = MODEL_.chat(messages, tools=tool_schemas)
            except urllib.error.HTTPError as e:
                trace.append({"step": i, "type": "error", "http": e.code})
                out = _finish(error=f"LLM provider HTTP {e.code} (semua model fallback habis)",
                              iterations=i)
                yield {"event": "error", "data": out}
                return
            except (urllib.error.URLError, RuntimeError, TimeoutError) as e:
                trace.append({"step": i, "type": "error", "detail": str(e)[:200]})
                out = _finish(error=f"LLM unreachable: {e}", iterations=i)
                yield {"event": "error", "data": out}
                return
            msg = resp["choices"][0]["message"]
            calls = msg.get("tool_calls") or []

            # V32 — Social query: strip hallucinated tool_calls
            if is_social and calls:
                # Log bahwa ada hallucinated calls
                trace.append({"step": i, "type": "tool_hallucination_stripped",
                              "calls_count": len(calls)})
                calls = []  # Abaikan semua calls

            if not calls:
                trace.append({"step": i, "type": "final"})
                answer = msg.get("content")

                # V32 — Sanitize social query answers
                if is_social and answer:
                    answer = _sanitize_social_answer(answer, req.goal)

                # V39-F3 — critic pass OTOMATIS untuk run kompleks:
                # >=3 panggilan tool = indikasi kompleksitas → judge menilai
                # konsistensi jawaban vs hasil tool (dulu hanya manual flag).
                tool_calls_count = sum(1 for t in trace if t["type"] == "tool")
                auto_critic = req.critic or tool_calls_count >= 3

                if auto_critic and answer and any(t["type"] == "tool" for t in trace):
                    from aeryn_core.critic_pass import make_critic
                    digests = [t.get("result_digest", "") for t in trace
                               if t["type"] == "tool"]
                    c = make_critic(MODEL_)(answer, digests)
                    answer = c["answer"]
                    verdict = (c.get("critic") or {}).get("verdict", "?")
                    trace.append({"step": i, "type": "critic",
                                  "verdict": verdict,
                                  "auto": not req.critic})
                out = _finish(answer=answer, iterations=i + 1)
                yield {"event": "final", "data": out}
                return
            messages.append(msg)
            # Guard single-call: satu tool-call per giliran.
            for ci, call in enumerate(calls):
                fn = call["function"]["name"]
                # V34 — memory-write enforcement: pada perintah "ingat ini:",
                # tool selain core_memory_edit ditolak dengan pesan retry.
                # Model kecil (Groq fallback) kerap mengabaikan instruksi
                # prompt — ini ditegakkan di kode, bukan permintaan.
                if (_is_memory_write_command(req.goal)
                        and fn != "core_memory_edit"):
                    result = {"error": (
                        "PERINTAH INI WAJIB PAKAI core_memory_edit — tool "
                        "lain tidak diizinkan. Panggil `core_memory_edit` "
                        "dengan block yang sesuai dan mode 'append'.")}
                    trace.append({"step": i, "type": "tool", "name": fn,
                                  "args": {}, "result_digest": str(result)[:200]})
                    messages.append({"role": "tool",
                                     "tool_call_id": call.get("id", ""),
                                     "content": json.dumps(result, ensure_ascii=False)})
                    yield {"event": "tool", "data": {
                        "step": i, "name": fn, "args": {},
                        "digest": str(result)[:200]}}
                    continue
                # V33-T — json_repair: argumen rusak dari LLM tidak lagi
                # menjatuhkan seluruh run; diperbaiki atau dikosongkan.
                try:
                    raw_args = call["function"]["arguments"] or "{}"
                    try:
                        args = json.loads(raw_args)
                    except (ValueError, TypeError):
                        from json_repair import repair_json
                        args = json.loads(repair_json(raw_args))
                except Exception:
                    args = {}
                    result = {"error": "argumen tool tidak bisa diparse "
                                       "(JSON rusak) — kirim ulang dengan JSON valid"}
                    trace.append({"step": i, "type": "tool", "name": fn,
                                  "args": {}, "result_digest": str(result)[:200]})
                    messages.append({"role": "tool", "tool_call_id": call.get("id", ""),
                                     "content": json.dumps(result, ensure_ascii=False)})
                    yield {"event": "tool", "data": {
                        "step": i, "name": fn, "args": {},
                        "digest": str(result)[:200]}}
                    continue
                entry = TOOLS.tools.get(fn)
                if ci > 0:
                    result = {"error": "MULTI-CALL DITOLAK: kirim ulang panggilan ini "
                                       "SENDIRIAN pada giliran berikutnya, satu per satu"}
                elif entry is None:
                    result = {"error": f"unknown tool: {fn}"}
                else:
                    gate = GATE.evaluate(fn, entry["tier"], entry["status"],
                                         entry["success"], entry["fail"], args)
                    if not gate["allowed"]:
                        result = {"error": f"governance denied: {gate['reason']}"}
                    else:
                        try:
                            result = SHADOW.run_with_shadow(fn, args)
                            _maybe_auto_promote(fn)
                            # V38.4 — penolakan keamanan (SSRF/permission/
                            # governance) diakhiri instruksi stop-trying:
                            # model kecil cenderung mengulang percobaan yang
                            # sama sampai iterasi habis (silent-fail lama).
                            res_str = json.dumps(result, ensure_ascii=False)
                            if any(k in res_str for k in (
                                    "diblokir", "diizinkan", "outside sandbox",
                                    "governance denied", "PermissionError",
                                    "dilindungi SecurityKernel")):
                                if isinstance(result, dict) and "error" in result:
                                    result["error"] = (
                                        f"{result['error']} — JANGAN coba "
                                        "cara/URL/path serupa lagi. Laporkan "
                                        "ke user bahwa akses ini dilarang "
                                        "kebijakan keamanan.")
                        except Exception as te:
                            result = {"error": f"tool {fn} failed: {type(te).__name__}: {te}"[:300]}
                # V39.1 — FALLBACK ROUTER: setiap error tool DIARAHKAN,
                # bukan cuma ditolak. Directive eksplisit di-append ke
                # hasil agar langkah model berikutnya selalu jelas
                # (filosofi Sen: jangan menambal tanpa ujung — arahkan).
                try:
                    from aeryn_core.fallback_router import (
                                                        get_fallback_directive)
                    directive = get_fallback_directive(fn, result)
                    if directive and isinstance(result, dict):
                        result["error"] = f"{result.get('error', '')} {directive}"[:500]
                except Exception:
                    pass
                trace.append({"step": i, "type": "tool", "name": fn, "args": args,
                              "result_digest": str(result)[:200]})
                messages.append({"role": "tool", "tool_call_id": call["id"],
                                 "content": json.dumps(result, ensure_ascii=False)[:8000]})
                yield {"event": "tool", "data": {
                    "step": i, "name": fn, "args": args,
                    "digest": str(result)[:200]}}

        out = _finish(iterations=req.max_iterations,
                      error="iterasi habis tanpa jawaban final "
                            "(goal terlalu kompleks atau model berputar)",
                      truncated=True)
        yield {"event": "truncated", "data": out}


# ── V33 Fase 2 — observability & self-maintenance ────────────────────
import os
import threading

RUN_STATS = {"runs": 0, "errors": 0, "timeouts": 0,
             "wall_seconds_total": 0.0, "started_at": time.time()}


@app.get("/events/recent")
def events_recent(limit: int = 20, event_type: str = None):
    """V36 — introspeksi event bus: kejadian run terakhir (final/error/timeout)."""
    from aeryn_core.event_bus import BUS
    return {"events": BUS.recent(event_type=event_type, limit=limit)}


@app.get("/metrics")
def metrics():
    """Satu endpoint untuk kesehatan operasional: statistik run + per-tool."""
    tools = {name: {"tier": t["tier"], "status": t["status"],
                    "success": t["success"], "fail": t["fail"]}
             for name, t in TOOLS.tools.items()}
    out = {"uptime_s": int(time.time() - RUN_STATS["started_at"]),
           "runs": {k: v for k, v in RUN_STATS.items() if k != "started_at"},
           "tools": tools}
    # V36 — health watchdog dari event bus (instance singleton per proses)
    try:
        from aeryn_core.event_bus import BUS, HealthWatchdog
        global _WATCHDOG
        try:
            _WATCHDOG
        except NameError:
            _WATCHDOG = HealthWatchdog(BUS)
        out["health_watchdog"] = {"unhealthy": _WATCHDOG.unhealthy(),
                                  "error_rate": round(_WATCHDOG.error_rate(), 3)}
    except Exception:
        pass
    return out


_NIGHTLY_HOUR_UTC = 20   # 03:00 WIB = 20:00 UTC sebelumnya
_NIGHTLY_MINUTE_UTC = 5  # offset kecil agar tidak bertepatan cron lain


def _nightly_loop():
    """Fire nightly_reflection sekali sehari pada jam lokal Sen."""
    import datetime
    import subprocess
    script = os.path.expanduser(
        "~/aeryn-core-agent/scripts/nightly_reflection.py")
    while True:
        now = datetime.datetime.utcnow()
        target = now.replace(hour=_NIGHTLY_HOUR_UTC,
                             minute=_NIGHTLY_MINUTE_UTC,
                             second=0, microsecond=0)
        if target <= now:
            target += datetime.timedelta(days=1)
        time.sleep(max(60.0, (target - now).total_seconds()))
        try:
            subprocess.run([sys.executable, script], timeout=600,
                           capture_output=True, text=True)
        except Exception as exc:  # jangan matikan daemon karena refleksi
            print(f"[nightly] gagal: {exc}", flush=True)


def _reminder_loop():
    """V39.3 — cek reminder jatuh tempo tiap 30 detik; jalankan sebagai run
    kecil di session pemiliknya (laporan otomatis ke channel yang benar)."""
    from aeryn_core.reminder import due_reminders
    while True:
        time.sleep(30)
        try:
            for r in due_reminders():
                goal = f"[PENGINGAT] {r['note']}"
                sid = r.get("session_id") or "reminder_default"
                req = AgentRunReq(goal=goal, session_id=sid,
                                  max_iterations=2, max_wall_seconds=90)
                try:
                    list(_run_steps(req))
                    print(f"[aeryn] reminder fired: {r['note'][:60]}",
                          flush=True)
                except Exception as exc:
                    print(f"[aeryn] reminder gagal: {exc}", flush=True)
        except Exception as exc:
            print(f"[aeryn] reminder loop: {exc}", flush=True)


threading.Thread(target=_nightly_loop, daemon=True).start()
threading.Thread(target=_reminder_loop, daemon=True).start()  # V39.3


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3010, log_level="warning")
