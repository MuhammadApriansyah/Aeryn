#!/bin/bash
# V39.64 — Log Rotation Script
# Run daily via cron: 0 0 * * * /home/sen/aeryn-core-agent/scripts/rotate_logs.sh

cd /home/sen/aeryn-core-agent

# Rotate PM2 logs
pm2 flush 2>/dev/null

# Compress old logs
find logs -name "*.log" -mtime +1 -exec gzip {} \; 2>/dev/null

# Remove logs older than 7 days
find logs -name "*.gz" -mtime +7 -delete 2>/dev/null

# Clean PM2 logs
pm2 reloadLogs 2>/dev/null

echo "Log rotation complete: $(date)"
