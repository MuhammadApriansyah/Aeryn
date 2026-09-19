---
id: v38-8-cross-user-privacy-episodes-jsonl-berisi-g
topic: aeryn
tags: [aeryn]
signal: med
created: 2026-08-26
updated: 2026-08-26
summary: V38.8 cross-user privacy: episodes.jsonl (berisi goal semua user) bisa dibaca fs_read oleh user manapun. Fix: masuk SECRET_BASENAMES + blokir dir epis
---

# V38.8 cross-user privacy: episodes.jsonl (berisi goal semua user) bisa dibaca fs_read oleh user manapun. Fix: masuk SECRET_BASENAMES + blokir dir episodes/ dan sessions/. Live E2E: permintaan baca episode via Discord session ditolak kernel, Aeryn melapor dengan benar. 391 tests green.


