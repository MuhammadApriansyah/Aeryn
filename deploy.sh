#!/bin/bash
# V39.64 — Aeryn Deployment Script
# Usage: ./deploy.sh [start|stop|restart|status|logs]

set -e

cd /home/sen/aeryn-core-agent

# Create required directories
mkdir -p logs
mkdir -p Personalisasi/Vault/{Raw,Wiki,Projects,System,Daily,Skills}
mkdir -p Personalisasi/Database/training

case "$1" in
    start)
        echo "Starting Aeryn services..."
        pm2 start ecosystem.config.cjs
        pm2 save
        echo "Services started. Check status with: ./deploy.sh status"
        ;;
    stop)
        echo "Stopping Aeryn services..."
        pm2 stop ecosystem.config.cjs
        pm2 save
        echo "Services stopped."
        ;;
    restart)
        echo "Restarting Aeryn services..."
        pm2 restart ecosystem.config.cjs
        pm2 save
        echo "Services restarted."
        ;;
    status)
        pm2 status
        ;;
    logs)
        pm2 logs
        ;;
    delete)
        echo "Deleting Aeryn services from PM2..."
        pm2 delete ecosystem.config.cjs
        pm2 save
        echo "Services deleted."
        ;;
    setup)
        echo "Setting up Aeryn for first time..."
        # Install Python deps if needed
        ./venv-proot/bin/pip install fastapi uvicorn psutil 2>/dev/null || true
        # Start services
        pm2 start ecosystem.config.cjs
        pm2 save
        # Setup log rotation
        pm2 install pm2-logrotate
        pm2 set pm2-logrotate:max_size 10M
        pm2 set pm2-logrotate:retain 7
        pm2 set pm2-logrotate:compress true
        echo "Setup complete!"
        ;;
    *)
        echo "Usage: ./deploy.sh [start|stop|restart|status|logs|setup|delete]"
        exit 1
        ;;
esac
