#!/usr/bin/env bash
set -e

echo "==================================================="
echo "          LabelLens Telegram Bot Runner            "
echo "==================================================="

echo "[1/4] Pulling latest updates from Git repository..."
git pull origin main

echo ""
echo "[2/4] Checking Python Virtual Environment..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment .venv..."
    python3 -m venv .venv
fi

echo ""
echo "[3/4] Installing / Updating Python requirements..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "[4/4] Starting LabelLens Telegram Bot..."
python3 -m app.main
