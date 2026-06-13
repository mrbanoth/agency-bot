@echo off
title Agency Bot — Running 24/7
call venv\Scripts\activate.bat
echo.
echo  Agency Bot is running. Do NOT close this window.
echo  Check your email every morning for new leads.
echo  Press Ctrl+C to stop.
echo.
python scheduler.py
pause
