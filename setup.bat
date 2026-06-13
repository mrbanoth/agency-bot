@echo off
title Agency Bot Setup
echo.
echo =====================================================
echo   FREELANCE AGENCY BOT -- ONE-TIME SETUP
echo =====================================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://python.org
    pause & exit /b 1
)
echo [1/5] Python found OK

REM --- Create virtual environment ---
if not exist venv (
    echo [2/5] Creating virtual environment ...
    python -m venv venv
) else (
    echo [2/5] Virtual environment already exists
)

REM --- Activate venv and install packages ---
echo [3/5] Installing packages (groq, playwright, schedule, etc.) ...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
if errorlevel 1 (echo ERROR: pip install failed & pause & exit /b 1)
echo       Packages installed OK

REM --- Install headless Chrome ---
echo [4/5] Installing headless Chrome browser ...
playwright install chromium
if errorlevel 1 (echo ERROR: playwright install failed & pause & exit /b 1)
echo       Chrome installed OK

REM --- Create .env if missing ---
echo [5/5] Checking .env ...
if not exist .env (
    copy .env.example .env >nul
    echo       .env created from template
) else (
    echo       .env already exists
)

echo.
echo =====================================================
echo   SETUP COMPLETE! Now do 2 things:
echo.
echo   1. Open .env and fill in:
echo      GMAIL_APP_PASSWORD=  (from myaccount.google.com)
echo      GROQ_API_KEY=        (free from console.groq.com)
echo.
echo   2. Then double-click run_24_7.bat to start the bot
echo =====================================================
echo.
pause
