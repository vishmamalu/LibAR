@echo off
title LibAR Mobile AR Server
echo ========================================================
echo   LibAR — Mobile AR Library Navigation Launcher
echo ========================================================
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else if exist "..\.venv\Scripts\python.exe" (
    set PYTHON_EXE=..\.venv\Scripts\python.exe
) else (
    set PYTHON_EXE=python
)

echo Starting LibAR server...
%PYTHON_EXE% run_production.py
pause
