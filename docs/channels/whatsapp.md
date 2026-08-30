# WhatsApp Integration

> **Purpose**: Document WhatsApp bot integration via Discord gateway proxy.
> **Rule**: Real implementation — Aeryn uses a gateway bridge for WhatsApp.

---

## 🏗️ Architecture

```
User (WhatsApp) → Gateway Bot → Aeryn Core → Response → Gateway Bot → User (WhatsApp)
```

Aeryn itself does not have a native WhatsApp API. The Discord gateway acts as a bridge:
1. Discord bot receives messages from Discord channels
2. User configures Discord ↔ WhatsApp bridge (via external service like Discohook or custom bridge)
3. Messages route through Discord to Aeryn
4. Aeryn processes and responds via Discord bot

---

## 🚀 Setup

### Prerequisites

1. Discord bot configured with gateway routing
2. Discord server with channels for each WhatsApp contact
3. Bridge service (Discohook, custom webhook, or WhatsApp Web API bridge)

### Environment Variables

```bash
export DISCORD_TOKEN=[REDACTED]
export DISCORD_GUILD_ID=[REDACTED]
export WHATSAPP_BRIDGE_ENABLED=true
```

---

## 📨 Message Flow

### Incoming Message (WhatsApp → Aeryn)

1. WhatsApp message sent to bridge
2. Bridge forwards to Discord channel
3. Discord bot picks up message
4. Message stored in `SocialMemory`
5. Processed by appropriate cognitive division
6. Response sent via Discord bot back to WhatsApp

### Outgoing Message (Aeryn → WhatsApp)

1. Aeryn generates response
2. Posted to Discord channel
3. Discord bot forwards to WhatsApp via bridge

---

## 🛠️ Configuration

### Discord Bot Commands

| Command | Description |
|---------|-------------|
| `/setup-whatsapp` | Configure WhatsApp bridge settings |
| `/whatsapp-send` | Send message to WhatsApp contact |
| `/whatsapp-list` | List connected WhatsApp contacts |

### Channel Mapping

Map Discord channels to WhatsApp contacts:

```python
# In SocialMemory
{
    "whatsapp_mapping": {
        "1234567890": "discord_channel_1",
        "+1234567890": "discord_channel_2"
    }
}
```

---

## 📊 Features

### Real-time Messaging
- Messages appear instantly in Discord
- Typing indicators supported via Discord

### Group Chats
- Group WhatsApp chats bridge to Discord channels
- Role-based permissions in Discord control group access

### Media Support
- Images: Supported via Discord file upload
- Documents: Forwarded as Discord attachments
- Audio: Voice notes forwarded as audio files

---

## 🧪 Testing

WhatsApp integration is tested via the Discord gateway:

```bash
# Run Discord-related tests
python -m pytest tests/test_discord.py -x -q

# Verify bot connectivity
curl http://127.0.0.1:3010/api/discord/commands
```

---

## ⚠️ Limitations

- Requires external bridge service (not built into Aeryn)
- Media forwarding depends on bridge capabilities
- Group admin rights needed for group bridging
- Rate limits apply (Discord + WhatsApp combined)

---

*WhatsApp integration v59.0 — Updated 2026-08-30.*
