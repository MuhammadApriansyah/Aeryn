---
id: discord-alpha
topic: discord
tags: [discord, alpha, guild, bot, role-gate, koya, owo, jockie]
signal: high
created: 2026-08-24
updated: 2026-08-24
summary: Discord server 'Alpha' (guild 1541432407847084042) built via API. 5 bots locked per-account. @everyone base permissions. Aeryn separated from Hermes gateway — dedicated Aeryn token on DIFFERENT server.
---

## Server Alpha (guild 1541432407847084042)
- Built fully via Discord API (Sen gave direct execution authority)
- Categories: information/lobby/media dump/yapping/listening (emoji+'・' icons)
- read-only info, slowmode, role gating (@everyone = information only; Cwe/Cwo open rest; roles Member/Cwe/Cwo)
- AFK VC room-afk-dan-turu 15m; room-1 Jockie & room-2 FlaviBot
- Gateway Aeryn#8623 runs manual `hermes gateway run --replace`; Koya config via web dashboard

## Hardening (Aug 2026)
- @everyone base DISTRIP Connect+UseApplicationCommands (default Discord ON — role gating alone insufficient)
- Bots locked PER ACCOUNT (overwrite type:1) deny Send+AppCmd in ALL 25 channels/categories; allow only own home:
  - OwO→bot-owo, Haruka→bot-haruka, Jockie & FlaviBot→command-music, Koya→announcements/welcome/roles/goodbye
- Chat VC also closed for bots (no now-playing, Sen agreed)
- New #rules pinned: server structure + strict bot table
- GOTCHA: urllib to discord.com hits Cloudflare 1010 → MUST User-Agent 'DiscordBot (...)'
- Bot IDs: OwO 408785106942164992, Haruka 797688230869991456, Jockie 411916947773587456, FlaviBot 684773505157431347, Koya 276060004262477825

## Aeryn separation (CRITICAL)
- Sen will SEPARATE Discord Aeryn from Hermes gateway (don't mix)
- Dedicated Aeryn bot token will be sent later, tested on DIFFERENT Discord server (NOT Alpha guild 1541432407847084042)
- Do NOT use existing token/server for Aeryn
