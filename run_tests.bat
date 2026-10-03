@echo off
echo Running MNIME tests...
set PYTHONPATH=%cd%
python -m pytest tests/
pause
