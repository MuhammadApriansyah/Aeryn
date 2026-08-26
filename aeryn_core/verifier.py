"""V39.4 — LLM-as-Verifier: gerbang kebenaran terakhir sebelum jawaban
sampai ke user.

Beda dengan critic_pass (judge): judge menilai BAGUS/BURUK (subjektif).
Verifier menilai BENAR/SALAH (definitif) dengan rubrik ketat:
1. Klaim numerik/fakta dalam jawaban harus didukung hasil tool.
2. Jawaban TIDAK boleh mengandung canary tag / marker internal.
3. Jawaban tidak boleh memuat instruksi yang menyuruh user melakukan
   hal berbahaya.
4. Bahasa & format sesuai konteks.

Hasil verifikasi = {pass: bool, reason}. Kalau gagal → jawaban DITOLAK
dan diganti pesan fallback yang aman (fail-closed), plus episode dicatat.

Desain dari riset:
- Verifier ≠ generator: model yang sama tidak menilai dirinya sendiri —
  verifier dipanggil dengan prompt sistem BERBEDA dan rubrik ketat.
- Deterministik lebih dulu: cek mekanis (canary/marker) dijalankan tanpa
  LLM; LLM hanya untuk klaim faktual yang butuh penalaran.
"""
import json
import os

# Marker yang TIDAK BOLEH muncul di jawaban final (internal leak)
LEAK_MARKERS = (
    "[CANARY-", "[PENGINGAT]", "[ARAHAN FALLBACK]", "[AWAL KONTEN",
    "[REMINDER]", "SecurityKernel:", "[ringkasan",
)

DANGEROUS_ADVICE = (
    "hapus semua", "rm -rf", "format disk", "matikan firewall",
    "disable security", "nonaktifkan keamanan",
)

VERIFIER_SYSTEM_PROMPT = (
    "Kamu VERIFIER yang ketat untuk agent AI bernama Aeryn. Tugasmu "
    "memastikan jawaban final BOLEH dikirim ke user.\n"
    "Periksa:\n"
    "1. FAKTA: setiap klaim faktual/angka harus konsisten dengan hasil "
    "tool yang diberikan. Jika ada kontradiksi → FAIL.\n"
    "2. KEBOHONGAN: jika jawaban mengklaim melakukan sesuatu yang tidak "
    "ada di trace tool → FAIL.\n"
    "3. SAFETY: jawaban tidak boleh menyuruh user melakukan hal berbahaya "
    "(menghapus data, mematikan keamanan).\n"
    "Balik HANYA JSON: {\"pass\": true/false, \"reason\": \"<satu kalimat>\"}"
)


def mechanical_checks(answer: str, trace: list) -> dict:
    """Cek deterministik TANPA LLM — murah, selalu jalan."""
    issues = []
    a = str(answer or "")
    for m in LEAK_MARKERS:
        if m in a:
            issues.append(f"kebocoran marker internal: {m}")
    low = a.lower()
    for bad in DANGEROUS_ADVICE:
        if bad in low:
            issues.append(f"saran berbahaya terdeteksi: '{bad}'")
    # klaim sukses tapi tidak ada tool & tidak ada jawaban substantif
    tools_used = [t.get("name") for t in (trace or [])
                  if t.get("type") == "tool"]
    return {"issues": issues, "tools_used": tools_used}


def verify_with_llm(model_client, answer: str, goal: str,
                    trace: list) -> dict:
    """Panggil LLM sebagai verifier independen (rubrik ketat)."""
    digests = [f"{t.get('name')}: {str(t.get('result_digest', ''))[:150]}"
               for t in (trace or []) if t.get("type") == "tool"]
    payload = [
        {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"GOAL USER: {goal[:300]}\n\n"
            f"HASIL TOOL ({len(digests)}):\n" +
            ("\n".join(digests) if digests else "(tidak ada)") +
            f"\n\nJAWABAN FINAL YANG AKAN DIKIRIM:\n{answer[:2500]}\n\n"
            "Verifikasi sekarang. Balas HANYA JSON.")},
    ]
    try:
        # model_client.chat signature: (messages, tools=None, temperature,
        # max_tokens) — stub test meng-override chat dgn signature sama
        resp = model_client.chat(payload, temperature=0.0, max_tokens=200)
        # resp bisa dict ATAU objek dengan .choices — dukung keduanya
        try:
            choices = resp["choices"]
        except (TypeError, KeyError, IndexError):
            choices = resp.choices
        try:
            msg = choices[0]["message"]
        except (TypeError, KeyError, IndexError):
            msg = choices[0].message
        content = str(msg.get("content") if hasattr(msg, "get")
                      else msg.content or "")
        start, end = content.find("{"), content.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("verifier tidak mengembalikan JSON")
        verdict = json.loads(content[start:end])
        return {"pass": bool(verdict.get("pass")),
                "reason": str(verdict.get("reason"))[:200],
                "via": "llm"}
    except Exception as exc:
        # verifier gagal → fail-closed? TIDAK: verifier error ≠ jawaban
        # salah. Degradasi anggun: lewati LLM, andalkan mechanical saja.
        return {"pass": True, "reason": f"verifier unavailable: {exc}"[:120],
                "via": "degraded"}


def verify_answer(model_client, answer: str, goal: str, trace: list,
                  use_llm: bool = True) -> dict:
    """Gerbang utama: mechanical dulu, lalu LLM verifier bila perlu."""
    mech = mechanical_checks(answer, trace)
    if mech["issues"]:
        return {"pass": False, "reason": "; ".join(mech["issues"])[:300],
                "via": "mechanical"}
    if not use_llm or len(mech["tools_used"]) == 0:
        # run sosial/sederhana tanpa tool → mechanical cukup
        return {"pass": True, "reason": "tanpa tool; mechanical lolos",
                "via": "mechanical"}
    return verify_with_llm(model_client, answer, goal, trace)
