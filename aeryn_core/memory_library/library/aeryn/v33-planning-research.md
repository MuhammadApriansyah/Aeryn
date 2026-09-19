---
id: v33-planning-research
topic: aeryn
tags: [aeryn, v32, v33, planning, social-detection, model-leak, sanitizer, research]
signal: high
created: 2026-08-25
updated: 2026-08-25
summary: Riset penuh 4 isu sisa V32 + rencana perbaikan V33 (3 fase, acceptance criteria tertulis, urutan prioritas berbasis dampak). Siap eksekusi setelah approve Sen.
---

# V33 Planning & Research — Perbaikan Sisa V32

## METODOLOGI RISET
Semua temuan dari baca source langsung (bukan memory): `aeryn_daemon.py`
(569 lines), `model_client.py` (171), `social_generator.py` (~215),
`dynamic_schema.py` (88), `planner.py` (137), plus diff git sub-agen dan
test suite V32 (53 passed).

---

## ISSUE #1 — False-positive social detection (PRIORITAS 1)

### Bukti riset
- `_is_social_query()` daemon: contains-match "kamu"/"aku" (<60 char) →
  *"kamu pake library apa buat embedding?"* = SOCIAL ❌ (padahal teknis)
- Lebih parah di `social_generator.py::_is_social_query`: prefix list
  termasuk **"apa", "bagaimana", "kenapa", "bisa", "kalo"** DAN rule
  `<40 char tanpa tech indicator = otomatis social` → hampir semua
  pertanyaan knowledge pendek masuk jalur sosial.
- Test suite TIDAK punya negative-case test (tidak ada assert _is_social
  == False untuk pertanyaan teknis).

### Root cause
Heuristic berbasis blacklist kata teknis terbatas; tidak ada whitelist
sinyal TEKNIS positif. "Apa/kenapa/bagaimana" adalah awalan netral — bisa
sosial bisa knowledge.

### Fix design (V33-F1)
1. Tambah **TECH_POSITIVE signals** dicek SEBELUM social match: noun
   teknis umum (library, framework, API, database, embedding, server,
   kode, fungsi, error message, install, cara kerja, bedanya, kenapa X
   error, dst).
2. Pertanyaan berbentuk "apa itu X" / "apa bedanya X dan Y" / "gimana
   cara Y" → KNOWLEDGE, bukan sosial.
3. Social butuh minimal SATU sinyal relasional: kata ganti orang
   (kamu/aku/kitа) ATAU greeting ATAU ada di KNOWN_RESPONSES.
4. Hapus rule "<40 char auto-social" — diganti cek KNOWN_RESPONSES +
   relational pronoun.
5. Tambah NEGATIVE-CASE tests: ±10 pertanyaan teknis yang HARUS lolos ke
   tool path.

### Acceptance criteria
- [ ] "apa itu react?" → bukan social
- [ ] "kamu pake library apa?" → bukan social
- [ ] "gimana cara kerja HNSW?" → bukan social
- [ ] 18 test sosial lama tetap 100% pass
- [ ] Zero tool-call pada 18 query sosial lama

---

## ISSUE #2 — Sanitizer over-aggressive (PRIORITAS 2)

### Bukti riset
`_sanitize_social_answer()`: internal_kw = ['error', 'exception', 'API',
'database', 'server', 'sistem', 'null', 'none', ...]. Jawaban natural yg
kebetulan nyebut kata itu → SELURUH jawaban dibuang, diganti canned.
Plus `re.sub(r'\{[^{}]*\}', '')` menghapus SEMUA kurung kurawal.

### Fix design (V33-F2)
1. Internal-kw check hanya jika jawaban TERLIHAT seperti output mesin:
   ada JSON remnant / backtick code block / key:value pattern.
2. Kata 'error/sistem' dalam kalimat natural ("aku juga pernah error
   waktu belajar") TIDAK memicu fallback.
3. Strip `{...}` hanya jika konten mengandung `"name"`/"arguments"/
   "function" (tool call shape), bukan semua braces.

### Acceptance criteria
- [ ] "Maaf, kemarin sistemku lagi ngambek~" TIDAK difallback
- [ ] JSON tool_call murni TETAP difallback
- [ ] Semua 18 test sosial tetap pass

---

## ISSUE #3 — MODEL global leak (PRIORITAS 3)

### Bukti riset
```python
global MODEL
if MODEL is None or req.model or req.provider:
    MODEL = ModelClient(provider=req.provider, model=req.model)
```
Request A dengan model="gemini" → global MODEL jadi Gemini → request B
(tanpa param) ikut Gemini. State leakage antar request/user.

### Fix design (V33-F3)
ModelClient cache per-(provider,model)-tuple:
```python
_CLIENTS: dict[tuple, ModelClient] = {}
def _get_client(provider, model):
    key = (provider or "", model or "")
    return _CLIENTS.setdefault(key, ModelClient(provider, model))
```
Default request selalu dapat client default; request spesifik dapat
client-nya sendiri. Thread-safe via existing session locks.

### Acceptance criteria
- [ ] Request default setelah request gemini-specific tetap pakai chain NOUS
- [ ] Test unit: dua client beda param → instance beda

---

## ISSUE #4 — Batas 60-char & contains-match (DIGABUNG KE F1)
Batas arbitrer + contains luas sudah tercakup desain F1 (sinyal relasional
wajib). Tidak diperlukan fix terpisah.

---

## URUTAN EKSEKUSI V33
| Fase | Isi | Estimasi |
|------|-----|----------|
| 1 | F1 deteksi + negative-case tests | ~45 mnt |
| 2 | F2 sanitizer + tests | ~20 mnt |
| 3 | F3 client cache + test | ~15 mnt |
| 4 | Full regression (53+ test baru) + live smoke test daemon | ~15 mnt |

Total ~95 menit. Setiap fase komit terpisah, rollback mudah.

## PRINSIP
- Tidak menyentuh persona file, social.json, data user
- Tidak mengubah endpoint/API contract
- Semua perubahan backward-compatible dengan Discord gateway
