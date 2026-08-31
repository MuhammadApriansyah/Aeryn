# Analisis Fitur Dashboard Hermes + Rancangan Dashboard Aeryn V61.3

## 📚 Bagian 1: Analisis Fitur Dashboard Hermes

### 1.1 Desktop App Architecture (Electron)

**3 lapisan jelas:**
- **Electron** (owns machine): process lifecycle, native filesystem/git, install/update, capability bridge
- **Renderer** (owns experience): navigation, presentation, ephemeral interaction state  
- **Agent Backend** (owns work): sessions, tools, model calls, streaming

### 1.2 Komponen UI Utama (dari kode sumber)

| Komponen | Path | Deskripsi |
|----------|------|-----------|
| **HUD Shell** | `hud/hud-shell.tsx` | Overlay/Heads-up display dengan timing yang presisi (HUD_RECENT_HOLD=1100ms, HUD_REVEAL=110ms, HUD_FADE=180ms, HUD_DIM=270ms, HUD_COLLAPSE=120ms) |
| **Skills Panel** | `skills/index.tsx` | Kelola skills + toolsets dengan detail pane, list column, capability rows |
| **Context Usage** | `context-usage-panel.tsx` | Panel usage context (memory/token) |
| **Gateway Menu** | `gateway-menu-panel.tsx` | Pengelolaan gateway connection & profil |
| **Command Center** | `command-center/index.tsx` | Central hub — 4 sections: sessions, system, usage, maintenance |
| **Status Bar** | `statusbar-controls.tsx` | Status bar dengan items yang bisa dikonfigurasi (show/hide via context menu) |
| **Model Picker** | `model-picker-overlay.tsx` | Overlay pemilihan model |
| **Right Sidebar** | `right-sidebar/index.tsx` | File browser, review panel, terminal |

### 1.3 Command Center (4 Sections Deep)

**Sections:** `sessions`, `system`, `usage`, `maintenance`

| Section | Fitur |
|---------|-------|
| **Sessions** | List all sessions, pin/unpin, open, delete, export |
| **System** | Status (getStatus), logs (4 types: agent/errors/gateway/desktop, 4 levels) |
| **Usage** | Analytics (calls, input/output tokens, 7/30/90 day periods), charts |
| **Maintenance** | Update Hermes, restart gateway, action status |

### 1.4 Status Bar (Rich, Configurable)

| Fitur | Deskripsi |
|-------|-----------|
| **Item Groups** | Left items + right items |
| **Item Types** | action, link, menu, text, render (arbitrary React node) |
| **Visibility** | Context menu untuk show/hide items |
| **Icons** | Codicon icons, custom GlyphSpinner |
| **Tooltips** | Hover tooltips dengan keybind hints |
| **Keybind Integration** | Setiap item bisa bound ke keybind action |

### 1.5 Status Bar Items (dari use-statusbar-items.tsx)

| Item | Icon | Function |
|------|------|----------|
| **Connection Status** | Globe | Gateway connection state |
| **Active Session** | Hash | Session name, click → session picker |
| **Context Usage** | BarChart3 | Progress ring, click → context breakdown panel |
| **Busy State** | Loader2 | Spinning saat agent bekerja |
| **Turn Timer** | Clock | Durasi turn saat ini |
| **Active Agents** | Activity | Subagent count (total + failed) |
| **Gateway Updates** | AlertCircle/Download | Update status, click → update overlay |
| **Version Status** | Wrench | Version badge, click → maintenance |
| **Profile** | User | Profil aktif, click → profile switcher |
| **Workspace** | Folder | CWD path, click → project tree |
| **Cron/Cron Failed** | Bookmark | Cron job status |
| **Notifications** | MessageCircle | Notification count |
| **Terminal** | Terminal | Quick terminal access |
| **Command Center** | Command | Cmd+K palette |

### 1.6 Layout System

| Komponen | Deskripsi |
|----------|-----------|
| **Pane Shell** | Tree-based layout system, right sidebar panels |
| **Right Sidebar** | File browser, review panel, terminal (tabbed) |
| **Context Menu** | Right-click context menu per item |
| **Overlay System** | Stackable overlays (model picker, updates, command center) |
| **Routing** | React Router dengan enum-based routes |

### 1.7 Fitur Interaktif Lanjutan

| Fitur | Deskripsi |
|-------|-----------|
| **Drag & Drop** | Composer drag, file drag to chat |
| **Keyboard Navigation** | Full keyboard control, keybind hints |
| **Search & Filter** | Debounced search, filters (log levels, periods) |
| **Export** | Session export (JSON), log download |
| **Context Menu** | Rich context menus everywhere |
| **Tooltip System** | Comprehensive tooltip dengan keybind labels |
| **Confirmation Dialogs** | Archive skill confirm, delete session, dll |
| **Loading States** | Skeleton loaders, page loaders |

### 1.8 UX Philosophy (dari design guide)

- **Server truth is cached, not owned**: Renderer paint from cache, merge don't clobber
- **Be optimistic, then honest**: Direct manipulation paints immediately, roll back on failure
- **Cross everything as observable ladder**: Ordered candidate resolution
- **Compatibility without carrying past forever**: Fallback untuk older backend
- **Focus management**: Active focus, context usage, live state

---

## 🎨 Bagian 2: Rancangan Dashboard Aeryn V61.3

### Gap Analysis: Fitur Hermes vs Aeryn

| Fitur | Hermes | Aeryn V61.2 | Perlu ditambah? |
|-------|--------|-------------|-----------------|
| Status bar | ✅ 15+ items, configurable | ❌ | **Wajib** |
| Command palette | ✅ Cmd+K | ❌ | **Wajib** |
| Command center | ✅ 4 sections deep | ❌ | **Wajib** |
| Context usage | ✅ Progress ring + breakdown | ❌ | **Wajib** |
| Session list | ✅ Sessions panel | ❌ | **Wajib** |
| Export session | ✅ JSON export | ❌ | Perlu |
| Logs viewer | ✅ 4 log types + levels | ❌ | **Wajib** |
| Usage analytics | ✅ Charts (7/30/90d) | ❌ | **Wajib** |
| Maintenance | ✅ Update, restart | ❌ | Perlu |
| Profile switcher | ✅ | ✅ partial | Perlu |
| Model picker | ✅ | ❌ | Perlu |
| Right sidebar | ✅ File/review/terminal | ❌ | **Wajib** |
| Overlay system | ✅ Stackable | ❌ | Perlu |
| Context menu | ✅ Rich | ❌ | Perlu |
| Keyboard nav | ✅ Full | Partial | Perlu |

### Fitur Baru untuk Aeryn V61.3 (24 fitur)

#### Status & Navigation
1. **Enhanced status bar** (15+ configurable items)
2. **Command palette** (Ctrl+K, fuzzy search)
3. **Profile switcher** (dropdown)
4. **Model picker** (current model + alternatives)
5. **Sidebar navigation** (collapsible, icons)

#### Command Center (Deep Dashboard)
6. **Sessions tab** (list, pin, export, delete)
7. **System tab** (health, logs, gateway restart)
8. **Usage tab** (analytics charts, token usage)
9. **Maintenance tab** (update, backup, restart)

#### Observability
10. **Log viewer** (4 types × 4 levels, filterable)
11. **Trace explorer** (expandable, span breakdown)
12. **Context usage** (progress ring, breakdown panel)
13. **Performance charts** (memory over time, response latency)

#### Data Management
14. **Session list panel** (sidebar or modal)
15. **Memory/vault browser** (search + sync)
16. **Tool catalog** (grid, categories, discover)
17. **Division control** (cards, execute, stats)

#### Workflows
18. **Workflow builder** (timeline, step execution)
19. **Checkpoint approval** (modal with details)

#### Utility
20. **Export** (session, traces, memory)
21. **Keyboard shortcuts help** (modal reference)
22. **Theme settings** (dark/light/custom, persisted)
23. **Search/global** (Ctrl+K, fuzzy)
24. **Help/support** (tips, version, changelog)

---

## 🗺️ Layout Dashboard V61.3 (9 Section)

### 1. Header (Fixed, Dark theme)
```
┌─ 🖥️ Aeryn | Status Dot (green/red/pulse) | Env (proot/sqlite) ───────────────┐
│ Logo | Capabilities | Tools | Divisions | Workflows | Traces | Settings        │
│                                   [🔍 Ctrl+K]  [⚙️] [🌙]                        │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Hero Section
- Large gradient title + subtitle
- Hero badge: "Sistem Siap" (green dot)
- CTA: "Mulai Chat" | "Eksplor Fitur"
- Quick action buttons: "Buat Workflow" | "Eksport Sesi"

### 3. Live Stats Bar (8 cards horizontal scroll)
```
● Status | 💾 Memory | 🔢 Version | 📈 Uptime | 🔍 Traces | 🔧 Tools | 🧠 Divisions | ✅ Tasks
healthy  | 56.2 MB   | 61.3      | 0d 12h   | 42       | 7      | 5 (14 agen)  | 3
```

### 4. Capabilities Showcase (5 Cards → bisa di klik)
Grid 5 kartu, setiap kartu expandable untuk lihat detail API.

### 5. Command Center Widget (Mini)
Quick access: Sessions (recent 5), System status, Usage this week, Maintenance alerts.

### 6. Chat Area
- Full width, panjang (70vh)
- Message bubbles: user (right, blue), assistant (left, surface), system (center, muted)
- Tool call transparency: inline badge
- Division routing info
- Multi-line input, Shift+Enter untuk newline

### 7. Smart Panel (Collapsible)
- **Right sidebar**: Memory search, Tools, Recent traces
- **Bottom panel**: Logs tail (live), performance metrics
- **Command palette modal**: Ctrl+K

### 8. Footer
- Environment info (full)
- Keyboard shortcuts help
- "Built by Hermes, learned by Aeryn"

### 9. Floating Elements
- Action FAB: "+" for quick actions (new chat, run tool, create workflow)
- Toast notifications (bottom-right)
- Modal dialogs (center)

---

## 🔧 Fitur Detail V61.3

### Command Palette (Ctrl+K)
```
Input: [🔍 Ketik perintah...] 
────────────────────────────────
💬 Mulai chat baru
🔧 Jalankan tool: dashboard_builder
📋 Buat workflow baru
🧠 Divisi: reasoning
📁 Export sesi saat ini
🔍 Cari memori
⚙️  Pengaturan sistem
```

### Status Bar (15 items, configurable)
Di-bawah header, bisa show/hide items via right-click.

### Command Center (Click untuk buka full)
Full-page modal atau tab baru dengan 4 sections:

**Sessions Tab:**
| Session | Last Message | Tokens | Actions |
|---------|-------------|--------|---------|
| chat_001 | "buat dashboard..." | 3.2k | 📤 Export | 🗑️ |

**System Tab:**
```
Status: ✅ healthy | Memory: 56.2 MB | Version: 61.3
Logs: [Agent] [Errors] [Gateway] [Desktop]
Level: ALL | INFO | WARNING | ERROR
```

**Usage Tab:**
```
Minggu ini: 12.4k token
[chart showing 7-day usage]
Input: 8.2k | Output: 4.2k
```

**Maintenance Tab:**
```
Update: ✅ latest (61.3)
Backup: ✅ 2h ago
Gateway: ⏱️ restarting...
```

### Right Sidebar (Tabbed)
```
[Memory] [Tools] [Traces] [Logs]
┌────────────────────────────────┐
│ Memory Search                  │
│ 🔍 [search...]                 │
│ ────────────────────────────  │
│ Vault: 429 entries             │
│ Recent: "dashboard design"     │
│         "chat UX pattern"      │
└────────────────────────────────┘
```

---

## 📐 Responsive & Aksesibilitas

### Breakpoints
- **Desktop (1440px)**: Full layout, 3-column stats
- **Laptop (1024-1440)**: 2-column stats, collapsible sidebar
- **Tablet (768-1024)**: 1-column, hamburger menu
- **Mobile (≤768)**: Chat-focused, bottom input bar

### Aksesibilitas (WCAG 2.1 AA)
- `lang="id"` + `dir="ltr"`
- Skip links
- ARIA labels & landmarks
- Focus rings (2px solid accent)
- Keyboard navigation (TAB, arrow keys)
- Color contrast 4.5:1+
- Screen reader text untuk icons

---

## 🗣️ Pertanyaan untuk Sen (Final Approval)

1. **Command Center** — mau jadi modal full-screen, atau tab baru?
2. **Right sidebar** — fixed width (300px) atau collapsible?
3. **Status bar** — mau semua 15 item, atau hanya 5 essential?
4. **Log viewer** — real-time stream, atau manually refresh?
5. **Export format** — JSON saja, atau tambah PDF/text?
6. **Quick actions FAB** — perlu 4 actions atau lebih?

**Silakan beri keputusan, Sen — saya akan implementasikan V61.3 sesuai prioritas.**