#!/usr/bin/env bash
set -e

echo "==================================================="
echo "          LabelLens Telegram Bot Runner            "
echo "==================================================="

# Export Linux performance & process environment variables
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}

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
echo "[1/4] Pulling latest updates from Git repository..."
git pull origin main || true

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
