"""V27.6 — CriticPass (div3): pemeriksaan fakta opsional sebelum jawaban final.

Goal kompleks (?critic=true) mendapat pass kedua: draft jawaban dikirim ke
LLM dengan prompt kritik "temukan kesalahan fakta/logika". Kalau kritik
menemukan masalah konkret → satu iterasi revisi. Heuristic guard: critic
hanya jalan kalau jawaban memakai hasil tool (bukan obrolan kosong).
"""
import json

CRITIC_PROMPT = """Kamu adalah kritikus ketat Aeryn (divisi reasoning). Periksa \
draft jawaban berikut TERHADAP bukti tool yang tersedia. Cari: klaim tanpa \
bukti, angka/nama yang tidak ada di bukti, kontradiksi internal. Balas JSON:
{"issues": ["..."], "verdict": "approved"|"revise"}
Maksimal 3 issues. Jika tidak ada masalah nyata, verdict approved."""


def make_critic(model_client):
    def critic(draft_answer: str, tool_digests: list) -> dict:
        """Kembalikan jawaban final (mungkin sudah direvisi) + metadata kritik."""
        evidence = "\n".join(f"- {d[:200]}" for d in tool_digests[:8]) or "(tidak ada)"
        msgs = [
            {"role": "system", "content": CRITIC_PROMPT},
            {"role": "user", "content":
                f"BUKTI TOOL:\n{evidence}\n\nDRAFT JAWABAN:\n{draft_answer}\n\nJSON:"},
        ]
        try:
            resp = model_client.chat(msgs, tools=None, temperature=0.1,
                                     max_tokens=600)
            raw = resp["choices"][0]["message"].get("content") or ""
            start, end = raw.find("{"), raw.rfind("}")
            if start < 0 or end <= start:
                return {"answer": draft_answer, "critic": "unparseable"}
            data = json.loads(raw[start:end + 1])
            issues = [i for i in (data.get("issues") or []) if isinstance(i, str)]
            verdict = data.get("verdict")
            if verdict == "revise" and issues and tool_digests:
                # Satu iterasi revisi dengan daftar masalah
                revise_msgs = [
                    {"role": "system",
                     "content": "Perbaiki draft sesuai kritik. Pertahankan "
                                "fakta dari bukti; hapus klaim tak terdukung. "
                                "Balas jawaban final saja tanpa komentar."},
                    {"role": "user", "content":
                        f"BUKTI:\n{evidence}\n\nDRAFT:\n{draft_answer}\n\n"
                        f"KRITIK:\n" + "\n".join(f"- {i}" for i in issues[:3])},
                ]
                resp2 = model_client.chat(revise_msgs, tools=None,
                                          temperature=0.3, max_tokens=1200)
                revised = resp2["choices"][0]["message"].get("content")
                if revised:
                    return {"answer": revised.strip(),
                            "critic": {"verdict": "revised", "issues": issues}}
            return {"answer": draft_answer,
                    "critic": {"verdict": verdict or "unknown", "issues": issues}}
        except Exception as e:
            # Fail-soft: kritik gagal ≠ run gagal — pakai draft apa adanya
            return {"answer": draft_answer,
                    "critic": {"verdict": "critic_error", "error": str(e)[:120]}}

    return critic
