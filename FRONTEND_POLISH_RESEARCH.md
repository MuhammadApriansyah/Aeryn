# Aeryn — Riset Advanced Frontend Polish (arah pengembangan)

> Disusun: 2026-09-06
> Jenis: riset (bukan implementasi) — menyiapkan arah polish frontend tingkat lanjut
> Sumber tervalidasi: Zylos Research, CallSphere, thefrontkit, AYDesign, Pamela Fox,
>   Markstream (simonhe), AI UX Playground, AYDesign "AI citation patterns 2026"

---

## Ringkasan Eksekutif

Frontend Aeryn sekarang (808 baris vanilla: chat.html 108 + chat.css 434 + chat.js 270)
sudah punya skeleton yang benar — SSE streaming, session, settings — tapi **belum
punya polish produksi** yang membedakan "chat demo" dari "produk AI yang dipercaya".

Riset lintas sumber menemukan **7 pilar polish** yang konsisten muncul di semua
produk AI terbaik 2026 (ChatGPT, Claude, Perplexity, Cursor, v0, Granola, Notion AI).

---

## 7 Pilar Polish (dari sumber, diurutkan dampak)

### P1. Token-by-token rendering + live cursor
**Masalah sekarang:** `chat.js` pakai `text.textContent = msg.content` — nempel teks
penuh sekali, cursor/token tidak muncul bertahap.
**Praktik 2026:** append token 1-2 per frame (requestAnimationFrame batch), render
cursor CSS animasi di ujung node streaming, hapus cursor hanya saat `[DONE]` (bukan
token terakhir). Pamela Fox: browser batch repaint → kirim NDJSON & parse di frontend
supaya word-by-word benar-benar terlihat.

### P2. Stable markdown render (tanpa layout jank)
**Masalah:** streaming markdown parsial bikin flicker (format belum lengkap).
**Praktik 2026:** render markdown di setiap update TAPI defer komponen mahal (code
block, table) sampai closing fence tiba. Markstream: `final=false` selama streaming,
parsing menunggu konten terlihat stabil, `typewriter` + `smoothStreaming` pacing.

### P3. Phase-based status (bukan spinner kosong)
**Masalah:** indikator "thinking..." generic (3 titik) → user takut gagal.
**Praktik 2026:** status spesifik per fase — "thinking", "mencari di web...",
"menjalankan tool bash...". Fase harus muncul **sebelum token pertama** (TTFT gap
200ms-3s = saat rentan ditinggal user).

### P4. Mid-stream tool call visualization
**Masalah:** `addToolCall`/`addToolResult` sudah ada, tapi ditampilkan polos (JSON
dump), bukan komponen transparan yang bisa diaudit.
**Praktik 2026:** tool call tampil inline sebagai "aktivitas" transparan — nama tool,
argumen ringkas, status (running/done), hasil yang bisa di-expand. Ini inti visibilitas
agentic (Zylos: "users can't trust a system they can't observe").

### P5. Interruptible stream (stop + retry + edit)
**Masalah:** tidak ada tombol stop/retry/regenerate.
**Praktik 2026:** tombol Stop menonjol selama streaming (hemat token, hormati user),
retry (regenerate prompt sama), edit & resubmit (fork percakapan). AbortController di
frontend.

### P6. Citations & trust (untuk Aeryn research-evidence)
**Masalah:** memory recall Aeryn punya source, tapi tidak ditampilkan.
**Praktik 2026:** inline numbered citation + hover preview; claim-level attribution
untuk domain high-stakes; confidence indicator (strong/mixed/weak/unsupported); "missing
source disclosure" (jujur saat klaim tak bersumber). Ini **sinkron sempurna** dengan
skill `research-evidence` yang baru dibuat — citation UI adalah frontend-nya.

### P7. Accessibility & edge cases
**Praktik 2026:** `aria-live="polite"` (bukan assertive — screen reader jangan dibanjiri
tiap token; debounce 2-3 detik), minimum height response container (hindari reflow),
fokus tetap di input saat streaming, keyboard navigasi, reduce-motion.

---

## Arsitektur target (untuk Aeryn)

```
apps/web/static/js/
├── chat.js             (UPGRADE) — token stream + cursor + stop/retry
├── markdown.js         (NEW)     — stable incremental markdown renderer
├── toolviz.js          (NEW)     — tool call card (status + expand)
├── citations.js        (NEW)     — inline citation + hover preview
└── a11y.js             (NEW)     — aria-live debounce + focus mgmt
```

Backend sudah siap: `/v1/chat/stream` (SSE), `/v1/chat/async` (poll), memory recall
punya `source`, guardrail punya approval. Frontend tinggal **konsumsi** yang sudah ada.

---

## Prioritas implementasi (urut dampak/effort)

| # | Pilar | Effort | Note |
|---|-------|--------|------|
| 1 | P1 token streaming + cursor | 1-2 jam | paling terasa, paling murah |
| 2 | P3 phase status (+ stop P5) | 1 jam | trust + hemat token |
| 3 | P5 stop/retry/edit | 1-2 jam | interaktivitas inti |
| 4 | P4 tool call viz | 2-3 jam | visibilitas agentic |
| 5 | P2 markdown render | 2-4 jam | butuh library ringan |
| 6 | P6 citations | 2-3 jam | butuh memory source plumb |
| 7 | P7 a11y | 1-2 jam | polish final |

---

## Catatan keputusan

- **Vanilla JS (ES5 IIFE) dipertahankan** sesuai konvensi AGENTS.md — tidak pindah
  React/Vue kecuali ada alasan kuat. 7 pilar ini semua bisa di-vanilla.
- **Markdown render**: pertimbangkan `marked` (ringan, ~40KB) via vendor/, atau tulis
  renderer incremental minimal. Jangan tarik React + react-markdown (over-kill).
- **Citations backend**: memory `search_dense`/`search_vault` sudah return `source` —
  tinggal kirim source di respons chat, tampilkan inline.
- **Ini riset, bukan implementasi** — menunggu keputusan kamu untuk mulai eksekusi,
  dan sebaiknya **setelah** backend embedding Termux (Backlog prioritas lain) stabil.

---

## Sumber (tervalidasi, untuk audit)

1. Zylos Research — "Agentic UX: Frontend Design Patterns for AI Agents in 2026"
   (protokol AG-UI/A2UI, visibility, HITL, tool streaming).
2. Pamela Fox — "Best practices for OpenAI Chat apps: Streaming UI" (NDJSON + word-by-word).
3. AYDesign — "AI streaming response UI design patterns for 2026" (7 streaming patterns).
4. AYDesign — "AI citation and source UI design patterns for 2026" (7 citation patterns,
   scoring matrix Visibility+Trust/Effort).
5. CallSphere — "Designing Chat UIs That Match LLM Capabilities" (status indicators,
   stop, retry, specific status text > generic thinking).
6. thefrontkit — "AI Chat UI Best Practices for 2026" (streaming edge cases, citations,
   feedback capture, a11y).
7. Markstream (simonhe) — "AI chat streaming Markdown" (stable markdown, typewriter,
   smoothStreaming pacing, final flag).
8. AI UX Playground — "Citations · Trust AI UX Pattern" (trust scaffolding, progressive depth).