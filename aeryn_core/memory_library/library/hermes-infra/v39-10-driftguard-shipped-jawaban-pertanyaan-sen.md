---
id: v39-10-driftguard-shipped-jawaban-pertanyaan-sen
topic: hermes-infra
tags: [hermes-infra]
signal: med
created: 2026-08-26
updated: 2026-08-26
summary: V39.10 DriftGuard shipped (jawaban pertanyaan Sen soal update Hermes): skrip drift_guard.py mengecek 5 titik integrasi (state.db schema, hermes CLI, a
---

# V39.10 DriftGuard shipped (jawaban pertanyaan Sen soal update Hermes): skrip drift_guard.py mengecek 5 titik integrasi (state.db schema, hermes CLI, auth agent_key, INDEX library, memory_library API) sebelum & sesudah update. Ritual: baseline OK -> update -> verify; drift = exit 1 + titik pecah ditunjuk. Live 5/5 hijau (Hermes v0.20.5). 462 tests green.


