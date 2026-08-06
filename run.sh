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

# Check system Tesseract installation
if command -v tesseract >/dev/null 2>&1; then
    echo "[✓] Tesseract OCR detected at: $(which tesseract)"
else
    echo "[!] Warning: Tesseract OCR not found in PATH."
    echo "    On Debian/Ubuntu: sudo apt-get install -y tesseract-ocr tesseract-ocr-eng"
fi

# Resolve python & pip — prefer .venv if it exists
if [ -d ".venv" ]; then
    PYTHON=".venv/bin/python"
    PIP=".venv/bin/pip"
    echo "[✓] Using virtual environment: .venv"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
    # Try to find pip — could be pip3, pip, or python3 -m pip
    if command -v pip3 >/dev/null 2>&1; then
        PIP="pip3"
    elif command -v pip >/dev/null 2>&1; then
        PIP="pip"
    else
        PIP="python3 -m pip"
    fi
    echo "[✓] Using global python3: $(which python3)"
else
    echo "[✗] Error: No python3 interpreter found. Aborting."
    exit 1
fi

echo ""
echo "[1/4] Pulling latest updates from Git repository..."
git pull origin main || true

echo ""
echo "[2/4] Installing / Updating Python requirements..."
$PIP install -r requirements.txt --break-system-packages 2>/dev/null || $PIP install -r requirements.txt

echo ""
echo "[3/4] Applying database migrations..."
$PYTHON -m alembic upgrade head

echo ""
echo "[4/4] Starting LabelLens Telegram Bot..."
exec $PYTHON -m app.main
