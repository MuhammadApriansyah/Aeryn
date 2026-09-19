---
id: webnovel-stack
topic: webnovel
tags: [webnovel, fastify, vite, react, sqlite, pm2]
signal: high
created: 2026-08-24
updated: 2026-08-24
summary: Webnovel platform = npm workspaces; apps/api Fastify v4+node:sqlite :3001, apps/web Vite+React :5173 proxy /api, both under PM2 ecosystem.config.js. Auth stdlib scrypt + sessions table. Core runs WITHOUT AI; AI optional author-side tool.
---

## Stack & constraints
- Root package.json workspaces: apps/api (Fastify v4.29.1 + node:sqlite, port :3001), apps/web (Vite+React :5173 proxying /api)
- PM2 ecosystem at ~/ecosystem.config.js
- Auth = stdlib scrypt + `sessions` table; NO external auth provider
- Sen INSISTS core platform runs fully without AI. AI is optional author-side tool only.

## API gotchas
- Fastify routes registered WITHOUT /api prefix (prefix comes from Vite proxy)
- JANGAN pin fastifyPlugin(fn,'5.0.0') → FST_ERR_PLUGIN_VERSION_MISMATCH, server won't listen but PM2 stays 'online'
- Import error in route file shows as 'Plugin did not start in time' (misleading) — debug with `node src/index.js` manually from apps/api
- 62 debug/test scripts now in scripts/debug/ (test_parser_real.mjs, e2e-v9.mjs, sync_titles.mjs)
- Mass chapter-title update via node:sqlite script with parameterized query — beware LIKE '%chapter-xl%' matches XLI-XLIX too; use exact match

## Parser (EPUB/PDF/DOCX)
- PDF: pdf-parse v2.4.5 API = new PDFParse({data}).getText() + destroy() (v1 default-function export gone)
- cleanPdfText(): strip '-- N of M --' page footers & reconstruct paragraphs (PDF line-breaks visual, not semantic)
- DOCX via mammoth preserves layout natively
- EPUB: Calibre merges multiple chapters per XHTML spine file ("A note for Miss Bennet. CHAPTER VII." inline in one paragraph)
- splitIntoChapters() MUST use non-anchor regex /(?:CHAPTER|chapter)\s+[IVXLCDM]+/gi — ^ anchor fails (9 vs 120 correct)
- Don't call splitIntoChapters on title+content recombined text (double-count)
- Post-split filter removes "index split XXX" dummy files
- EPUB title: <h2> Calibre contains sentence+CHAPTER → trim with /CHAPTER\s+([IVXLCDM]+)\.?$/i; <title>Unknown</title> must be ignored
