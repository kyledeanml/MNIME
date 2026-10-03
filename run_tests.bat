@echo off
echo Running MNIME tests...
cd /d "%~dp0"
set PYTHONPATH=%~dp0
python -m pytest tests/
pause
