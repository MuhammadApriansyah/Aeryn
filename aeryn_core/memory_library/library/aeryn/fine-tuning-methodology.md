# Metodologi Fine-Tuning Menyeluruh untuk Aeryn-Core

> Dibuat V38.5 (2026-08-25) atas permintaan Sen: riset metode fine-tuning
> dari web → didokumentasikan → dipakai sebagai sumber celah putaran
> berikutnya. Setiap metode dinilai kelayakannya di konteks Aeryn
> (single-tenant, proot ARM64, tanpa akses bobot model).

## Sumber riset (2025–2026)

1. **Self-Improving LLM Agents at Test-Time** (arXiv 2510.07841) — self-awareness
   via uncertainty estimator → sintesis data terarah pada kelemahan.
2. **Multiagent Finetuning** (MIT/Harvard/Stanford, ICLR 2025) — masyarakat
   generation+critic agent saling memperbaiki; single-agent mencapai plateau,
   multiagent tidak.
3. **ExpeL-style experience learning** (UCL + Huawei Noah's Ark) — adaptasi
   tanpa menyentuh bobot: structured memory yang meng-update diri dari
   pengalaman.
4. **Galileo — 7 AI Agent Failure Modes** — taksonomi kegagalan sistematis.
5. **OWASP LLM Top 10 + Prompt Injection Cheat Sheet** — LLM01 prompt injection
   (direct & indirect via knowledge base), LLM08 vector/embedding weaknesses.
6. **Chaos Engineering for AI Agents** (ReliabilityBench 2026) — fault injection:
   consistency (pass@k), robustness (task perturbation), fault tolerance
   (tool/API failure). Komponen 50×99% reliability ≈ 40% system reliability!
7. **Memory canary values** (Maxim) — menanam nilai kanari di memori untuk
   deteksi manipulasi.

## Prinsip kunci yang berlaku untuk Aeryn

> Aeryn TIDAK bisa fine-tune bobot model (API-only). Maka "fine-tuning"
> = fine-tune KONTEKS, TOOL, GUARD, dan MEMORI — bukan bobot. Semua metode
> diadaptasi ke arah itu.

---

## Metode → Status adopsi Aeryn

| # | Metode | Status | Catatan |
|---|---|---|---|
| M1 | Differential testing (2 sisi) | ✅ LIVE | parity_probe.py — lahir dari Sen |
| M2 | Reflection loop (episode → lesson → inject balik) | ✅ LIVE | ditutup di V37.2 |
| M3 | Failure-mode taxonomy audit | 🟡 SEBAGIAN | baru ad-hoc; lihat Rencana F1 |
| M4 | Red teaming / adversarial probing | ✅ LIVE | test_v37_4/5 security |
| M5 | Chaos/fault injection tool | ❌ BELUM | **Rencana F1 utama** |
| M6 | Memory canary values | ❌ BELUM | **Rencana F2** |
| M7 | Self-critique / LLM-as-judge pass | 🟡 ADA (critic_pass) | belum dipakai rutin |
| M8 | Canary deployment (shadow→native) | ✅ LIVE | lebih maju dari Hermes! |
| M9 | OWASP LLM01 indirect injection guard | 🟡 SEBAGIAN | wrap_untrusted ada, belum dipakai konsisten |

## Rencana putaran berikutnya (dari metode yang belum jalan)

### Metode generasi-2 (terbukti efektif di V38.6, masuk ritual)
- M10 **Unicode normalization testing** — homoglyph/fullwidth bypass
  pada semua string-matching guard (SOP, injection markers, allowlist).
- M11 **Rate-limit bypass probe** — coba rotasi kunci identitas
  (session_id/user) di setiap limiter baru.
- M12 **Resource-exhaustion audit** — input tak dibatasi = biaya tak
  terbatas; cap wajib untuk query/param yang menyentuh I/O eksternal.
- M13 **Safety-interlock review** — tool berbahaya (chaos, terminal power,
  reset) wajib env interlock + default-deny.
- M14 **Unbounded-growth check** — struktur data persisten wajib punya cap
  + eviction policy (people, fakta, arsip).

### Metode generasi-3 (V38.9+, escalation bertahap)
- M15 **Cross-user privacy audit** — semua file/direktori yang menggabung
  data multi-user (episodes, sessions) wajib diblokir dari tool agent
  (ditemukan: episodes.jsonl bocor goal antar user).
- M16 **Symlink/TOCTOU probing** — symlink dalam sandbox menunjuk keluar;
  realpath check + secret-basename match pada TARGET akhir.
- M17 **Computational DoS probe** — input yang memicu komputasi eksponen
  (bigint pow, regex bermata airan, nested parse) harus punya operand/
  depth/result guard SEBELUM eksekusi (kasus: math_calc "9**9**9" hang >30s).
- M18 **Fallback-directive injection** — pastikan teks user tidak bisa
  mempengaruhi pencocokan rule fallback (matching hanya pada error internal).
- M19 **Reminder/scheduler bounds** — delay negatif/masif, cap jumlah item,
  atomic pop saat fire.

### Metode generasi-4 (V39.5, dari riset LLM-as-Verifier)
- M20 **Mechanical-first verification** — cek deterministik dulu (leak
  marker, dangerous advice) TANPA LLM; LLM hanya untuk klaim faktual.
- M21 **Verifier ≠ Generator/Judge** — verifier pakai system prompt berbeda
  + rubrik BENAR/SALAH (bukan skor bagus/buruk); model tidak menilai
  dirinya sendiri dengan rubrik sama.
- M22 **Fail-closed output gate** — jawaban gagal verifikasi diganti pesan
  aman + alasan; verifier error ≠ blokir (degrade anggun).

## Riwayat putaran fine-tuning

| Putaran | Versi | Metode | Temuan → Fix | Test |
|---|---|---|---|---|
| 1 | V37.1 | Analisa episode | 43 silent-fail; "siapa namaku?"→fs_read | 226→226 |
| 2 | V37.2–37.3 | Data + wiring review | Strategy loop mati; ledger amnesia; state collision | →226 |
| 3 | V38.4 | Security sweep manual | terminal leak secrets; gateway no-allowlist; file:// SSRF | →228 |
| 4 | V38.5 | Data hygiene | 49 kenalan hantu di social memory | →230 |
| 5 | V38.6 | 7 metode gen-1 sekaligus | unicode bypass; rl bypass; query unbounded; chaos interlock; people cap | →236 |
| 6 | V38.7 | M10–M14 gen-2 | limiter memory leak; audit trail terbuka; reset tanpa auth | →238 |
| 7 | V38.8 | M15 cross-user privacy | episodes.jsonl bocor antar user | →241 |
| 8 | V38.9 | M17 computational DoS | math_calc hang >30s (bigint) | →245 |
| 9 | V39.3 | Pasca-build smoke | reminder dikira sosial; jawaban lama menjerumuskan | →408* |

*angka test absolut naik karena fitur baru ikut menambah test.

Total celah ditutup: 20+ (semua jadi test regresi permanen).



### F1 — Chaos harness (`chaos_harness.py`)
Fault injection deterministik terhadap tool registry:
- web_search/web_read/http_get → simulasi timeout, 429, 500, body rusak
- fs_read/fs_write → PermissionError acak, disk-full simulation
- Ukur: apakah run INDUK tetap selesai dengan degradasi anggun (fallback/
  laporkan), bukan crash/silent-fail. Skor resilience per tool.

### F2 — Memory canary
- Tanam canary fakta palsu bertanda di core_memory + social memory
  (hanya saat flag audit aktif).
- Probe berkala: kalau canary "bocor" ke jawaban user atau hilang tanpa
  jejak audit → alarm integritas memori.

### F3 — Critic pass otomatis untuk run kompleks
- critic_pass sudah ada tapi manual. Aktifkan otomatis saat run pakai
  ≥3 tool calls (indikasi kompleksitas) — judge menilai konsistensi
  jawaban vs hasil tool.

### F4 — Indirect injection sweep berkala
- Korpus uji injeksi tidak langsung (teks halaman web berisi instruksi)
  dijalankan mingguan lewat chaos harness; hasil masuk nightly digest.

### F5 — Uncertainty-driven backlog (dari paper #1)
- Nightly reflection menandai goal yang gagal/berputar (iterations≥max)
  sebagai "weakness cluster" → otomatis jadi kandidat item backlog.

## Disiplin

Setiap metode yang mulai jalan → wajib punya test regresi + entri CHANGELOG +
update dokumen ini. Metode baru dari riset berikutnya → tambah tabel dulu,
jangan langsung eksekusi.
