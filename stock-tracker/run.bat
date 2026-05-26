@echo off
title Stock News Tracker
cd /d "%~dp0"

:: Try 'py' (Python Launcher) first, fall back to 'python'
where py >nul 2>&1
if %errorlevel% == 0 (
    py main.py %*
) else (
    python main.py %*
)

echo.
pause
