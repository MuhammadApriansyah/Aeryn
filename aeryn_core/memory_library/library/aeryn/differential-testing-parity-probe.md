---
id: differential-testing-parity-probe
topic: aeryn
tags: [aeryn,parity-probe,differential-testing,metodologi,testing]
signal: high
created: 2026-08-25
updated: 2026-08-25
summary: Metodologi parity probe: uji tool sama dari dua sisi (direct vs pipeline agen); divergensi = data perkembangan, provider-error = inconclusive.
---

# Differential Testing / Parity Probe

## Inti metodologi

Uji capability yang SAMA dari dua sisi:

1. **Direct layer** — fungsi/tool murni dipanggil langsung (tanpa agen).
2. **Pipeline layer** — permintaan setara dilewatkan lewat pipeline agen
   lengkap (routing klasifikasi → pemilihan tool → eksekusi → post-check).

Bandingkan hasilnya. Tiga verdict:

- **ALL PARITY** — kedua sisi sepakat. Pipeline menyalurkan maksud dengan
  benar sampai tool yang tepat.
- **DIVERGENSI** — direct benar tapi pipeline salah jalur/hasil. Ini bukan
  kegagalan proyek; ini **data perkembangan**: petanya di mana lapisan
  reasoning/pipeline masih bocor. Setiap divergensi = satu item kerja
  konkret (perbaiki prompt routing, enforcement di kode, dsb).
- **INCONCLUSIVE** — provider error (429/5xx, timeout, quota) di salah
  satu sisi. Jangan dicatat sebagai divergensi — noise infrastruktur bukan
  sinyal perilaku. Ulang run; hitung terpisah.

Disiplin verdict ini penting: kalau provider-error ikut dihitung divergensi,
streak parity jadi flaky dan sinyal asli tenggelam. Kalau divergensi dianggap
kegagalan, tim takut menjalankan probe dan probe berhenti jadi ritual.

## Kisah nyata #1 — flaky routing karena model kecil

Run pertama probe langsung membuktikan nilainya: perintah "ingat ini:"
kadang dirouting ke `memory_search` / `pitfall_search` / `web_search`
secara acak, padahal maksudnya memory-WRITE. Root cause: PM2 env hanya
punya GROQ_API_KEY (bukan NOUS) sehingga chain jatuh ke model kecil
(gpt-oss-20b) yang kerap mengabaikan instruksi prompt klasifikasi.

Pelajaran: divergensi menunjuk ke penyebab sistemik (env var hilang →
model fallback lemah), bukan ke bug tool mana pun. Fix-nya pun bukan
prompt tambahan tapi **enforcement di kode**: saat perintah ingat-ini,
tool lain ditolak dengan retry message — pola sama dengan single-call
guard. Setelah fix: 3x berturut ALL PARITY.

## Kisah nyata #2 — tabrakan fitur riwayat × memory-write

Dua fitur yang masing-masing sudah hijau bisa bertabrakan saat digabung:
riwayat multi-turn (V35) membuat konteks pesan lama ikut masuk, dan
memory-write lama sempat bereaksi pada konteks itu seolah perintah baru —
dua fitur bagus menghasilkan perilaku gabungan yang salah. Parity probe
(direct vs pipeline) yang menangkapnya, karena direct layer tidak punya
riwayat sehingga perbedaan jalur langsung terlihat.

Pelajaran: probe wajib dijalankan ulang setiap kali dua fitur pipeline
disatukan — test unit per-fitur tidak menjamin parity gabungan.

## Ritual

`parity_probe.py` jadi gerbang wajib tiap penambahan fitur Aeryn:
test unit green → probe ALL PARITY → smoke live E2E. Divergensi = bahan
perbaikan tercatat di tracker; inconclusive = ulang, jadi data.
