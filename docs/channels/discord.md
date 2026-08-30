# Discord Integration

> **Purpose**: Document Discord bot integration with Aeryn's cognitive system.
> **Rule**: Real implementation — Aeryn has a production Discord bot handler.

---

## 🏗️ Architecture

```
Discord User → Discord Gateway → Aeryn DiscordBotHandler → Cognitive Divisions → Discord Response
```

### Components

| Component | File | Purpose |
|----------|------|---------|
| `DiscordBotHandler` | `aeryn_core/platform/discord_bot.py` | Discord bot event handler |
| Bot Runner | `apps/api/aeryn_api.py` | Bot lifecycle management |
| Channel Routing | `aeryn_core/platform/discord_bot.py` | Route messages to handlers |

---

## 🚀 Setup

### Bot Permissions

Required Discord permissions:
- Read Messages
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Add Reactions
- Use Slash Commands

### Environment Variables

```bash
export DISCORD_TOKEN=[REDACTED]
export DISCORD_GUILD_ID=1541432407847084042
export DISCORD_PREFIX=!
export DISCORD_BOT_OWNER=<owner_user_id>
```

### Starting the Bot

The Discord bot starts automatically with the Aeryn API:

```bash
pm2 start apps/api/aeryn_api.py --name aeryn-api --interpreter ./venv-proot/bin/python
```

Or check if running:

```bash
# List registered commands
curl http://127.0.0.1:3010/api/discord/commands

# Trigger interaction
curl -X POST http://127.0.0.1:3010/api/discord/interaction
```

---

## 📨 Message Handling

### Command Processing

```python
# Commands handled:
# !help          — List available commands
# !run <goal>    — Execute a goal via Aeryn
# !search <q>    — Search Aeryn's knowledge
# !chat <msg>    — Chat with Aeryn
# !health        — Check system health
# !plugins       — List available plugins
# !billing       — Check subscription status
```

### Message Routing

Messages are routed based on:
1. **Channel ID**: Different channels for different purposes
2. **Command prefix**: `!` for commands, otherwise treated as chat
3. **User role**: Admin commands restricted to owner

### Cognitive Division Routing

Incoming messages are routed to the appropriate division:

| Message Type | Division | Example |
|-------------|----------|---------|
| Creative request | Division 1 (Creative) | "Write a poem about AI" |
| Emotional/behavioral | Division 2 (Psychology) | "How do I feel today?" |
| Logical reasoning | Division 3 (Reasoning) | "Plan my project timeline" |
| Compliance/audit | Division 4 (Governance) | "Show my audit log" |
| System operations | Division 5 (Infrastructure) | "Check system health" |
| General chat | Auto-routed | "Hello Aeryn" |

---

## 🔧 Configuration

### Bot Commands Endpoint

```bash
curl http://127.0.0.1:3010/api/discord/commands
```

Returns:
```json
{
  "commands": [
    {"name": "help", "description": "List commands"},
    {"name": "run", "description": "Execute a goal"},
    {"name": "search", "description": "Search knowledge"}
  ]
}
```

### Interaction Handler

```bash
curl -X POST http://127.0.0.1:3010/api/discord/interaction
```

---

## 📊 Features

### Slash Commands
- `/run` — Execute a goal
- `/search` — Search knowledge
- `/chat` — Chat with Aeryn
- `/health` — System status
- `/plugins` — Plugin management

### Message Content
- Rich embeds with formatted output
- File attachments for code/output
- Typing indicators during processing
- Automatic error handling with error boundary

### Channel Management
- Multi-channel support
- Channel-specific permissions
- Auto-archive inactive channels
- Notification routing

---

## 🧪 Testing

```bash
# Run Discord tests
python -m pytest tests/test_discord.py -x -q
python -m pytest tests/test_discord_bot.py -x -q

# Verify bot connectivity
curl http://127.0.0.1:3010/api/discord/commands
curl -X POST http://127.0.0.1:3010/api/discord/interaction
```

---

## ⚠️ Known Limitations

- Bot runs as single instance (no sharding)
- Limited to 50 commands (Discord limit)
- Embed size limits (6000 chars max)
- Rate limits: 50 requests/50ms per channel
- File upload: 25MB max (non-Nitro), 500MB (Nitro)

---

## 🐛 Troubleshooting

### Bot Not Responding

```bash
# Check if bot is registered
curl http://127.0.0.1:3010/health

# Check for errors
pm2 logs aeryn-api | grep -i discord

# Verify bot is online in Discord
```

### Command Not Registered

```bash
# Re-register commands
curl -X POST http://127.0.0.1:3010/api/discord/register
```

### Permission Errors

- Ensure bot has `applications.commands` scope
- Verify channel permissions
- Check bot role hierarchy

---

*Discord integration v59.0 — Production ready. Updated 2026-08-30.*
