# Aeryn Development Roadmap & Probabilitas

> Dibuat 2026-08-25 (V37). Dokumen strategi pengembangan berkelanjutan
> Aeryn-Core sebagai pasangan Hermes ("otak kanan" ↔ "otak kiri").
> Sumber data: empiris V33–V37 dalam satu hari kerja penuh.

---

## 1. Basis empiris

| Metrik | Nilai | Interpretasi |
|---|---|---|
| Velocity rilis | V33→V37 = 5 versi/hari (pola 4 sub-agen paralel) | Kapasitas build tinggi |
| Pertumbuhan test | 53 → 311 (+487%) | Kualitas terjaga saat iterasi cepat |
| Bug tersembunyi tertangkap | 4 besar: flaky routing (model kecil), tabrakan riwayat×memory-write, gateway broken sejak V33, amnesia antar-pesan | Sistem verifikasi (parity probe + smoke E2E) terbukti bekerja |
| Success rate runtime | 82,7% (255 run) | ±17% gagal, dominan error provider eksternal |

## 2. Probabilitas per milestone

| Milestone | Estimasi | Catatan |
|---|---|---|
| Aeryn stabil sebagai companion harian (Discord+WA lancar, konteks utuh) | 🟢 85–90% / 1 minggu | Fondasi ada; sisanya polish + observasi nightly |
| Success rate runtime ≥95% | 🟡 70% / 2 minggu | Error sisa dominan eksternal; perlu retry pintar + rotasi agresif |
| Self-improving loop (nightly → backlog → auto-fix issue kecil dengan guard) | 🟡 60% / 3–4 minggu | Refleksi sudah lapor; fase auto-fix butuh guard ketat anti-rusak-diri |
| Framework multi-tenant (penghuni kedua) | 🔴 15–20% / 30 hari | Platform engineering besar; belum ada konsumen → DITAHAN |
| Backflow diterima upstream Hermes resmi (repo publik) | 🟡 40–50% | Skill lokal sudah 100%; probabilistik hanya bagian kontribusi upstream |

## 3. Risk register

| Risiko | P | Mitigasi |
|---|---|---|
| Quota/rate limit provider | Tinggi | Chain 4-provider ✅, cap ask_hermes ✅, cache compaction ✅, health check ✅ |
| Bottleneck orkestrator (konteks sesi hilang) | Sedang | handoff.py + library ✅; disiplin komit wajib |
| RAM proot habis (host ~69%) | Sedang↑ | Daemon 45–112MB; arsip modul mati ✅; tolak fitur boros memori |
| Complexity tax (test makin mahal) | Pasti naik | Ritual parity + regression otomatis; full-suite ±13 detik masih murah |
| Drift saat Hermes update | Sedang | Parity tracker + refleks fail-soft + probe berkala |
| Over-engineering tanpa konsumen | Tinggi bila tanpa disiplin | Aturan Sen: "tidak membangun tanpa pemesan" |

## 4. Definisi "optimal" (target terukur)

1. **Reliabilitas** — success rate ≥95%, uptime PM2 ≥99%, zero silent-failure
   (semua error tampak di /metrics + nightly).
2. **Kontinuitas** — nol amnesia: riwayat, core memory, refleks lintas-otak
   aktif di setiap percakapan.
3. **Kolaborasi** — delegasi dua arah mulus, cap dihormati, nightly gabungan
   konsisten 7 malam berturut-turut.
4. **Kemandirian minimal** — Aeryn menangani masalah kelas-satu sendiri
   (restart, cache invalidation) dan MELAPOR, bukan diam.
5. **Testimen** — setiap fitur baru lolos ritual penuh (test + parity +
   smoke), tanpa kecuali.

> Bila 5 poin stabil ≥2 minggu → potensi maksimal utk skala saat ini
> tercapai. Lebih dari itu = diminishing returns; energi beralih ke
> PEMAKAIAN nyata, bukan pembangunan.

## 5. Protokol kerja berkelanjutan

- **Malam**: nightly reflection fire (03:00 WIB) → pagi jadi backlog
  prioritas otomatis (data-driven).
- **Tiap sesi kerja**: ambil 1–4 item backlog teratas → pola 4 sub-agen
  paralel → orkestrator integrasi → komit versi.
- **Mingguan**: audit arsip + review tracker + maksimal satu rilis besar.
- **Rem**: fitur baru wajib punya konsumen nyata ATAU menyambung ke
  poin definisi optimal §4.

## 6. Roadmap konkret 2 minggu (draft backlog)

### Minggu 1 — Reliabilitas & kontinuitas
- H1–H2: Analisa 17% error runtime dari episode JSONL → kategori penyebab →
  retry policy per-kategori (backoff pintar, bukan spam).
- H3: Nightly auto-backlog: refleksi menghasilkan daftar top-issue terurut
  otomatis di digest core memory.
- H4: Smoke harian otomatis (health-check ringan via cron daemon yang ada)
  → hasil masuk nightly.
- H5–H6: Discord live observation window: kumpulkan interaksi nyata, catat
  miss-case klasifikasi ke backlog.
- H7: Review minggu-1 vs definisi optimal §4; update dokumen ini.

### Minggu 2 — Kolaborasi & kemandirian
- H8–H9: Self-healing kelas-satu: restart PM2 sendiri saat health gagal 2×
  berturut (guard: maksimal 1×/jam, selalu lapor WA).
- H10: Retry pintar ask_hermes (timeout → tawarkan degradasi, bukan error mentah).
- H11: Kalibrasi nada via affect engine: mode kognitif dipakai memilih gaya
  jawaban knowledge-path (bukan hanya social).
- H12: Audit kompleksitas: waktu full-suite harus <60s; kalau lewat,
  pecah/pindahkan test lambat.
- H13–H14: Stabilitas 7-malam nightly gabungan; jika lolos → deklarasi
  "potensi maksimal skala ini" tercapai, freeze fitur, fokus pakai.

## 7. Kriteria penghentian (anti over-engineering)

Fitur development DIBEKUKAN sementara bila semua terpenuhi:
- [ ] 5 poin §4 hijau 14 hari berturut
- [ ] Tidak ada item backlog berlabel "konsumen nyata" tersisa
- [ ] Semua risiko §3 dalam mitigasi aktif

Setelah freeze: energi → pemakaian nyata, dokumentasi pengalaman,
dan evaluasi ulang bulanan.

---
*Pemilik dokumen: ox-alpha (orkestrator) atas mandat Sen.*
*Review: tiap akhir minggu kerja, atau saat arsitektur Hermes berubah.*
