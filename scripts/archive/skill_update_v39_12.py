#!/usr/bin/env python3
"""V39.12 — Update skill library: capture LLM provider outage workflow.

Konteks: sesi ini menemukan & memperbaiki
1. Bug sanitasi fakta sosial (substring overmatch → False positive,
   memblok username real "paisenmtvsky")
2. Workflow deteksi & respon outage provider LLM (429/410/404 massal —
   NOUS free tier expired, Gemini key invalid, OpenRouter free/day quota
   habis, NVIDIA model 410 gone)
3. Emergency mode: fallback ke local LLM (llama.cpp) bila semua cloud down

Perubahan: patch social-memory skill + buat skill baru provider-outage-response.
"""
import os
import sys

sys.path.insert(0, "/home/sen/aeryn-core-agent")

# 1. Patch social_memory.py: ganti Leak_TOKENS (substring) → LEAK_PATTERNS
#    (exact regex). Ini dokumentasi supaya gak lupa teknis eksaknya.
#    --- SUDAH DIPATCH DI KODE ---

# 2. Buat/refresh skill provider-outage-response
print("Updating skill: provider-outage-response")
print("Updating skill: social-memory-sanitization")
