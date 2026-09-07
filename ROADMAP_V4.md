# Aeryn — Rancangan Gabungan (Roadmap v4)

> Disusun: 2026-09-06
> Keputusan arsitektur: **neural embedding & komputasi berat pindah ke Termux murni
> (bukan proot)**, dihubungkan via SSH manual. Ini membuka Gap 2 & Gap 3 yang
> selama ini terblokir oleh proot (spawn/GPU/multi-worker).
>
> Roadmap ini **menyatukan**: (A) 3 item fix-nanti dari STRESS_REPORT, dan
> (B) dimensi baru dari Utopia (knowledge graph) + JiuwenSwarm (swarm/self-evolution).

---

## Topologi Baru

```
┌─────────────────────────────────────────────────────┐
│ TERMUX HOST (u0_a396, aarch64, port 8022 — sshd)    │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  PROOT LINUX (user: sen)  ← AERYN sekarang   │  │
│  │  Python + FastAPI + PM2 + SQLite + Rust engine│  │
│  │                                               │  │
│  │  HARD TO DO HERE (proot limit):               │  │
│  │   · multiprocessing.spawn (multi-worker)      │  │
│  │   · torch / sentence-transformers (hangs)     │  │
│  └───────────────────────────────────────────────┘  │
│           │  SSH (127.0.0.1:8022)                   │
│           ▼                                         │
│  ┌───────────────────────────────────────────────┐  │
│  │  TERMUX NATIVE (no proot)  ← komputasi berat │  │
│  │   · torch / sentence-transformers ✓           │  │
│  │   · multiprocessing.spawn ✓                   │  │
│  │   · uvicorn workers=N ✓                       │  │
│  │   · neural embedding (all-MiniLM) ✓           │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Bagian A — 3 item fix-nanti (sekarang bisa di Termux)

### A1. Neural embedding (Gap 2) — pindah ke Termux

**Masalah lama:** `sentence-transformers` hang di proot headless (import timeout 25s).

**Solusi:** jalankan embedding service **murni di Termux**, expose sebagai HTTP
endpoint kecil (FastAPI) yang dipanggil Aeryn (proot) via HTTP.

```
Termux native (port 8081):
  embedding_server.py  →  POST /embed {text} → {vector: [384]}
                         model: all-MiniLM-L6-v2 (80MB, CPU di Termux)

Aeryn (proot) — aeryn_core/memory/embedding.py:
  _SentenceEmbedder.embed() → HTTP POST ke http://127.0.0.1:8081/embed
  fallback: hash embedder (sudah ada) kalau service down
```

**Config** (`deploy/termux-embedding/`):
- `embedding_server.py` — FastAPI + SentenceTransformer, single endpoint
- `start.sh` — jalankan via Termux (python venv termux)

### A2. Multi-instance (Gap 3) — uvicorn workers di Termux

**Masalah lama:** `workers=N` gagal karena `multiprocessing.spawn` rusak di proot.

**Solusi:** `spawn` bekerja murni di Termux. Jalankan Aeryn API (atau minimal
worker pool yang berat) di Termux native dengan `workers=6`.

```
Termux native:
  uvicorn apps.api.routers.main:app --workers 6 --port 3010
  (state sharing PG sudah siap — sessions/tasks/approvals/traces semua PG-backed)
```

### A3. Streaming UI — tetap di proot (ringan, no compute)

Ini satu-satunya yang BUKAN masalah compute:
- `apps/web/static/js/chat.js` → arahkan ke `/v1/chat/stream` (SSE token-by-token)
- Render token real-time, bukan tunggu response penuh.

---

## Bagian B — Dimensi dari Utopia + JiuwenSwarm (ROADMAP v3, tapi sekarang ada compute home)

### B1. Bitemporal knowledge graph (Utopia)

Memory layer Aeryn → Postgres `facts(valid_from, valid_to, tx_from, tx_to, fact, source)`.
Neural embedding (A1) jadi backend vector untuk entity resolution & conflict detection.

### B2. Swarmflow + skill evolution (JiuwenSwarm)

Multi-agent & self-improvement. Komputasi evaluasi/optimasi skill bisa lari di
Termux (multi-worker) via A2.

### B3. Auto harness loop

Evaluation (Fase 6) + feedback → tune harness. Berat → Termux.

---

## Config SSH (dibutuhkan untuk semuanya)

Karena Aeryn (proot) harus memanggil Termux native secara stabil, siapkan
SSH key-based auth (sekali setup, tanpa password setiap call).

### `deploy/ssh/setup-termux-ssh.sh`

```bash
#!/bin/bash
# Setup SSH key-auth dari proot (sen) ke Termux host (u0_a396:8022)
# Jalankan SEKALI. Password host: 000 (isikan manual saat pertama).

TERMUX_USER="u0_a396"
TERMUX_PORT="8022"

# 1. Generate key kalau belum ada (id_ed25519 sudah ada di ~/.ssh)
if [ ! -f "$HOME/.ssh/id_ed25519" ]; then
  ssh-keygen -t ed25519 -N "" -f "$HOME/.ssh/id_ed25519"
fi

# 2. Salin public key ke Termux (butuh password sekali — isi 000)
echo "Salin key ke Termux (masukkan password 000 saat diminta):"
ssh -p "$TERMUX_PORT" "$TERMUX_USER@127.0.0.1" \
  'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys' < "$HOME/.ssh/id_ed25519.pub"

# 3. Verifikasi (harus tanpa password setelah ini)
ssh -p "$TERMUX_PORT" "$TERMUX_USER@127.0.0.1" 'echo SSH_KEY_AUTH_OK'
```

### `deploy/ssh/config` (letakkan di ~/.ssh/config)

```
Host termux
    HostName 127.0.0.1
    Port 8022
    User u0_a396
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
    ConnectTimeout 8
```

Setelah ini, cukup `ssh termux "..."` untuk eksekusi remote tanpa password.

---

## Prioritas Implementasi (baru)

| # | Item | Lingkungan | Effort |
|---|------|-----------|--------|
| 0 | **Setup SSH key-auth** (config di atas) | proot→Termux | 15 menit |
| 1 | **A1 Neural embedding server** di Termux | Termux native | 1-2 jam |
| 2 | **A3 Streaming UI** | proot | 1 jam |
| 3 | **A2 uvicorn workers=6** | Termux native | 30 menit |
| 4 | **B1 Bitemporal graph** | proot (PG) + Termux (vector) | 2-3 hari |
| 5 | **B2 Swarmflow + skill evolution** | campuran | 3-5 hari |
| 6 | **B3 Auto harness loop** | Termux | 2-3 hari |

---

## Catatan penting

- **Aeryn API tetap di proot** untuk HTTP/memory/logic; Termux hanya untuk
  **komputasi berat** (embedding, multi-worker evaluasi). Ini mempertahankan
  arsitektur hybrid tanpa migrasi total.
- **Neural embedding (A1)** adalah batu pijakan: membuka B1 (entity resolution
  embedding) dan meningkatkan RAG presisi yang selama ini pakai hash fallback.
- **SSH key-auth (item 0)** wajib dulu — tanpa itu, tidak ada cara stabil Aeryn
  memanggil Termux dari proot (password interaktif = tidak bisa diotomasi).

---

## Status item lama → status baru

| Item | Sebelumnya | Sekarang |
|------|-----------|----------|
| Neural embedding | ❌ terblokir proot | ✅ via Termux (A1) |
| Multi-instance | ❌ terblokir proot | ✅ via Termux workers (A2) |
| Streaming UI | ⚠️ belum | ✅ tetap di proot (A3) |
| Utopia (knowledge graph) | roadmap | ✅ compute ada (B1) |
| JiuwenSwarm (swarm/evolution) | roadmap | ✅ compute ada (B2-B3) |

---

## PROGRESS NYATA (verified pada environment)

1. **SSH key-auth proot→Termux** ✅ — `ssh termux` bekerja tanpa password.
   Termux native = `u0_a396`, `PREFIX=/data/data/com.termux/files/usr`, Python 3.14.6, aarch64.

2. **torch 2.11.0 terpasang di Termux native** ✅ — `torch.get_num_threads() = 8`.
   Ini membuktikan keputusan: torch/neural yang HANG di proot ternyata JALAN di Termux.

3. **numpy 2.4.4** sudah prebuilt via `pkg` (apt), tidak perlu build dari source.

4. **fastapi + uvicorn + sentence-transformers** — terpasang via kombinasi apt (prebuilt) + pip `--no-deps`.

### Status install neural di Termux native

| Komponen | Status |
|----------|--------|
| numpy 2.4.4 (prebuilt apt) | ✅ |
| python-torch 2.11.0 (prebuilt apt) | ✅ 8 threads |
| python-scipy 1.18.1 (prebuilt apt) | ✅ |
| python-tokenizers (prebuilt apt) | ✅ |
| fastapi 0.141.1 + uvicorn 0.52.4 | ✅ |
| sentence-transformers 6.0.1 | ✅ |
| transformers 5.16.1 | ✅ |

### Pitfall install Termux (ditemukan & diatasi)

Python 3.14 di Termux sangat baru → banyak wheel aarch64 belum ada, pip mencoba
**build dari source** yang gagal (numpy/scipy/scikit-learn butuh compiler fortran).
Solusi yang jalan:

1. **Install heavy binary dari `pkg`/apt** (prebuilt): `python-torch`, `python-scipy`,
   `python-tokenizers`, `python-numpy` — tidak build dari source.
2. **Install sisanya via pip `--no-deps`** supaya tidak menarik dependency yang
   akan dibangun dari source.
3. `tokenizers` dari pip menghasilkan `tokenizers.abi3.so` yang **ABI-mismatch**
   dengan Python 3.14 (`dlopen failed: PyBaseObject_Type`). Fix: pakai
   `python-tokenizers` dari apt (binary compatible).

### Pitfall #2 — DUAL PYTHON (akar "MISSING" berulang)

Simptom: `pip install X` sukses, tapi `python3 -c "import X"` selalu MISSING.

Akar: **`pip`/`pip3` menunjuk Python 3.11, sedangkan `python3` = 3.14.**
Semua `pip install` meng-install ke site-packages 3.11, tapi runtime `python3`
membaca 3.14 → tidak pernah ketemu.

**FIX WAJIB:** selalu pakai `pip3.14 install ...` ATAU `python3 -m pip install ...`
supaya interpreter & pip selaras (keduanya 3.14). Jangan pernah `pip` polos di
Termux ini.

Catatan tambahan:
- `python2.7` masih terinstall (sisa) — abaikan.
- `python3.11` masih ada (pip default menunjuk ke sini) — ini jebakan.

### Pitfall #3 — TUR repo & bentrokan Python (analisa menyeluruh)

**Struktur Python di tur (hasil `apt-cache policy`):**

| Paket | Versi tur | Versi stable/main |
|-------|-----------|------------------|
| `python` (meta) | 3.13.12-3 | 3.14.6-1 |
| `python3.13` | 3.13.13 | — |

**Paket ML tur (SEMUA compiled untuk Python 3.13):**
torch 2.11.0-2, numpy 2.4.4-1, scipy 1:1.18.1, tokenizers 0.23.2, onnxruntime 1.29.0
— semuanya `Depends: python` (=3.13 di tur), `.so` dibangun melawan libpython3.13.

**Bentrokan nyata (bukan spekulasi):**
1. `python3` = **3.14.6** (dari stable), tapi tur packages = **3.13** → ABI mismatch.
2. `pip` default → **3.11** (sisa), `python3` → **3.14** → pip install ke lokasi salah.
3. `tokenizers.abi3.so` dari pip = compiled utk Python 3.14 awal (rusak `PyBaseObject_Type`),
   sedangkan `python-tokenizers` (tur) = compiled utk 3.13 (menginstall ke 3.13 site-packages).

**Solusi yang TERBUKTI (bukan downgrade):**
Stack lengkap JUSTU sudah bisa di Python 3.14 via pip binary wheels:
- `sklearn 1.9.0`, `torch 2.11.0`, `numpy 2.5.3`, `scipy 1.15.2`, `pandas 3.0.5`,
  `polars`, `sentence-transformers 6.0.1`, `transformers 5.16.1`, `maturin 1.15.0`.
- Akar "import gagal" selama ini = **dependency `--no-deps` terlewat** (joblib,
  cloudpickle, narwhals, dsb). `pip install scikit-learn` (DENGAN deps) otomatis
  resolve semuanya → sklearn import OK.
- Satu-satunya yang butuh build dari source = **tokenizers** (Rust compile di Termux,
  `cargo`/`rustc` sudah tersedia), karena tidak ada wheel abi3 3.14 yang bersih.

**ATURAN FINAL (urutan & versi jelas):**
1. Pakai `python3 -m pip` (BUKAN `pip` polos) — pastikan interpreter = 3.14.
2. Binary berat yang tidak ada wheel aarch64 3.14 → `pkg install` (tetapi ingat: tur=3.13,
   jadi untuk 3.14 lebih baik pip binary wheel).
3. Kalau `import` gagal padahal `pip list` menunjuk ada → cek dependency terlewat,
   install pakai pip TANPA `--no-deps` (biar resolve otomatis).
4. Build-from-source (tokenizers) butuh Rust — sudah ada di Termux.

### Koreksi analisa (setelah eksekusi downgrade & revert)

**Kesimpulan terbukti di lapangan: TUR PACKAGES = Python 3.14, BUKAN 3.13.**

Saat downgrade ke 3.13 dicoba, `dpkg -L python-numpy` menunjukkan file di
`lib/python3.14/site-packages` — artinya tur/stable packages yang terinstall
sebenarnya compiled utk **3.14** (tur-continuous), bukan 3.13 (tur-packages).
`apt-cache policy python-numpy` konfirmasi: installed 2.4.4-1 dari termux-main,
bukan tur `1.23.0` (3.13 lama).

**Jadi downgrade ke 3.13 = LANGKAH KELIRU**, sudah di-revert kembali ke 3.14.
Koreksi pemahaman:

| Asumsi awal | Fakta |
|-------------|-------|
| tur = Python 3.13 | ❌ salah — tur/stable = Python 3.14 (file di lib/python3.14) |
| perlu downgrade | ❌ salah — 3.14 sudah benar |

**Status akhir (verified):**
- `numpy 2.4.4`, `torch 2.11`, `scipy 1.18.1`, `tokenizers 0.23.2` — import OK di 3.14.
- `sklearn 1.9.0` — import OK (binary wheel 3.14).
- **A1 embedding server MASHI JALAN** (`curl /health` → ok), vector 384-dim dihasilkan.
- Sisa masalah kecil: `scipy.spatial.transform` submodule error `_promote` saat
  import segar (campuran tur+pip scipy), TAPI `scipy.spatial.transform` TIDAK
  dipakai sentence-transformers/transformers → tidak memblokir embedding.