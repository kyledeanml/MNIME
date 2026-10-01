@echo off
title OMNIME Desktop - Setup
cd /d "%~dp0"

echo ========================================================
echo Installing OMNIME Desktop Dependencies
echo ========================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python was not found in PATH.
    echo Please install Python 3.9+ or run this project from PyCharm.
    pause
    exit /b 1
)

if not exist ".venv" if not exist "venv" (
    echo Creating virtual environment (.venv)...
    python -m venv .venv
)

echo.
echo Installing required packages from requirements.txt...
if exist ".venv\Scripts\pip.exe" (
    ".venv\Scripts\pip.exe" install --upgrade pip
    ".venv\Scripts\pip.exe" install -r requirements.txt
) else if exist "venv\Scripts\pip.exe" (
    "venv\Scripts\pip.exe" install --upgrade pip
    "venv\Scripts\pip.exe" install -r requirements.txt
)

echo.
echo ========================================================
echo Setup complete! You can now run 'run.bat' or open
echo this directory in PyCharm and run OMNIME.py.
echo ========================================================
pause
