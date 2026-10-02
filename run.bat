@echo off
title MNIME Desktop
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    echo Starting MNIME with .venv...
    ".venv\Scripts\python.exe" MNIME.py
) else if exist "build_env\Scripts\python.exe" (
    echo Starting MNIME with build_env...
    "build_env\Scripts\python.exe" MNIME.py
) else if exist "venv\Scripts\python.exe" (
    echo Starting MNIME with venv...
    "venv\Scripts\python.exe" MNIME.py
) else (
    echo Starting MNIME with system Python...
    python MNIME.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%.
    pause
)
