---
id: synth-aeryn-core+webnovel-stack
topic: synthesis
tags: [aeryn, webnovel, insight]
signal: med
summary: Cross-domain insight: aeryn x webnovel
---

# aeryn x webnovel

Both systems rely on PM2 for process management but face silent failures: Aeryn's daemon can hang on provider timeouts while Webnovel's Fastify server stays "online" despite plugin version mismatches, masking actual startup errors. The shared lesson is that PM2's process status doesn't guarantee functional health, so both need explicit health checks (like Aeryn's /health endpoint) to detect when the service is running but not actually serving requests.
