#!/bin/bash
# V40.0 — Production Deployment Script
# Run once to setup production environment

set -e

cd /home/sen/aeryn-core-agent

echo "=== AERYN v40 PRODUCTION DEPLOYMENT ==="

# 1. Create directories
mkdir -p logs
mkdir -p /tmp/aeryn_sandbox

# 2. Install dependencies for production
./venv-proot/bin/pip install psutil 2>/dev/null || true

# 3. Setup log rotation (pm2-logrotate)
pm2 install pm2-logrotate 2>/dev/null || true
pm2 set pm2-logrotate:max_size 10M 2>/dev/null || true
pm2 set pm2-logrotate:retain 7 2>/dev/null || true
pm2 set pm2-logrotate:compress true 2>/dev/null || true

# 4. Start all services
echo "Starting services..."
pm2 start ecosystem.config.cjs --env production 2>&1 || pm2 restart ecosystem.config.cjs

# 5. Save PM2 state
pm2 save

# 6. Setup monitoring cron
echo "Setting up monitoring..."

# 7. Verify
sleep 3
echo ""
echo "=== VERIFICATION ==="
curl -s http://127.0.0.1:3010/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Aeryn API: {d[\"status\"]} ({d.get(\"memory_mb\",\"?\")}MB)')"
curl -s http://127.0.0.1:5678/healthz && echo " — n8n: online"
curl -s http://127.0.0.1:3010/shared/stats | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Stats: {d[\"reminders\"][\"total\"]} reminders, {d[\"tasks\"][\"total\"]} tasks')"

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
pm2 status
