"""V31.3 — VerificationGate: klaim faktual wajib didukung bukti tool.

Lapisan deterministik (0 LLM) yang melengkapi CriticPass (LLM-based):
deteksi kalimat berpola klaim faktual ("file sudah diubah", "server berjalan",
"versinya adalah X") lalu cek apakah ada tool-call di trace yang relevan
dengan klaim tersebut. Klaim tanpa bukti → ditandai + jawaban diberi
caveat eksplisit (bukan diblok — transparan lebih baik dari senyap).

Pola klaim & bukti yang cocok:
  - "diubah/ditulis/diperbarui"  → butuh tool tulis (terminal/write)
  - "berjalan/jalan/online"      → butuh terminal/healthcheck
  - "versi X / isi file Y"       → butuh fs_read pada path serupa
"""
import re

# pola klaim → jenis bukti yang harus ada
CLAIM_PATTERNS = [
    (re.compile(r"\b(sudah|telah|berhasil)\s+(diubah|ditulis|diedit|diperbarui|dihapus)\b", re.I),
     "write", "klaim perubahan file"),
    (re.compile(r"\b(server|daemon|service|proses)\s+\w*\s*(sudah\s+)?(berjalan|jalan|online|aktif)\b", re.I),
     "process", "klaim proses berjalan"),
    (re.compile(r"\b(versi[nya]*|version)\s*(adalah|:)?\s*[\w.-]+", re.I),
     "read", "klaim versi"),
    (re.compile(r"\b(isi|konten)\s+(file|dari)\b", re.I),
     "read", "klaim isi file"),
    (re.compile(r"\b(terinstal|terinstall|installed|terpasang)\b", re.I),
     "process", "klaim instalasi"),
]

WRITE_TOOLS = {"terminal"}          # penulisan via terminal tier power
READ_TOOLS = {"fs_read"}
PROCESS_TOOLS = {"terminal", "http_get"}


def check_claims(answer: str, trace: list) -> dict:
    """Return {claims_found, unsupported:[...], covered:bool}."""
    if not answer:
        return {"claims_found": 0, "unsupported": [], "covered": True}
    tools_used = {t.get("name") for t in trace if t.get("type") == "tool"}
    # digest hasil tool — bukti konten
    digests = " ".join(str(t.get("result_digest", ""))
                       for t in trace if t.get("type") == "tool").lower()

    unsupported = []
    total = 0
    for pat, need, label in CLAIM_PATTERNS:
        if not pat.search(answer):
            continue
        total += 1
        ok = False
        if need == "write":
            ok = bool(tools_used & WRITE_TOOLS) and any(
                k in digests for k in ("exit_code", "written", "success"))
        elif need == "read":
            ok = bool(tools_used & READ_TOOLS) and len(digests) > 40
        elif need == "process":
            ok = bool(tools_used & PROCESS_TOOLS)
        if not ok:
            unsupported.append(label)

    return {"claims_found": total, "unsupported": unsupported,
            "covered": not unsupported}


def annotate_answer(answer: str, check: dict) -> str:
    """Tambahkan caveat transparan bila ada klaim tak terdukung.
    Tidak memblokir jawaban — Aeryn jujur soal batas pengetahuannya."""
    if check["covered"] or not answer:
        return answer
    items = "; ".join(check["unsupported"])
    caveat = (f"\n\n> ⚠️ Verifikasi: sebagian klaim ({items}) tidak didukung "
              "bukti tool pada sesi ini. Sebagai langkah hati-hati, verifikasi "
              "manual disarankan.")
    return answer + caveat
