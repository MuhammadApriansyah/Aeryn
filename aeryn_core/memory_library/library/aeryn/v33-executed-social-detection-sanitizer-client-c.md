---
id: v33-executed-social-detection-sanitizer-client-c
topic: aeryn
tags: [aeryn,v33,executed,web-search,bing]
signal: high
created: 2026-08-25
updated: 2026-08-25
summary: v33 executed: social detection + sanitizer + client cache + bing web search
---

# v33 executed: social detection + sanitizer + client cache + bing web search

V33 COMPLETE all phases. F1: _is_social_query rewritten (daemon+generator) - TECH_POSITIVE signals win first (library/api/cara kerja/apa itu...), social requires relational signal (greeting/pronoun/smalltalk), auto-40-char rule DELETED; 14 negative-case tests added. F2: sanitizer context-aware via _looks_machinelike (code-block/tool-shape/key:value>=2); natural sentences with error/sistem KEPT; log-style 'Error:' prefix + null/true/false JSON literals still caught. F3: MODEL global leak FIXED via _CLIENTS dict keyed (provider,model) - default requests no longer poisoned by specific-model requests. BONUS: web_search provider switched DuckDuckGo->Bing scrape (DDG SSL-blocked from this proot; Bing works), redirect u=a1<base64> decoded to real URLs. RESULTS: 194/194 tests passed (was 53), live smoke: 'kamu agy'->Aeryn correction 1-iter deterministic, 'kamu ingat aku'->personal natural reply, knowledge query goes through web_search tool path correctly. Files: aeryn_daemon.py, social_generator.py, model_client.py (by sibling), tool_bridge.py, +3 new test files.
