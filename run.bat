@echo off
title OmniMesh Desktop
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    echo Starting OmniMesh with .venv...
    ".venv\Scripts\python.exe" main.py
) else if exist "build_env\Scripts\python.exe" (
    echo Starting OmniMesh with build_env...
    "build_env\Scripts\python.exe" main.py
) else if exist "venv\Scripts\python.exe" (
    echo Starting OmniMesh with venv...
    "venv\Scripts\python.exe" main.py
) else (
    echo Starting OmniMesh with system Python...
    python main.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%.
    pause
)
