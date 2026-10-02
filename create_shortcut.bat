@echo off
title MNIME - Create Desktop ^& Quickbar Shortcut
cd /d "%~dp0"

echo ========================================================
echo Generating MNIME Quickbar and Desktop Shortcuts
echo ========================================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "from core.app_icon import create_windows_shortcuts, ensure_ico_file; ensure_ico_file(); res = create_windows_shortcuts(); print('Shortcut status:', res)"
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" -c "from core.app_icon import create_windows_shortcuts, ensure_ico_file; ensure_ico_file(); res = create_windows_shortcuts(); print('Shortcut status:', res)"
) else (
    python -c "from core.app_icon import create_windows_shortcuts, ensure_ico_file; ensure_ico_file(); res = create_windows_shortcuts(); print('Shortcut status:', res)"
)

echo.
echo ========================================================
echo A shortcut 'MNIME' has been created on
echo your Desktop and inside this folder!
echo.
echo To pin to your Quickbar / Taskbar:
echo Right-click the shortcut -> click 'Pin to taskbar'
echo ========================================================
echo.
pause
