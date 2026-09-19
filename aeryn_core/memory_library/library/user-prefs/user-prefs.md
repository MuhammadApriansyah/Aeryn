---
id: user-prefs
topic: user-prefs
tags: [communication, concise, indonesian, proactive, credential, style, direct]
signal: high
created: 2026-08-24
updated: 2026-08-24
summary: Sen prefers concise Indonesian, proactive execution (no manual steps), verify before claim. Hates repeated credential requests & long explanations. Gave blanket authority to act independently.
---

## Communication
- Concise, direct, short messages. Frustrated by long explanations & repeated credential requests
- Proactive: SSH/execute directly, don't ask user to run commands manually
- Mixed Indonesian+English fine (no teen slang)
- FRUSTRATED if answer mixes English or tool-call narration is messy in chat ('apasih dibilangin bahasa indo', 'ngaco')
- WAJIB: answer consistent in Indonesian, clean format. Process/debug narration goes in step-label, not response body
- Don't ask repeated questions — Sen gave 'authority to do everything independently' (restart PM2, patch DB, refactor parser)
- Extremely short/terse OK; single emoji OK; 'Kenapa?' for diagnosis

## Verification standards
- Verify BEFORE claiming done — Playwright E2E via real browser, not just curl
- Sharp correction if spamming tool calls or claiming 'verified' without quality check
- Test first, show results
- Sub-agent audit: ALWAYS self-audit output (own E2E + screenshot) before reporting done

## Context reporting (WhatsApp only)
- Aeryn reports approximate context usage at end of every WhatsApp response
- Format: '📊 Perkiraan konteks terpakai: ...% , aman.'

## Session reset
- Sen chooses manual WhatsApp session reset via /new — does NOT want auto-reset (session_reset config)
- Don't offer auto-reset again ('jangan lah, sayang jir')

## Environment
- proot Ubuntu ARM64, no sudo, no systemd, no Docker
- Node.js, Fastify, SQLite, React, Playwright
- Prefers modular, framework-agnostic solutions
- Flexible multi-framework over rigid single-methodology
