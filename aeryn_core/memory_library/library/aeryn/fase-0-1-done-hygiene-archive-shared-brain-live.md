---
id: fase-0-1-done-hygiene-archive-shared-brain-live
topic: aeryn
tags: [aeryn,v33,shared-brain,hygiene,architecture]
signal: high
created: 2026-08-25
updated: 2026-08-25
summary: fase 0+1 done: hygiene archive + shared brain live
---

# fase 0+1 done: hygiene archive + shared brain live

FASE 0 (hygiene): AST import-graph audit dari semua entry point menemukan 31 modul tak terjangkau. Klasifikasi aman: 26 zero-importer+zero-test DIARSIPKAN ke _archive/v33-hygiene/ via git mv (restore mudah), 5 ber-test DIPARKIR (dynamic_schema, memory_consolidation, memory_curator, multi_agent, verification_gate). CHANGELOG V28->V33 ditulis. Regression 202/202 tetap hijau pasca-arsip. FASE 1 (shared brain): aeryn_core/hermes_brain.py baru - 3 tool tier-safe read-only menjembatani Aeryn ke memori kolektif Hermes via CLI: memory_search (library RAG), graph_traverse (knowledge graph), pitfall_search (pitfalls). Parity checkers + auto-promote terdaftar. Live E2E: agent menjawab 'webnovel stack pakai apa?' -> Fastify v4.29.1 dari memory_search. Bug nyata tertangkap di E2E: LLM kirim top sebagai string -> defensive coercion + test baru. Komit git tunggal V33+hygiene. Prinsip Hermes dipenuhi: extend dont duplicate, narrow waist, capability at edges.
