# Aeryn — Arah Perkembangan Selanjutnya (Roadmap v2)

> Disusun: 2026-09-04
> Status saat ini: Fase 1-8 selesai, 765 test passing, CI/CD hijau.
> Gap tersisa: 3 hal yang memisahkan "framework utuh" dari "sistem siap beban nyata".

---

## Ringkasan Posisi

Aeryn sudah **menyeberang titik kritis** — dari "agent core yang jalan" menjadi
framework yang memenuhi **7 dari 8 production requirements** (riset AWS/Azure playbook).
Yang tersisa adalah **kedewasaan di bawah beban**, bukan kekurangan arsitektur.

Tiga gap tersisa, diurutkan berdasarkan dampak:

| # | Gap | Dampak | Urutan |
|---|-----|--------|--------|
| 1 | Chaos/Stress Test | Cari titik patah sebelum user menemukannya | ⬆️ Pertama |
| 2 | Dense Embedding (RAG) | Naikkan kualitas memory recall (presisi) | Kedua |
| 3 | Multi-instance Scalability | Produksi 10k user/day | Ketiga |

---

# GAP 1 — Chaos & Stress Testing

**Tujuan:** Temukan titik patah Aeryn di luar happy path, sebelum user menemukannya.

**Kenapa duluan:** Semua test sekarang = happy path. Riset (Zylos, MAESTRO) tegas:
agent failure mode yang berbahaya muncul hanya di bawah beban/adversarial load.
Lebih murah ketemu sekarang daripada di produksi.

## Alur Spesifik

### 1.1 Load Test (Concurrency)
```
Input: N request paralel ke /v1/chat (N = 10, 50, 100, 500)
Ukur:
  - throughput (req/detik)
  - latency P50/P95/P99
  - error rate (5xx, timeout)
  - memory usage (apakah naik linear atau bocor?)
  - token cost per request (bom biaya?)

Perintah:
  - lokust/artillery/script custom async (asyncio + aiohttp)
  - pantau via /health (memory_mb) + /v1/traces (token total)

Titik patah yang dicari:
  - SQLite lock contention (banyak write paralel)
  - asyncio event loop block (urllib sync di thread executor)
  - LLM provider rate-limit → fallback chain kehabisan
  - memory leak di session store / trace collector
```

### 1.2 Chaos Test (Fault Injection)
```
Skenario:
  A. Tool crash berulang → apakah error recovery (retry+fallback) bekerja?
  B. LLM provider down → fallback chain jalan ke provider berikutnya?
  C. Disk penuh → task queue / session store graceful fail?
  D. Prompt injection canggih → guardrail 4 lapis tangkap semua?
  E. Context overflow → token budget enforced, tidak OOM?
  F. Concurrency race → dua user edit session sama → isolated?

Injeksi:
  - Monkeypatch tool handler untuk throw exception
  - Kill koneksi LLM di tengah stream
  - Kirim payload raksasa (100k+ token)
  - Kirim payload adversarial (injection, traversal)
```

### 1.3 Battery of Edge Cases
```
  - Empty input, whitespace-only, non-ASCII, emoji-only
  - Session ID collision antar user
  - Task queue dengan 1000 pending task
  - Approval request yang tidak pernah di-decide (stuck pending)
  - Trace spans 10k+ dalam satu trace (query lambat?)
```

### 1.4 Deliverable
```
File: tests/chaos/ + tests/load/
  - load_test.py          (script async concurrency)
  - chaos_test.py         (fault injection scenarios)
  - edge_cases_test.py    (battery)
  - STRESS_REPORT.md      (hasil + titik patah + rekomendasi fix)

Acceptance: semua titik patah tercatat, yang kritis difix.
```

---

# GAP 2 — Dense Embedding untuk RAG

**Tujuan:** Ganti recall keyword/TF-IDF dengan dense vector similarity → presisi memori naik.

**Kenapa:** Sekarang `recall.py` pakai keyword matching + `semantic_recall.py` pakai TF-IDF.
Ini works tapi tidak menangkap *makna semantik*. Query "cara bikin website" tidak akan
match memori yang berisi "buat situs" walaupun maknanya sama.

## Alur Spesifik

### 2.1 Pilih Embedding Backend
```
Opsi (dari ringan → berat):
  1. Rust engine (sudah ada cosine_similarity di C API) → embedding di Python
  2. sentence-transformers (sudah di venv, model lokal) → all-MiniLM-L6-v2
  3. API embedding (OpenAI/Cohere) → butuh kunci, latency tinggi

Rekomendasi: sentence-transformers (all-MiniLM, 384-dim, ~80MB),
sesuai dimensi yang sudah di-hardcode di divisi creative (dimension=384).
```

### 2.2 Embedding Store
```
Bangun di atas VectorStore yang sudah ada (Rust cosine_similarity):
  - EmbeddingIndex: simpan {id, vector, content} di SQLite
  - embed(text) → Vec<f32>
  - search(query, k) → top-k via cosine (pakai Rust C API)

Integrasi ke memory:
  - recall.py: search_semantic() dipanggil sebelum keyword search
  - gabungkan hasil dense + sparse (hybrid), ranking berdasarkan score
```

### 2.3 Index & Caching
```
  - Saat memory ditulis (write.py), auto-embed + index
  - Cache embedding di disk (hindari re-embed teks yang sama)
  - Batasi jumlah memori ter-index (misal 10k) → evict LRU
```

### 2.4 Evaluasi Kualitas
```
  - Bandingkan recall keyword vs dense pada 100 query benchmark
  - Metrik: hit rate@5, MRR (mean reciprocal rank)
  - Pakai harness evaluasi yang sudah ada (Fase 6)
```

### 2.5 Deliverable
```
File: aeryn_core/memory/embedding.py
  - EmbeddingIndex class
  - embed() + search() + hybrid_search()
  - Terintegrasi ke recall.py

Acceptance: recall dense mengalahkan keyword pada benchmark (hit rate naik).

Catatan: di proot/HEADLESS tanpa GPU, model MiniLM kecil masih bisa jalan CPU.
Kalau terlalu berat, fallback ke Rust hash-based simhash (lebih murah).
```

---

# GAP 3 — Multi-Instance Scalability

**Tujuan:** Dukungan >1 instance untuk 10k user/day, tanpa kehilangan state.

**Kenapa:** Sekarang single-node di PM2. Riset tegas: "stateless HTTP scaling
doesn't work for stateful long-running agents."

## Alur Spesifik

### 3.1 Pecah State vs Compute
```
Identifikasi state yang harus shared:
  - Session store (sessions.db) → pindah ke Postgres (sudah ada adapter)
  - Task queue (tasks.db)     → pindah ke Postgres (adapter ada)
  - Approval store               → Postgres
  - Trace collector              → Postgres (volume besar, tapi async)

Compute yang boleh per-instance:
  - Agent loop, LLM client, tool execution (stateless per-request)
  - Memory recall (pake index lokal per instance, atau shared Read replica)
```

### 3.2 Sesi Multi-Instance
```
  - PM2 cluster mode (`instances: max`) untuk aeryn-api
  - Session store pindah ke Postgres → semua instance lihat state sama
  - Cek: session yang dibuat di instance A bisa dibaca dari instance B
```

### 3.3 Load Balancer
```
  - nginx / PM2 built-in load balancing
  - Health check per instance
  - Sticky session OPSIONAL (kalau memory recall pakai index lokal)
```

### 3.4 Deliverable
```
File:
  - ecosystem.config.cjs (instances: max)
  - nginx.conf (reverse proxy)
  - migrations (SQLite → Postgres untuk sessions/tasks/approvals/traces)

Acceptance: 2 instance jalan, session ter-create di A bisa dibaca di B,
tidak ada data race pada task queue.
```

---

## Dependensi Antar Gap

```
Gap 1 (Chaos test) ── bersifat independen, bisa mulai kapan saja
                        │
                        ▼ (temuan bottleneck SQLite → motivasi Gap 3)
Gap 2 (Dense RAG)   ── independen dari yang lain
                        │
                        ▼ (index embedding → bisa perlu shared state → terkait Gap 3)
Gap 3 (Scale)       ── butuh hasil Gap 1 untuk tahu bottleneck yang harus di-scale

Rekomendasi urutan: Gap 1 → (fix temuan) → Gap 2 → Gap 3.
```

---

## Prinsip yang Tidak Boleh Dilanggar (dari riset)

1. **No test double** — semua test chaos/load = beban nyata, bukan mock.
2. **The tool is the gate** — setiap perubahan tetap lewat guardrail engine.
3. **Token cost = functional signal** — stress test wajib measure token/cost.
4. **Evaluation ≠ tracing** — kualitas embedding diukur terpisah (harness Fase 6).
5. **Dokumentasi tiap selesai gap** — tidak menumpuk sampai akhir.

---

## Ringkasan Eksekusi (Estimasi)

| Gap | Effort | Deliverable utama |
|-----|--------|-------------------|
| 1 | 3-5 hari | STRESS_REPORT + fix kritis |
| 2 | 3-5 hari | EmbeddingIndex + hit rate naik |
| 3 | 1-2 minggu | Postgres migration + cluster + nginx |

---

> **Status target selesai Gap 1-3:** Aeryn = production-ready (bukan cuma
> framework utuh, tapi teruji beban + RAG presisi + scalable).