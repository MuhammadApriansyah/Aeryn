---
id: webnovel-ux-stack
topic: webnovel
tags: [webnovel, ui, ux, navbar, theme, modal, animation, playwright]
signal: high
created: 2026-08-24
updated: 2026-08-24
summary: Senior-level UI/UX standards. Dark mode required, instant theme toggle (NO View Transitions API). Modal via createPortal to document.body. Guest-first. Verify visual via Playwright E2E.
---

## Global UX standards (Sen is senior-level)
- Separate page per purpose (detail vs reader)
- Modal MUST createPortal to document.body (avoid stacking context bug — sticky navbar z-400 makes elements 'pierce')
- NO non-standard emoji for icons (⏻ = box on Android — use inline SVG)
- Motion 200-400ms; dark mode + prefers-reduced-motion REQUIRED
- Guest-first (login only for personal features); login must return to original context + preserve draft

## Theme transition pitfall (CRITICAL)
- JANGAN set zIndex on hero banner (stacking context traps dropdown)
- Global theme transition 120ms
- View Transitions API (startViewTransition) causes DELAY on mobile Chrome — snapshot layer repaints async, content text looks 'separated' from navbar
- SOLUTION: remove view transition + disable ALL transitions during switch (inline style transition:none for 2 frames) → instant simultaneous theme swap
- Animation fill-mode 'both' creates permanent compositor layer — use 'backwards'

## Navbar final+bugfix (Aug 2026)
- [wordmark 'Web Novel' | Search... center | bell | hamburger] all viewports
- Bug1: bell dropdown 300px right-anchored pokes 26px outside 360px viewport → portal document.body + position:fixed + clamp left ≥8px
- Bug2: handleLogout didn't reset mobileOpen → panel stuck after logout, fix setMobileOpen(false)
- Bug3: ThemeToggle still emoji ☀️🌙 → SVG feather sun/moon 16px stroke currentColor
- Checks: navfix-v31-check.mjs 19/19 + e2e-check.mjs stays 21/24 (C2/C3 obsolete by design)
- Gotcha v32: sticky navbar z-400 STILL pierces portal backdrop z-900 on Android WebView (not repro desktop) → fix: visibility:hidden .wn-nav-hideable when menu open + backdrop 1200/sheet 1250
- /author/stats didn't return author_id → other users' series leaked to WRITER panel; fix SELECT s.author_id + frontend filter
- Mobile drawer: 100dvh fallback after 100vh (dynamic Android toolbar)

## UI component patterns
- Asset upload/replace (e.g. cover) MUST go through modal preview + confirm, not apply on file-select
- Global navbar action buttons (+ Series) must work from ANY page — modal state in Router shell, not per-page listener
- Modal closable via Escape + backdrop click

## UI/UX stack
- cmdk (Ctrl+K CommandPalette), sonner (Toaster top-center), framer-motion, gsap, @dnd-kit/core
- Skills cloned to ~/.hermes/skills/: emil-design-eng, taste-skill, ui-ux-pro-max, web-design-guidelines, frontend-design, impeccable, baseline-ui + animation-vocabulary, find-animation-opportunities, fixing-motion-performance
- Principles: keyboard-action without animation, <300ms ease-out cubic-bezier(0.16,1,0.3,1), transform/opacity only, respect prefers-reduced-motion

## E2E
- Playwright Chromium: LD_LIBRARY_PATH=/tmp/nss-libs/extract/usr/lib/aarch64-linux-gnu
- e2e-check.mjs (21 checks); auth rate limit 10/min → wait ~65s between runs
- headless Chromium lacks emoji fonts (boxes = font issue, NOT bug)
- filechooser event does NOT work in proot headless — use setInputFiles() directly on locator
