#!/bin/bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 20
cd /home/sen/aeryn-core-agent/aeryn-web
NODE_ENV=development NODE_OPTIONS="--max-old-space-size=512" npm run dev -- --port 3020
