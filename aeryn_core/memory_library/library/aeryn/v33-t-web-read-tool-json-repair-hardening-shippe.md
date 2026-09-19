---
id: v33-t-web-read-tool-json-repair-hardening-shippe
topic: aeryn
tags: [aeryn,v33,web-read,trafilatura,json-repair,research]
signal: high
created: 2026-08-25
updated: 2026-08-25
summary: v33-T: web_read tool + json_repair hardening shipped
---

# v33-T: web_read tool + json_repair hardening shipped

GitHub research executed (trafilatura/json_repair feasible; llm-sandbox skip karena no-Docker di proot; MCP SDK ditunda). SHIPPED: (1) web_read(url) via trafilatura - clean article extraction with title/author, tier safe read-only auto-promote registered+checker. Completes research loop: web_search -> web_read -> answer. (2) json_repair pada jalur parse argumen tool-call di daemon - broken LLM JSON args no longer crash whole run; unfixable -> clear retry message ke model. Live E2E: 'cari tahu apa itu react' -> tools [web_search, web_read] -> accurate answer from source. Tests 206->213 green. Deps venv baru: trafilatura + json-repair (ARM64 proot verified). Commit V33-T.
