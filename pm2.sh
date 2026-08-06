#!/usr/bin/env bash
set -e

COMMAND="${1:-start}"

echo "==================================================="
echo "          LabelLens Bot PM2 Manager               "
echo "==================================================="

if ! command -v pm2 >/dev/null 2>&1; then
    echo "[!] Error: PM2 is not installed."
    echo "    To install PM2 globally, run: npm install -g pm2"
    exit 1
fi

mkdir -p logs

case "$COMMAND" in
    start)
        echo "Starting LabelLens Bot under PM2..."
        pm2 start ecosystem.config.js
        ;;
    stop)
        echo "Stopping LabelLens Bot..."
        pm2 stop labellens-bot
        ;;
    restart)
        echo "Restarting LabelLens Bot..."
        pm2 restart labellens-bot
        ;;
    logs)
        pm2 logs labellens-bot
        ;;
    status)
        pm2 status labellens-bot
        ;;
    *)
        echo "Usage: ./pm2.sh {start|stop|restart|logs|status}"
        exit 1
        ;;
esac
