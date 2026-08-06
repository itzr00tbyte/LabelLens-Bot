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

# Resolve python interpreter (venv-first)
if [ -d ".venv" ]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python3"
fi

mkdir -p logs

case "$COMMAND" in
    start)
        echo "[1/1] Starting LabelLens Bot under PM2..."
        pm2 start ecosystem.config.js
        pm2 save
        ;;
    stop)
        echo "Stopping LabelLens Bot..."
        pm2 stop labellens-bot
        ;;
    restart)
        echo "Restarting LabelLens Bot..."
        pm2 restart labellens-bot
        ;;
    deploy)
        # Full deploy: pull latest → apply migrations → reload bot (zero-downtime)
        echo "[1/3] Pulling latest changes from Git..."
        git pull origin main

        echo "[2/3] Applying database migrations..."
        PYTHONPATH=. $PYTHON -m alembic upgrade head

        echo "[3/3] Reloading bot process..."
        if pm2 list | grep -q "labellens-bot"; then
            pm2 reload labellens-bot --update-env
        else
            pm2 start ecosystem.config.js
        fi
        pm2 save
        echo "[✓] Deploy complete."
        ;;
    logs)
        pm2 logs labellens-bot --lines 50
        ;;
    status)
        pm2 status labellens-bot
        ;;
    *)
        echo "Usage: ./pm2.sh {start|stop|restart|deploy|logs|status}"
        echo ""
        echo "  start    — Start the bot under PM2"
        echo "  stop     — Stop the bot"
        echo "  restart  — Hard restart the bot"
        echo "  deploy   — Pull latest → migrate DB → zero-downtime reload"
        echo "  logs     — Tail PM2 logs"
        echo "  status   — Show PM2 process status"
        exit 1
        ;;
esac
