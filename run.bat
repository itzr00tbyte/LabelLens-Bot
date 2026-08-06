@echo off
setlocal enabledelayedexpansion
echo ===================================================
echo       LabelLens Telegram Bot Runner (Windows)     
echo ===================================================

:: 1. Git Pull Latest Code
echo [1/4] Pulling latest updates from Git repository...
git pull origin main

:: 2. Check and Auto-Install Tesseract OCR on Windows RDP
echo.
echo [2/4] Checking Tesseract OCR Installation...
set "TESS_PATH="

if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    set "TESS_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe"
) else if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" (
    set "TESS_PATH=C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
) else if exist "%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe" (
    set "TESS_PATH=%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"
)

if not defined TESS_PATH (
    echo Tesseract OCR binary not found in standard paths.
    echo Attempting auto-installation via Winget...
    winget install --id UB-Mannheim.TesseractOCR -e --accept-source-agreements --accept-package-agreements
    if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
        set "TESS_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe"
    )
)

if defined TESS_PATH (
    echo [OK] Tesseract OCR located at: !TESS_PATH!
    set "TESSERACT_CMD=!TESS_PATH!"
) else (
    echo [NOTE] If Tesseract OCR is not installed yet, please download it from:
    echo        https://github.com/UB-Mannheim/tesseract/wiki
)

:: 3. Check Virtual Environment & Requirements
echo.
echo [3/4] Checking Python Virtual Environment & Dependencies...
if not exist .venv (
    echo Creating virtual environment .venv...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 4. Start LabelLens Bot
echo.
echo [4/4] Starting LabelLens Telegram Bot...
python -m app.main

pause
