@echo off
echo ===================================================
echo           LabelLens Telegram Bot Runner           
echo ===================================================

echo [1/4] Pulling latest updates from Git repository...
git pull origin main

echo.
echo [2/4] Checking Python Virtual Environment...
if not exist .venv (
    echo Creating virtual environment .venv...
    python -m venv .venv
)

echo.
echo [3/4] Installing / Updating Python requirements...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [4/4] Starting LabelLens Telegram Bot...
python -m app.main

pause
