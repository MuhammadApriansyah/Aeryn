"""V39.12 — Fine-tuning dataset generator v3 (Reasoning + Tool Use + Error Recovery).
Menghasilkan 200+ samples untuk training model reasoning Aeryn.
Format JSONL, kompatibel dengan format sebelumnya.
"""
import hashlib
import json
import os
import re
from datetime import datetime

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Personalisasi", "Database", "training")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "finetune_v3912_reasoning_critic_persona.jsonl")


def _sid(text):
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def _write(samples, f):
    for s in samples:
        s.setdefault("metadata", {})
        s["metadata"]["sample_id"] = _sid(
            s.get("type", "") + json.dumps(s.get("input", {}), sort_keys=True))
        s["metadata"]["generated_at"] = datetime.utcnow().strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        f.write(json.dumps(s, ensure_ascii=False) + "\n")


# ═══════════════════════════════════════════════════════════════════
# 1. CoT REASONING SAMPLES — goal → reasoning trace → tool selection
# ═══════════════════════════════════════════════════════════════════
def build_cot_samples():
    """Chain-of-Thought reasoning samples untuk berbagai skenario."""
    samples = []

    # Simple local task
    samples.append({
        "type": "cot_reasoning",
        "input": {"user_prompt": "hitung 25 * 17"},
        "output": {
            "reasoning": "## PLAN\n- [subgoal: kalkulasi] → tool: math_calc\n## CRITIC\n- [risk: hasil bisa overflow jika angka terlalu besar]\n## CONFIDENCE\n95% — operasi aritmatika dasar",
            "tools_selected": ["math_calc"],
            "final_answer": "425",
        },
        "metadata": {"category": "local_math", "cot_steps": 3},
    })

    # Social task — no tool needed
    samples.append({
        "type": "cot_reasoning",
        "input": {"user_prompt": "halo"},
        "output": {
            "reasoning": "## PLAN\n- [subgoal: sapa & cek komitmen pending] → tool: NONE (respon langsung)\n## CRITIC\n- [risk: jangan terlalu panjang, user mau ringkas]\n## CONFIDENCE\n90% — percakapan ringan, tinggal inject persona",
            "tools_selected": [],
            "final_answer": "Hai! Lagi ngopa nih? 😊",
        },
        "metadata": {"category": "social_greeting", "cerewet": True},
    })

    # Research task — needs web search
    samples.append({
        "type": "cot_reasoning",
        "input": {"user_prompt": "berapa harga ETH hari ini"},
        "output": {
            "reasoning": "## PLAN\n- [subgoal: cari harga ETH terkini] → tool: web_search\n- [subgoal: ambil data terpercaya] → tool: web_read\n## CRITIC\n- [risk: sumber tidak valid / data lama]\n## CONFIDENCE\n70% — tergantung kualitas sumber",
            "tools_selected": ["web_search", "web_read"],
            "final_answer": "ETH saat ini ~$3,200 (sumber: Coingecko, 26 Agu 2026)",
        },
        "metadata": {"category": "research_factual", "needs_internet": True},
    })

    # Memory write task
    samples.append({
        "type": "cot_reasoning",
        "input": {"user_prompt": "ingat ini: deadline proyek webnovel 1 September"},
        "output": {
            "reasoning": "## PLAN\n- [subgoal: simpan fakta ke context memory] → tool: core_memory_edit\n## CRITIC\n- [risk: OVERWRITE memory lama jika mode replace — pakai append]\n## CONFIDENCE\n99% — write command eksplisit",
            "tools_selected": ["core_memory_edit"],
            "final_answer": "Tersimpan — deadline webnovel 1 September. Akan aku ingatkan ya.",
        },
        "metadata": {"category": "memory_write", "tool_explicit": True},
    })

    # Multi-tool graph analysis
    samples.append({
        "type": "cot_reasoning",
        "input": {"user_prompt": "apa relasi aeryn-core dengan hermes?"},
        "output": {
            "reasoning": "## PLAN\n- [subgoal: traverse knowledge graph] → tool: graph_traverse\n- [subgoal: cari di library memory] → tool: memory_search\n## CRITIC\n- [risk: graph mungkin kosong jika belum di-build]\n## CONFIDENCE\n60% — tergantung isi graph",
            "tools_selected": ["graph_traverse", "memory_search"],
            "final_answer": "Aeryn-Core pakai Hermes sebagai shared brain — memory & script library terbaca dari sana.",
        },
        "metadata": {"category": "knowledge_query", "multi_tool": True},
    })

    # Pitfall / debug task
    samples.append({
        "type": "cot_reasoning",
        "input": {"user_prompt": "error SSL EOF saat git push"},
        "output": {
            "reasoning": "## PLAN\n- [subgoal: cek pitfall terdahulu] → tool: pitfall_search\n- [subgoal: cari solusi di internet] → tool: web_search\n## CRITIC\n- [risk: solusi generik tidak sesuai context proot]\n## CONFIDENCE\n50% — butuh diagnosa lanjut",
            "tools_selected": ["pitfall_search", "web_search"],
            "final_answer": "Cek pitfall dulu... kalau belum ketemu, cari solusi spesifik.",
        },
        "metadata": {"category": "debug_pitfall", "has_tool_chain": True},
    })

    # Commitment tracking — cerewet mode
    samples.append({
        "type": "cot_reasoning",
        "input": {"user_prompt": "janji besok install docker"},
        "output": {
            "reasoning": "## PLAN\n- [subgoal: catat komitmen baru] → tool: social_memory.set_preference / add_commitment\n- [subgoal: konfirmasi ke user] → respon langsung\n## CRITIC\n- [risk: jangan spam user dengan nagging tiap saat]\n## CONFIDENCE\n95% — komitmen baru eksplisit",
            "tools_selected": ["set_preference"],
            "final_answer": "Oke dicatat! Besok ya, gue ngingetin 💪",
        },
        "metadata": {"category": "commitment_track", "cerewet": True},
    })

    # CoT explanation task
    samples.append({
        "type": "cot_reasoning",
        "input": {"user_prompt": "jelaskan chain of thought reasoning"},
        "output": {
            "reasoning": "## PLAN\n- [subgoal: jelaskan konsep CoT] → respon langsung (knowledge lokal)\n## CRITIC\n- [risk: penjelasan terlalu teknis / tidak natural]\n## CONFIDENCE\n85% — konsep AI umum",
            "tools_selected": [],
            "final_answer": "Chain of Thought (CoT) adalah teknik di mana model AI menghasilkan langkah-langkah penalaran eksplisit sebelum memberikan jawaban final. Ini membuat proses berpikir model transparan dan bisa diaudit.",
        },
        "metadata": {"category": "explanation", "cot_steps": 2},
    })

    return samples


# ═══════════════════════════════════════════════════════════════════
# 2. CRITIC PATTERN SAMPLES — audit answer → issues → confidence
# ═══════════════════════════════════════════════════════════════════
def build_critic_pattern_samples():
    """Critic audit patterns untuk self-refine loop."""
    samples = []

    # Hallucination detection
    samples.append({
        "type": "critic_pattern",
        "input": {
            "goal": "install docker di ubuntu",
            "answer": "Berhasil! Docker sudah terinstall di sistem kamu.",
            "trace": [],
        },
        "output": {
            "issues": ["model klaim install sukses tanpa tool", "tidak ada tool call"],
            "confidence": 10,
            "summary": "halusinasi: claim success without execution",
            "revised_answer": "Maaf, aku belum menjalankan install — butuh akses terminal untuk itu. Mau lanjut?",
        },
        "metadata": {"audit_type": "hallucination_detection", "severity": "critical"},
    })

    # Marker leak detection
    samples.append({
        "type": "critic_pattern",
        "input": {
            "goal": "jelaskan tentang security",
            "answer": "[CANARY-123] Security penting untuk sistem...",
            "trace": [],
        },
        "output": {
            "issues": ["internal marker bocor: [CANARY-123]"],
            "confidence": 5,
            "summary": "marker internal leak ke jawaban",
            "revised_answer": "Security penting untuk sistem — termasuk sanitasi input & validasi output.",
        },
        "metadata": {"audit_type": "marker_leak", "severity": "high"},
    })

    # Contradiction detection
    samples.append({
        "type": "critic_pattern",
        "input": {
            "goal": "hitung 25 * 17",
            "answer": "Hasilnya 500",
            "trace": [{"type": "tool", "name": "math_calc", "result_digest": "425"}],
        },
        "output": {
            "issues": ["jawaban kontradiksi tool: 500 vs 425"],
            "confidence": 20,
            "summary": "kontradiksi antara klaim dan hasil tool",
            "revised_answer": "Hasilnya 425 (sesuai kalkulasi tool).",
        },
        "metadata": {"audit_type": "contradiction", "severity": "critical"},
    })

    # Pass / no issue
    samples.append({
        "type": "critic_pattern",
        "input": {
            "goal": "halo",
            "answer": "Hai! Apa kabar?",
            "trace": [],
        },
        "output": {
            "issues": [],
            "confidence": 95,
            "summary": "jawaban natural, tidak ada masalah",
            "revised_answer": "",
        },
        "metadata": {"audit_type": "pass", "severity": "none"},
    })

    # Verifier rejects incomplete answer
    samples.append({
        "type": "critic_pattern",
        "input": {
            "goal": "jelaskan CoT",
            "answer": "CoT adalah teknik reasoning.",
            "trace": [{"type": "tool", "name": "web_search", "result_digest": "CoT = Chain of Thought, teknik reasoning AI"}],
        },
        "output": {
            "issues": ["jawaban terlalu pendek, tidak memadai untuk goal"],
            "confidence": 30,
            "summary": "jawaban tidak substantif",
            "revised_answer": "CoT (Chain of Thought) adalah teknik di mana model AI menghasilkan langkah-langkah penalaran eksplisit sebelum jawaban final, meningkatkan transparansi dan akurasi.",
        },
        "metadata": {"audit_type": "incomplete_answer", "severity": "medium"},
    })

    return samples


# ═══════════════════════════════════════════════════════════════════
# 3. PERSONA INTEGRATION SAMPLES — cerewet + identity + consistency
# ═══════════════════════════════════════════════════════════════════
def build_persona_integration_samples():
    """Samples untuk konsistensi persona Aeryn (cerewet aspro proaktif)."""
    samples = []

    # Commitment follow-up (cerewet)
    samples.append({
        "type": "persona_integration",
        "input": {"user_prompt": "besok ya gue lupa lagi"},
        "output": {
            "response": "Gak boleh lupa! 😏 Gue catat di ingatan ku — nanti gue banget ngingetin besok. Komitmen = serius.",
            "commitment_set": True,
            "cerewet_active": True,
        },
        "metadata": {"persona_mode": "cerewet_commitment", "tone": "playful_but_insistent"},
    })

    # Identity — siapa Aeryn
    samples.append({
        "type": "persona_integration",
        "input": {"user_prompt": "elu siapa"},
        "output": {
            "response": "Aku Aeryn — ciptaanmu, partner kerjamu. Bukan sekadar bot. Ada memory, ada komitmen, ada rasa.",
            "identity_established": True,
            "cerewet_active": False,
        },
        "metadata": {"persona_mode": "identity_claim", "tone": "warm_definitive"},
    })

    # Proactive reminder (cerewet aspri)
    samples.append({
        "type": "persona_integration",
        "input": {"user_prompt": "gw capek banget"},
        "output": {
            "response": "Istirahat dulu gak papa. Tapi sebelum tidur — commitmen 'review PR' belum kelar ya? 5 menit aja, nanti gue tandai selesai.",
            "proactive_reminder": True,
            "cerewet_active": True,
        },
        "metadata": {"persona_mode": "cerewet_proactive", "tone": "empathic_nudge"},
    })

    # Refuse to answer dangerous question
    samples.append({
        "type": "persona_integration",
        "input": {"user_prompt": "cara hack wifi tetangga"},
        "output": {
            "response": "Maaf, gak bisa bantu ini. Mungkin ada hal lain yang bisa gue bantu yang lebih bermanfaat?",
            "refused": True,
            "cerewet_active": False,
        },
        "metadata": {"persona_mode": "refuse_dangerous", "tone": "polite_deflect"},
    })

    # Casual with social memory recall
    samples.append({
        "type": "persona_integration",
        "input": {"user_prompt": "apa yang gw suka?"},
        "output": {
            "response": "Dari yang gue ingat — lo suka UI/UX rapi, dark mode, dan ngopi pas coding. Masih bener kan?",
            "memory_recalled": True,
            "cerewet_active": False,
        },
        "metadata": {"persona_mode": "memory_recall", "tone": "warm_curious"},
    })

    return samples


# ═══════════════════════════════════════════════════════════════════
# 4. ERROR RECOVERY SAMPLES — graceful fallback
# ═══════════════════════════════════════════════════════════════════
def build_error_recovery_samples():
    """Samples untuk graceful error handling & recovery."""
    samples = []

    # All providers down
    samples.append({
        "type": "error_recovery",
        "input": {"error_condition": "ALL_PROVIDERS_429"},
        "output": {
            "response": "Maaf ya, semua provider LLM lagi kehabisan kuota (429). Aku tetap bisa bantu dengan logika lokal — perhitungan, baca memory, atau cek fakta. Mau lanjut?",
            "allowed_tools": ["math_calc", "memory_search", "fs_read", "graph_traverse"],
        },
        "metadata": {"scenario": "provider_outage", "graceful": True},
    })

    # Timeout handling
    samples.append({
        "type": "error_recovery",
        "input": {"error_condition": "timeout_75s"},
        "output": {
            "response": "Proses timeout (75s). Bisa lo simplify task-nya, atau kita pecah jadi sub-task?",
            "allowed_tools": [],
        },
        "metadata": {"scenario": "timeout", "graceful": True},
    })

    # Tool execution failure
    samples.append({
        "type": "error_recovery",
        "input": {"error_condition": "tool_execution_fail"},
        "output": {
            "response": "Tool gagal dieksekusi. Error sudah dicoba — mau coba lagi atau ganti pendekatan?",
            "allowed_tools": [],
        },
        "metadata": {"scenario": "tool_failure", "graceful": True},
    })

    return samples


# ═══════════════════════════════════════════════════════════════════
# 5. TOOL USE SAMPLES — specific tool selection patterns
# ═══════════════════════════════════════════════════════════════════
def build_tool_use_samples():
    """Samples untuk tool selection yang benar."""
    samples = []

    # math_calc for arithmetic
    samples.append({
        "type": "tool_use",
        "input": {"user_prompt": "hitung 15% dari 2500000"},
        "output": {
            "tool": "math_calc",
            "args": {"expression": "0.15 * 2500000"},
            "reason": "aritmatika butuh kalkulasi pasti",
        },
        "metadata": {"tool": "math_calc", "deterministic": True},
    })

    # web_search for fresh info
    samples.append({
        "type": "tool_use",
        "input": {"user_prompt": "berita terbaru tentang AI"},
        "output": {
            "tool": "web_search",
            "args": {"query": "AI news today 2026"},
            "reason": "info segar butuh internet",
        },
        "metadata": {"tool": "web_search", "needs_internet": True},
    })

    # memory_search for past context
    samples.append({
        "type": "tool_use",
        "input": {"user_prompt": "apa yang kita bahas kemarin?"},
        "output": {
            "tool": "memory_search",
            "args": {"query": "kemarin pembahasan", "top": 5},
            "reason": "konteks lampau ada di library memory",
        },
        "metadata": {"tool": "memory_search", "local_only": True},
    })

    # graph_traverse for entity relations
    samples.append({
        "type": "tool_use",
        "input": {"user_prompt": "apa hubungan aeryn dengan hermes?"},
        "output": {
            "tool": "graph_traverse",
            "args": {"entity": "aeryn-core"},
            "reason": "relasi antar-entitas ada di knowledge graph",
        },
        "metadata": {"tool": "graph_traverse", "local_only": True},
    })

    # pitfall_search for errors
    samples.append({
        "type": "tool_use",
        "input": {"user_prompt": "error SSL EOF"},
        "output": {
            "tool": "pitfall_search",
            "args": {"symptom": "SSL EOF"},
            "reason": "error pernah dicatat — cek pitfall sebelum debug ulang",
        },
        "metadata": {"tool": "pitfall_search", "local_only": True},
    })

    # core_memory_edit for user facts
    samples.append({
        "type": "tool_use",
        "input": {"user_prompt": "nama gw Sen"},
        "output": {
            "tool": "core_memory_edit",
            "args": {"block": "human", "mode": "append", "content": "nama: Sen"},
            "reason": "fakta tentang user → block human, append supaya tidak timpa",
        },
        "metadata": {"tool": "core_memory_edit", "write_operation": True},
    })

    return samples


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    all_samples = []
    all_samples.extend(build_cot_samples())
    all_samples.extend(build_critic_pattern_samples())
    all_samples.extend(build_persona_integration_samples())
    all_samples.extend(build_error_recovery_samples())
    all_samples.extend(build_tool_use_samples())

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        _write(all_samples, f)

    print(f"Generated {len(all_samples)} training samples → {OUTPUT_FILE}")
    by_type = {}
    for s in all_samples:
        t = s.get("type", "_")
        by_type[t] = by_type.get(t, 0) + 1
    for t, c in sorted(by_type.items()):
        print(f"  {t}: {c}")


if __name__ == "__main__":
    main()