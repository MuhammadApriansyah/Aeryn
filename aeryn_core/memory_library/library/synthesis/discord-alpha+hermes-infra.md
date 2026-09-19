---
id: synth-discord-alpha+hermes-infra
topic: synthesis
tags: [discord, hermes-infra, insight]
signal: med
summary: Cross-domain insight: discord x hermes-infra
---

# discord x hermes-infra

Both systems rely on a single operator (Sen) with bypass-level access: Sen manually runs `hermes gateway run --replace` in Discord while also controlling `gwctl.py` and `config.yaml` edits via terminal approval, creating a shared risk where any compromise or mistake by Sen could simultaneously disrupt both the Discord bot permissions and the gateway infrastructure.
