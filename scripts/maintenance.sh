#!/bin/bash
# V40.22 — Maintenance Automation: Cron jobs, backup, health checks.
# Run daily/weekly maintenance tasks.

set -e

cd /home/sen/aeryn-core-agent
LOG_FILE="logs/maintenance_$(date +%Y%m%d).log"

echo "=== AERYN MAINTENANCE $(date) ===" | tee -a "$LOG_FILE"

# 1. Health check
echo "1. Health check..." | tee -a "$LOG_FILE"
HEALTH=$(curl -s http://127.0.0.1:3010/health 2>/dev/null || echo '{"status":"down"}')
STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','down'))" 2>/dev/null || echo "down")
echo "   Status: $STATUS" | tee -a "$LOG_FILE"

if [ "$STATUS" != "healthy" ]; then
    echo "   WARNING: Service unhealthy, restarting..." | tee -a "$LOG_FILE"
    pm2 restart aeryn-api
    sleep 5
fi

# 2. Memory indexing
echo "2. Memory indexing..." | tee -a "$LOG_FILE"
curl -s -X POST http://127.0.0.1:3010/memory/decay 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print(f'   Decayed: {d.get(\"total_affected\",0)} entries')
except:
    print('   No decay needed')
" | tee -a "$LOG_FILE"

# 3. Dream synthesis (once daily at 3AM)
HOUR=$(date +%H)
if [ "$HOUR" -eq "03" ]; then
    echo "3. Dream synthesis..." | tee -a "$LOG_FILE"
    curl -s -X POST http://127.0.0.1:3010/dream/synthesize 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print(f'   Generated: {d.get(\"insights_generated\",0)} insights')
except:
    print('   Synthesis skipped')
" | tee -a "$LOG_FILE"
fi

# 4. Backup (once daily at 4AM)
if [ "$HOUR" -eq "04" ]; then
    echo "4. Backup..." | tee -a "$LOG_FILE"
    curl -s -X POST http://127.0.0.1:3010/sync/backup 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print(f'   Backup: {d.get(\"files_backed_up\",0)} files, {d.get(\"total_size_mb\",0)}MB')
except:
    print('   Backup failed')
" | tee -a "$LOG_FILE"
fi

# 5. Log cleanup
echo "5. Log cleanup..." | tee -a "$LOG_FILE"
find logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
echo "   Old logs cleaned" | tee -a "$LOG_FILE"

# 6. Git backup
echo "6. Git backup..." | tee -a "$LOG_FILE"
git add -A 2>/dev/null
git diff --cached --quiet || git commit -m "Maintenance: $(date +%Y-%m%d) auto-backup" 2>/dev/null || true
echo   "Git committed" | tee -a "$LOG_FILE"

echo "=== MAINTENANCE COMPLETE $(date) ===" | tee -a "$LOG_FILE"
