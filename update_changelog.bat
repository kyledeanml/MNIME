@echo off
title Update MNIME Change Log PDF
cd /d "%~dp0"

echo ========================================================
echo Updating MNIME Change Log PDF from CHANGE_LOG.txt...
echo ========================================================

set "PYTHON_EXE="
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "C:\Users\kyled\AppData\Local\Programs\Python\Python312\python.exe" set "PYTHON_EXE=C:\Users\kyled\AppData\Local\Programs\Python\Python312\python.exe"
if not defined PYTHON_EXE set "PYTHON_EXE=python"

"%PYTHON_EXE%" scripts\generate_changelog_pdf.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo SUCCESS: MNIME_Change_Log.pdf and docs\changelog_cover.png
    echo have been successfully generated and synchronized.
    echo ========================================================
) else (
    echo.
    echo ERROR: Failed to generate changelog PDF.
)
pause
