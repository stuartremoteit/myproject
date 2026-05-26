@echo off
title Stock News Tracker [LIVE]
cd /d "%~dp0"

:: Try 'py' (Python Launcher) first, fall back to 'python'
:: Passes --watch automatically; any extra args (tickers, --interval) go after
where py >nul 2>&1
if %errorlevel% == 0 (
    py main.py --watch %*
) else (
    python main.py --watch %*
)

echo.
pause
