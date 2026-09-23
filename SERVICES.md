# Aeryn — Services (runit / runsvdir)

> Layanan Aeryn dijalankan via `runsvdir $PREFIX/var/service`.
> Script sumber: `aeryn_core/platform/service-aeryn-*.run` (satu sumber per service).

## Kelompok 1 — Aeryn Core (4 service)

| Service | Script | Peran | Log |
|---------|--------|-------|-----|
| `aeryn-api` | `service-aeryn-api.run` | FastAPI backend (:3010) — chat, catat, reminder, ledger, briefing, MCP | `aeryn-api.log` |
| `aeryn-worker` | `service-aeryn-worker.run` | Queue worker — poll_due (ZSET reminder) → execute | `aeryn-worker.log` |
| `aeryn-gateway` | `service-aeryn-gateway.run` | Discord gateway — ws+READY → allowlist → AgentLoop | `aeryn-gateway.log` |
| `aeryn-watchdog` | `service-aeryn-watchdog.run` | Monitor kesehatan (api/postgres/redis) interval 60s | `aeryn-watchdog.log` |

## Kelompok 2 — Infrastruktur (5 service)

| Service | Peran | Log |
|---------|-------|-----|
| `postgres` | Database utama (facts bitemporal, goals, cron_jobs) | `sv/postgres` |
| `redis` | Queue ZSET (scheduled/due) + cache | `sv/redis` |
| `sshd` | SSH akses (deploy + maintenance) | `sv/sshd` |
| `ssh-agent` | SSH agent (kredensial tanpa passphrase ulang) | `sv/ssh-agent` |
| `dbus` | System bus (termux-api: battery, notification) | `sv/dbus` |

## Pola run script (standar)

```sh
#!/data/data/com.termux/files/usr/bin/sh
export HOME=/data/data/com.termux/files/home
export PREFIX=/data/data/com.termux/files/usr
export PATH=$PREFIX/bin:$PATH
export AERYN_DB=... ; export NEON_DATABASE_URL=...
exec sh -c '<cmd> 2>&1 | stdbuf -oL tee -a $PREFIX/var/log/aeryn/<svc>.log'
```

## ⚠️ Orphan pattern (terkonfirmasi)

`sv restart` yang gagal bind (port dipakai) meninggalkan process lama (parent=1)
yang pegang port — anak runit crash loop. Solusi: kill process orphan
(`ps -ef | grep <svc>` + kill parent=1) → anak runit otomatis bind.

## Perintah harian

```sh
sv status $PREFIX/var/service/aeryn-api   # status satu service
sv restart $PREFIX/var/service/aeryn-api  # restart
tail $PREFIX/var/log/aeryn/aeryn-api.log  # log
```
