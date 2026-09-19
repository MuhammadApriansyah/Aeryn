---
id: aeryn-v32-final-study-social-generator-hybrid-no
topic: aeryn
tags: [aeryn,v32,social-generator,nous,discord-gateway]
signal: high
created: 2026-08-25
updated: 2026-08-25
summary: aeryn v32 final study: social generator hybrid + nous primary + discord gateway split
---

# aeryn v32 final study: social generator hybrid + nous primary + discord gateway split

V32 complete: (1) social_generator.py hybrid - deterministic KNOWN_RESPONSES untuk short queries (zero LLM), LLM fallback complex; (2) model_client provider chain rombak: NOUS stealth/ox-alpha primary -> Gemini 2.5 pro -> OpenRouter/Groq, OPENROUTER key mapped ke NOUS; (3) discord_gateway.py TERPISAH dari hermes gateway, mention/DM -> POST :3010/agent/run; (4) test_v32_social 53 passed/2s. SISA MASALAH: 'apa' prefix + contains kamu/aku masih nangkep knowledge question ('kamu pake library apa buat embedding?' -> salah jalur social); sanitizer internal_kw terlalu agresif; MODEL global leak belum difix.
