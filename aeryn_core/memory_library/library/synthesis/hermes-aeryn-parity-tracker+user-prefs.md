---
id: synth-hermes-aeryn-parity-tracker+user-prefs
topic: synthesis
tags: [hermes-infra, user-prefs, insight]
signal: med
summary: Cross-domain insight: hermes-infra x user-prefs
---

# hermes-infra x user-prefs

Both systems risk silent drift when delegation boundaries blur: Aeryn's ask_hermes channel could route tasks Hermes handles imperfectly, while user-prefs' "authority to do everything" invites unlogged changes that break parity without test-suite coverage. The transferable lesson is enforcing explicit handoff contracts (tested inputs/outputs) before autonomous delegation, not after.
