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

# ── Resolve python interpreter (venv-first, then global) ────────────────────
if [ -d ".venv" ]; then
    PYTHON=".venv/bin/python"
    PIP=".venv/bin/pip"
    echo "[✓] Using .venv interpreter"
else
    PYTHON="python3"
    # Resolve pip — try pip3, pip, then python3 -m pip as last resort
    if command -v pip3 >/dev/null 2>&1; then
        PIP="pip3"
    elif command -v pip >/dev/null 2>&1; then
        PIP="pip"
    else
        PIP="python3 -m pip"
    fi
    echo "[✓] Using global python3: $(which python3)"
fi

mkdir -p logs

# ── Helper: install requirements ────────────────────────────────────────────
install_requirements() {
    echo "    Installing Python requirements..."
    # Try plain install first (Ubuntu 22.04 / older pip has no --break-system-packages)
    # Fall back to --break-system-packages for Debian 12+ / Ubuntu 23+
    $PIP install -r requirements.txt 2>/dev/null \
        || $PIP install -r requirements.txt --break-system-packages
}

# ── Helper: run alembic migration ───────────────────────────────────────────
run_migrations() {
    echo "    Running: PYTHONPATH=. $PYTHON -m alembic upgrade head"
    PYTHONPATH=. $PYTHON -m alembic upgrade head
}

case "$COMMAND" in
    start)
        echo "[1/3] Installing / Updating Python requirements..."
        install_requirements

        echo "[2/3] Applying database migrations..."
        run_migrations

        echo "[3/3] Starting LabelLens Bot under PM2..."
        pm2 start ecosystem.config.js
        pm2 save
        echo "[✓] Bot started."
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
        echo "[1/4] Pulling latest changes from Git..."
        git pull origin main

        echo "[2/4] Installing / Updating Python requirements..."
        install_requirements

        echo "[3/4] Applying database migrations..."
        run_migrations

        echo "[4/4] Reloading bot process (zero-downtime)..."
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
        echo "  start    — Install deps + migrate DB + start under PM2"
        echo "  stop     — Stop the bot"
        echo "  restart  — Hard restart the bot"
        echo "  deploy   — Pull latest + install deps + migrate + zero-downtime reload"
        echo "  logs     — Tail PM2 logs (last 50 lines)"
        echo "  status   — Show PM2 process status"
        exit 1
        ;;
esac
