# Aeryn — Motion, Transisi & Layout (Kunci Teknologi Web UI)

> Disusun: 2026-09-07
> Jenis: riset + spesifikasi implementasi (bukan kode)
> Sumber: CODERCOPS 2026, Alex Mayhew (spring physics), SmoothUI (motion),
>   adamarant (checklist), skillrepo/motion-patterns, LottieFiles motion-design,
>   FuseLab Creative, AI Plain English, The Skins Factory, NNGroup State of UX 2026.

---

## 1. Filosofi Inti

**"Animation is the physicality layer of UI"** — bukan dekorasi, tapi komunikasi:
- **Feedback** — tombol/aksi langsung merespons.
- **Continuity** — elemen baru tampak "berasal dari mana" (tidak re-parse layar).
- **Hierarchy** — sorot satu elemen yang baru berubah, lalu tenang.
- **Causality** — drag/klik "snap" → user lihat sistem merespons.

Untuk **agent UI**, motion punya peran ekstra: **visibilitas supervising** —
planning, tool-use, memory, confidence, recovery → semua butuh transisi yang
menunjukkan *proses* agent, bukan cuma hasil (FuseLab + AI Plain English).

---

## 2. Prinsip Fisika (Spring & Easing)

### 2.1 Damping ratio (ζ) — kunci "feel"

| ζ | Karakter | Pakai untuk |
|---|----------|-------------|
| **< 1** (underdamped / bouncy) | overshoot, main-main | playful, gesture, perhatian |
| **≈ 1** (critically damped) | smooth, settle | ✅ **modal, menu, dialog, page transition** (default UI) |
| **> 1** (overdamped) | sluggish | jarang — elemen berat |

**Rule:** untuk dashboard/agent UI, **naikkan damping** (ζ≈1) — terasa profesional.
Bounce ≤ 0.1 untuk interactive, hindari > 0.1 (distracting).

### 2.2 Spring vs Easing

| Jenis | Pakai untuk |
|-------|-------------|
| **Spring** (physics) | interactive: button, modal, tab, gesture |
| **Easing** | predictable timing: loading bar, progress, sequence |

### 2.3 Curves standard (3-4 saja, jangan inline)

```css
--ds-ease-enter:   cubic-bezier(0.0, 0.0, 0.2, 1);  /* ease-out: masuk */
--ds-ease-exit:    cubic-bezier(0.4, 0.0, 1.0, 1.0);  /* ease-in: keluar */
--ds-ease-standard:cubic-bezier(0.4, 0.0, 0.2, 1.0); /* antara 2 state */
--ds-ease-linear:  linear;                            /* spinner/progress */
```

- **ease-out** untuk elemen MASUK (mulai cepat, settle) → responsif.
- **ease-in** untuk elemen KELUAR (mulai lambat, cepat hilang) → user sudah putuskan.
- **ease-in-out** untuk pergerakan antar 2 state elemen sama.
- **linear** HANYA untuk indeterminate (spinner, loader).

---

## 3. Token Durasi (100ms–500ms)

| Tipe | Durasi | Contoh |
|------|--------|--------|
| **Micro-interaction** (hover/focus/toggle) | 100–200ms | hover, toggle, feedback tombol |
| **Component state** (modal open/drawer/dropdown) | 200–300ms | modal, drawer, dropdown |
| **Page/full transition** | 300–500ms | hanya bila bermakna |
| **> 500ms** | — | harus bisa dijustifikasi |

```css
--ds-duration-fast: 120ms;   /* hover/focus/toggle */
--ds-duration-base: 240ms;   /* modal/component */
--ds-duration-slow: 360ms;   /* page transition */
```

**Material 3 & Apple HIG** menetapkan: 200ms komponen, 300ms inter-screen. Rutin default 300ms untuk interactive.

---

## 4. Properti yang Boleh Dianimasikan (GPU-Composited)

### 4.1 HANYA 3 (dengan hati-hati filter)

```
✅ opacity
✅ transform  (translate, scale, rotate)
⚠️ filter     (dengan hati-hati)
```

Ini jalankan di **compositor thread** (bukan main thread) → 60fps aman.

### 4.2 DILARANG dianimasikan (trigger layout/reflow)

```
❌ width, height   → pakai transform: scale()
❌ top, left, right, bottom → pakai translateX/Y
❌ padding, margin
❌ font-size
```

Layout cost 6–14ms di device mid-range, kaskade ke semua child → **drop frame**.

---

## 5. FLIP & Layout Projection (kunci modal adaptif)

Animasi `width/height/top/left` mahal. Solusi **FLIP**:

1. **First** — catat posisi/ukuran awal.
2. **Last** — apply style final, ukur posisi/ukuran baru.
3. **Invert** — gunakan transform untuk balikkan ke posisi awal.
4. **Play** — animasikan transform ke identity (0).

Hasil: elemen *tampak* berubah ukuran, tapi sebenarnya pakai transform GPU.

**Untuk modal adaptif Aeryn** (small→medium→large→full): bukan animasi `width`,
tapi **layout projection** — ukur bounds baru, transform ke sana. Ini yang bikin
modal "tumbuh" mulus tanpa reflow.

**Velocity preservation (C¹ continuity):** saat user interrupt animasi mid-flight,
animasi baru mulai dari velocity sekarang (bukan 0) — tidak ada lompatan.

---

## 6. Modal (spesifikasi wajib)

Setiap modal Aeryn Wajib punya:
1. **Focus trap** — tab cycle dalam modal.
2. **Escape-key close**.
3. **Scroll lock** — body tidak scroll di belakang.
4. `role="dialog"` + `aria-modal="true"`.
5. **Interruptible** — bisa dibalik mid-entry (state drives animation, bukan sebaliknya).
6. Backdrop blur + opacity (bukan hanya scale).

**Exit/enter pairing:** selalu definisikan `enter` + `exit` bersamaan — animation
tanpa exit = incomplete.

---

## 7. Reduced Motion (WAJIB, bukan opsional)

WCAG 2.3.3 — motion yang dipicu interaksi harus bisa dinonaktifkan.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

**Plus JS guard** untuk motion berat (parallax, 3D scale besar):
```js
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
if (reduceMotion) { /* skip GSAP 3D, ganti fade sederhana */ }
```

**Klasifikasi:**
- Page transition → optional, harus hormati reduced motion.
- Loading spinner → essential, boleh tetap.
- Hover → optional, disable/reduce.
- Drag feedback → essential (fungsional), minimalkan.

---

## 8. Aplikasi di Aeryn (konkret)

### 8.1 Floating navbar (GSAP)
- Muncul: slide-down 300ms + fade, ease-out, ζ≈1.
- Active state: `layoutId`-style indicator (shared element) geser antar menu.
- Hover: 120ms scale 1.05 (token fast).

### 8.2 Modal adaptif (small/medium/large/full)
- Buka: FLIP/layout projection → scale+fade, spring ζ≈1, 240ms.
- Tutup: reverse dari frame sekarang (interruptible), ease-in 200ms.
- Backdrop: opacity 0→1, blur.
- Ukuran berubah (small→large): **layout projection**, bukan width animasi.

### 8.3 Tool call viz (feedback)
- Status running: skeleton/progress (linear).
- Selesai: reveal result (ease-out 240ms) — menunjukkan causality.

### 8.4 Command palette (⌘K)
- Buka 200ms, ζ≈1, focus trap + ESC.
- List item: stagger 0.05–0.10s (bukan >0.2).

### 8.5 Toast notification
- Masuk: slide+scale 240ms ease-out.
- Stack: keluar lama exit 200ms ease-in.
- Interruptible.

### 8.6 Three.js (graph/topology)
- Spoiler: rotasi kamera lembut (damping tinggi), bukan parallax liar.
- Gate di belakang reduced-motion.

---

## 9. Layout — Sistem (selain animasi)

Dari riset agentic UX (FuseLab + NNGroup State of UX 2026):

1. **Planning visibility** — plan/step agent tampak (bukan black box).
2. **Tool-use disclosure** — tool yang dipanggil + argumen terlihat.
3. **Memory surfacing** — memori yang dipakai untuk jawaban tampak.
4. **Confidence signaling** — confidence level untuk keputusan.
5. **Progressive disclosure** — beginner lihat ringkas, expert lihat detail.
6. **Progressive delegation** — approval history atur pace otonomi.
7. **Recovery routing** — kalau gagal, ada jalur override/undo.

**Layout structur Aeryn app shell:**
- **Left/float nav** = modul & tools (bukan tab atas tradisional).
- **Main canvas** = chat (default) atau konten modal.
- **Status rail** = agent status (thinking/working/idle) + phase (P3).
- **Confidence + source rail** = citation/confidence (P6).

---

## 10. Anti-Pattern (JANGAN dilakukan)

| Anti-pattern | Kenapa salah |
|--------------|--------------|
| Animate `width/height/top/left` | trigger layout, drop frame |
| Linear easing untuk UI | terasa mekanis |
| Parallax setiap scroll | vestibular trigger #1 |
| > 3 elemen animasi bersamaan | user tak tahu mana yang merespons |
| Spinner untuk aksi < 150ms | nambah latency, bukan reassurance |
| Cinematic reveal di first visit | gagal WCAG 2.3.3, "portfolio feel" |
| Curves beda-beda tiap komponen | produk terasa "off" tanpa sebab |
| Exit tanpa enter | animation incomplete |

---

## 11. Token Layer (yang harus dibangun)

```
:motion-duration-fast   120ms
:motion-duration-base   240ms
:motion-duration-slow   360ms
:motion-ease-enter      cubic-bezier(0,0,0.2,1)
:motion-ease-exit       cubic-bezier(0.4,0,1,1)
:motion-ease-standard   cubic-bezier(0.4,0,0.2,1)
:motion-spring-ui       spring ζ≈1, stiffness ~180, damping ~26
:motion-spring-snappy   spring stiff (hover/tap)
```

Semua nilai dari token, **bukan inline** (prinsip skillrepo/motion-patterns rule #8).

---

## 12. Sumber

1. CODERCOPS — "Web Animation 2026: GSAP/Framer/CSS decision tree".
2. Alex Mayhew — "Atmospheric Animations: Physics of Motion" (damping ratio, FLIP, velocity).
3. SmoothUI — "Motion tutorial 2026" (springs, layoutId, gestures, reduced motion).
4. adamarant — "Functional UI animation 2026 checklist" (duration/easing/GPU/reduced-motion).
5. skillrepo / affaan-m — "motion-patterns" (AnimatePresence rules, focus trap, stagger).
6. LottieFiles — "motion-design-skill" (Disney principles for agent UI, 1.5k stars).
7. FuseLab Creative — "Agent UX 2026" (planning visibility, delegation, recovery).
8. NNGroup State of UX 2026 + AI Plain English (transparency patterns).
9. The Skins Factory — "Agentic UX 5 patterns".