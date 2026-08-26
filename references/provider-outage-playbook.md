# Provider Outage Playbook

Full diagnosis tree for when LLM providers return errors.

## Quick triage
```bash
# 1. Is it code rot or provider outage?
./venv-proot/bin/python scripts/parity_probe.py 2>/dev/null | tail -1

# 2. If INCONCLUSIVE/DIVERGENSI with HTTP error codes → provider outage
#    Test each provider individually
./venv-proot/bin/python scripts/monitor_429.py
```

## Diagnosis tree
```
Agent returns: {"error": "LLM provider HTTP 4xx/5xx (semua model fallback habis)"}
                    ↓
          Semua provider error sama sekali?
                    ├─ YA → outage (bukan bug kode)
                    │         ├─ Cek kode error tiap provider:
                    │         │   - 429: rate limit → CircuitBreaker cooldown
                    │         │   - 404: model expired → hapus dari chain
                    │         │   - 410: model deprecated → update nama
                    │         │   - 403: UA block → browser UA
                    │         └─ 401: key expired → refresh auth.json
                    │
                    └─ TIDAK → bug kode (check recent commits)
```

## Live provider status checklist (Aug 2026)

| Provider | Status | Notes |
|---|---|---|
| NOUS (stealth/ox-alpha) | ✅ OK | Primary — fresh-read agent_key each chain build |
| NOUS free models | ❌ DEAD | Free period ended → remove from fallback chain |
| Groq (gpt-oss-20b) | ✅ OK | Works with browser-ident UA |
| OpenRouter free models | ❌ QUOTA | 429/day free-model quota → add paid key or rotate |
| Gemini (gemini-2.5-pro) | ⚠️ KEY ROTATION | Key di auth.json expired → refresh, bukan hardcoded |
| NVIDIA NIM (llama-3.1-8b-inst) | ❌ MODEL GONE | 410 Gone — ganti ke nvidia/llama-3.3-nemotron-super-49b-v1.5 |

## Response to 429 spam (the "astgho 429" case)

Symptom: `INCONCLUSIVE (provider error — ulangi probe): ... HTTP 429 (semua model fallback habis)` repeated 3× consecutively.

Root causes observed:
1. **Free-tier quota exhausted** (OpenRouter: 429 "free-models-per-day"). Fix: add paid model / API key
2. **NOUS free period ended** (404 "This model free period has ended"). Fix: remove from chain, use paid key
3. **CircuitBreaker not engaged** — each attempt retries same provider 3×. Fix: `range(1)` + circuit breaker `record_failure`

## Emergency actions

| If all cloud providers down → use local |
|---|
| Install llama.cpp + model GGUF (7B+) |
| Route agent → local endpoint fallback |
| `hermes send -t whatsapp "Semua provider down, Aeryn offline pakai llama lokal"` |

## Social memory sanitisation bug (V39.10e case study)
Leak pattern `"paisenmtvsky"` (concatenation bug) vs valid username `"Discord user: paisenmtvsky_ok"`.

Solution: regex exact-phrase match, BUKAN substring match.
```python
# BENAR (exact phrase):
LEAK_PATTERNS = [r"discord user:\s*siaisenmtvsky", ...]
for pat in LEAK_PATTERNS:
    if re.search(pat, fact, re.I): return False

# SALAH (block substring → False Positive username real):
LEAK_TOKENS = ("siais", "mtvsky", ...)
if any(tok in fact.lower()): return False
```
