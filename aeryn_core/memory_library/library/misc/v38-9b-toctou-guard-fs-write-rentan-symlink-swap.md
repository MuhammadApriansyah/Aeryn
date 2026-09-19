---
id: v38-9b-toctou-guard-fs-write-rentan-symlink-swap
topic: misc
tags: [misc]
signal: med
created: 2026-08-26
updated: 2026-08-26
summary: V38.9b TOCTOU guard: fs_write rentan symlink-swap race antara check_path dan open. Fix: parent dir_fd + O_NOFOLLOW (kernel tolak ELOOP). Simulasi race
---

# V38.9b TOCTOU guard: fs_write rentan symlink-swap race antara check_path dan open. Fix: parent dir_fd + O_NOFOLLOW (kernel tolak ELOOP). Simulasi race test: .env asli utuh, tulis ditolak. 415 tests green.


