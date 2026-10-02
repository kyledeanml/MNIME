@echo off
title MNIME Desktop - Setup
cd /d "%~dp0"

echo ========================================================
echo Installing MNIME Desktop Dependencies
echo ========================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python was not found in PATH.
    echo Please install Python 3.9+ or run this project from PyCharm.
    pause
    exit /b 1
)

if exist ".venv" goto :skip_venv
if exist "venv" goto :skip_venv
echo Creating virtual environment (.venv)...
python -m venv .venv

:skip_venv
echo.
echo Installing required packages from requirements.txt...

if exist ".venv\Scripts\pip.exe" (
    ".venv\Scripts\pip.exe" install --upgrade pip
    ".venv\Scripts\pip.exe" install -r requirements.txt
    goto :done
)

if exist "venv\Scripts\pip.exe" (
    "venv\Scripts\pip.exe" install --upgrade pip
    "venv\Scripts\pip.exe" install -r requirements.txt
    goto :done
)

echo ERROR: pip not found in .venv or venv. Setup may have failed.
pause
exit /b 1

:done
echo.
echo ========================================================
echo Setup complete! You can now run 'run.bat' or open
echo this directory in PyCharm and run MNIME.py.
echo ========================================================
pause
