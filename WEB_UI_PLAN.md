# Aeryn — Rancangan Web UI (App Shell SPA + Advanced Polish)

> Disusun: 2026-09-07
> Status: RANCANGAN (belum implementasi)
> Keputusan: `aeryn-dashboard` (legacy) DIBUANG → `aeryn-api` jadi satu-satunya proses.
> Fondasi: vanilla JS + GSAP + Three.js + Alpine.js, **no build step**, FastAPI serve static.

---

## 1. Inventaris Aeryn (apa yang bisa di-expose via Web UI)

### 1.1 Tool bawaan (ToolRegistry — TIER_SAFE)

| Tool | Fungsi |
|------|--------|
| `web_search` | Cari web (discovery) |
| `web_read` | Ekstrak artikel bersih (fallback chain trafilatura→readability→html2text) |
| `http_get` | GET URL → status+body |
| `bash` | Eksekusi shell (guarded 4-layer) |
| `fs_read` | Baca file (sandbox) |
| `fs_write` | Tulis file (sandbox) |
| `file_read` / `file_write` / `file_search` | File tools tambahan |

### 1.2 5 Divisi Kognitif (Agent)

`division_1_creative` (POV/Style), `division_2_psych` (psikologi), `division_3_reasoning`
(MCTS/FOL/Critique/Graph), `division_4_gov` (governance), `division_5_infra`
(sync/validator). Routing otomatis di `AgentLoop`, terlihat di chat.

### 1.3 Domain Fitur (dari 28 router API, ~424 endpoint)

| Kategori | Router | Fungsi utama |
|----------|--------|-------------|
| **Chat & Agent** | chat, chat_agent, agents, advanced_router | chat, stream, async, division routing |
| **Memory** | memory (36 ep) | vault, hybrid search, semantic recall, graph memory, entity |
| **Tools & Engine** | tools, engine, platform_router | tool exec, FFI engine, plugin, MCP |
| **Reasoning** | reasoning (41 ep) | planner, reflection, constitutional AI, proactive |
| **Safety** | safety (21 ep) | guardrail, sandbox, approval, OWASP |
| **Multi-Agent** | orchestrator_router, phase4 | supervisor, handoff, blackboard, parallel |
| **Auth/Identity** | auth, auth_router | API key, SSO, rate limiter, email verify |
| **Evaluation** | eval_router | harness, benchmark, diagnostics |
| **Tracing/Telemetry** | tracing_router, distributed_tracing | OTel spans, trace tree |
| **Tasks/Runtime** | task_router, approval_router | background queue, HITL approval |
| **Admin/Billing** | admin (20), billing | usage meter, plans, secrets |
| **Workspace** | workspaces, workspace | sandbox, file mgmt |
| **Notifications** | notifications | push, webhook |
| **Dead code** | dead_code_router (54) | ⚠️ dipertimbangkan buang |

### 1.4 Plugin (7 terpasang)

`calculator`, `code-review`, `experience_transfer`, `messaging_gateway`,
`postgres_memory`, `research-assistant`, `aeryn-core`.

---

## 2. Arsitektur Web UI (App Shell)

### 2.1 Konsep inti

```
┌─────────────────────────────────────────────┐
│  APP SHELL (index.html, single page)        │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │ FLOATING NAVBAR (persistent)          │   │
│  │  [Chat] [Memory] [Tools] [Agents]     │   │
│  │  [Safety] [Trace] [Eval] [Plugins]    │   │
│  │  [Settings]                   [⚙][👤]  │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │ CONTENT AREA (ubah isi via modal /    │   │
│  │  section swap, BUKAN full reload)     │   │
│  │                                       │   │
│  │   ┌─────────────────────────────┐     │   │
│  │   │  MODAL (ukuran adaptif)      │     │   │
│  │   │  small/medium/large/full     │     │   │
│  │   └─────────────────────────────┘     │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### 2.2 Floating Navbar — Menu & Modal size

| Menu | Konten | Modal size |
|------|--------|-----------|
| **Chat** | percakapan agent (main view) | full (bukan modal, ini default) |
| **Memory** | vault, search, graph, entity | large |
| **Tools** | daftar+exec tool, plugin, MCP | large |
| **Agents** | 5 divisi + orchestrator + multi-agent | large |
| **Safety** | guardrail, approval queue, sandbox | medium-large |
| **Trace** | span/trace tree, telemetry | medium |
| **Eval** | benchmark, harness run, diagnostics | medium |
| **Plugins** | install/enable/disable plugin | medium |
| **Settings** | provider, model, API key, persona | small-medium |

### 2.3 Modal sizing (adaptif per menu)

```
small   (360px)   : quick status, satu setting, konfirmasi
medium  (560px)   : trace, eval, plugins, safety detail
large   (820px)   : memory, tools, agents (grid/table)
full    (95vw)    : hanya Chat (atau expand dari large)
```

Transisi modal: GSAP (scale+fade, spring), backdrop blur, fokus trap, ESC close.

---

## 3. Pustaka (Library) — Wajib

| Library | Peran | Sumber |
|---------|-------|--------|
| **GSAP** (+ ScrollTrigger) | animasi modal, navbar, micro-interaction | sudah ada `vendor/gsap.min.js` |
| **Three.js** | visualisasi graph memory / agent topology (3D) | sudah ada `vendor/three.min.js` |
| **Alpine.js** | interaktivitas declarative (show/hide, x-data) | CDN / vendor |
| **Chart.js** (opsional) | trace/eval metrics (line/bar) | CDN |
| **Marked / markdown-it** (opsional) | render markdown streaming | vendor |

**Aturan:** no build step. Semua via `vendor/` atau CDN. Jaga ES5-friendly (non-module)
di mana mungkin, tapi Alpine/GSAP boleh via IIFE global.

---

## 4. Polish Lanjutan (7 pilar — diterapkan di shell baru)

| Pilar | Implementasi di app shell |
|-------|---------------------------|
| **P1** Token streaming + cursor | ✅ sudah (chat.js), dipertahankan |
| **P2** Stable markdown render | markdown-it/marked + defer code block |
| **P3** Phase status | floating status bar ("thinking / reading web / running tool") |
| **P4** Tool call viz | tool card transparan (nama+args+status+expand result) |
| **P5** Stop/retry/edit | AbortController + regenerate + fork |
| **P6** Citations | inline citation + hover preview (memory source) |
| **P7** Accessibility | aria-live debounce, fokus trap modal, reduce-motion |

Ditambah polish khusus App Shell:
- **Floating navbar** GSAP (slide in, blur backdrop, active state).
- **Modal focus trap** + scroll lock + ESC.
- **Command palette** (⌘K) untuk loncat antar menu/tools.
- **Toast notification** untuk status tool/agent.
- **Dark theme** (sudah ada) + micro-motion.

---

## 5. Migrasi dari Dashboard Legacy

Langkah (setelah P2 selesai):

1. **Audit** fitur di `dashboard.js` (964 baris) + `dashboard.html` + `server.py`:
   mana yang masih hidup vs duplikat dengan router baru.
2. **Migrasi** fitur penting ke app shell (health monitor → status bar; task
   scheduler → Tasks modal; API key → Settings modal; memory search → Memory modal).
3. **Buang** `dashboard.html`/`dashboard.js`/`server.py` + hapus `aeryn-dashboard`
   dari `ecosystem.config.cjs`.
4. **Route** `aeryn-api` jadi entrypoint tunggal: `/` → app shell.

---

## 6. Struktur File Baru (rencana)

```
apps/web/
├── templates/
│   └── index.html          (app shell — navbar + modal container)
├── static/
│   ├── css/
│   │   ├── app.css         (shell + navbar + modal + status + toast)
│   │   └── chat.css        (dipertahankan, di-refactor sebagai section)
│   ├── js/
│   │   ├── app.js          (router navbar→modal, focus trap, command palette)
│   │   ├── chat.js         (dipertahankan, integrasi stream)
│   │   ├── memory.js       (vault/search/graph view)
│   │   ├── tools.js        (tool exec + plugin)
│   │   ├── safety.js       (approval + guardrail)
│   │   ├── trace.js        (trace tree + metrics)
│   │   ├── eval.js         (benchmark + harness)
│   │   └── modal.js        (GSAP modal manager, adaptive sizing)
│   └── vendor/             (gsap, three, alpine, chart, marked)
```

---

## 7. Prioritas Implementasi

| # | Tahap | Isi |
|---|-------|-----|
| 0 | Selesaikan P2-P7 polish saat ini | lanjut pilar polish |
| 1 | Audit dashboard legacy | petakan fitur hidup/mati |
| 2 | App shell + floating navbar + modal manager | GSAP + Alpine, modal adaptive |
| 3 | Migrasi section (memory, tools, safety, trace, eval) | satu per satu ke modal |
| 4 | Chat sebagai default view + integrasi stream P1 | chat.js refactor |
| 5 | Buang legacy + hapus aeryn-dashboard | cleanup |
| 6 | Command palette + toast + a11y final | polish akhir |

---

## 8. Catatan Keputusan

- **No build step** — FastAPI serve static `apps/web/`, no Vite/Node. Konsisten
  dengan Aeryn hybrid (Rust=perf, Python=logic, JS=shell ringan).
- **Modal ≠ iframe** — section di-render dalam DOM yang sama (bukan iframe), supaya
  shared state + GSAP bisa berinteraksi mulus.
- **Alpine.js** untuk show/hide + reactivity ringan; **GSAP** untuk animasi;
  **Three.js** khusus graph/topology visual. Tidak perlu framework full.
- **Chat tetap default** (full view), semua modul lain muncul sebagai modal di atas.