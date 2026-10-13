@echo off
title LibAR Public Mobile HTTPS Launcher
echo ========================================================
echo   LibAR — Public Mobile HTTPS Launcher
echo ========================================================
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else if exist "..\.venv\Scripts\python.exe" (
    set PYTHON_EXE=..\.venv\Scripts\python.exe
) else (
    set PYTHON_EXE=python
)

echo Starting LibAR public HTTPS server...
%PYTHON_EXE% run_tunnel.py
pause
