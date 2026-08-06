#!/usr/bin/env bash
set -e

echo "==================================================="
echo "          LabelLens Telegram Bot Runner            "
echo "==================================================="

# Export Linux performance & process environment variables
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
export PYTHONPATH=.

# Auto-provision .env if missing
if [ ! -f ".env" ]; then
    if [ -f ".env.linux.example" ]; then
        echo "[!] No .env file found. Copying .env.linux.example to .env..."
        cp .env.linux.example .env
    elif [ -f ".env.example" ]; then
        echo "[!] No .env file found. Copying .env.example to .env..."
        cp .env.example .env
    fi
fi

# Check system Tesseract installation on Linux
if command -v tesseract >/dev/null 2>&1; then
    echo "[✓] Tesseract OCR detected at: $(which tesseract)"
else
    echo "[!] Warning: Tesseract OCR binary not found in PATH."
    echo "    On Linux (Debian/Ubuntu), run: sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-eng"
fi

echo ""
echo "[1/3] Pulling latest updates from Git repository..."
git pull origin main || true

echo ""
echo "[2/3] Installing / Updating Python requirements..."
if [ -d ".venv" ]; then
    echo "Using virtual environment .venv..."
    source .venv/bin/activate
    pip install -r requirements.txt
else
    echo "Installing requirements globally using system python3..."
    pip3 install -r requirements.txt --break-system-packages 2>/dev/null || pip3 install -r requirements.txt
fi

echo ""
echo "[3/3] Starting LabelLens Telegram Bot..."
if [ -d ".venv" ]; then
    python3 -m app.main
else
    python3 app/main.py
fi
