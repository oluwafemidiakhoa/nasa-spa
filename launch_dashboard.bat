@echo off
echo NASA Space Weather Dashboard Launcher
echo ====================================
echo.

cd /d "%~dp0"

REM Use miniconda Python to avoid module issues
"C:\Users\adminidiakhoa\AppData\Local\miniconda3\python.exe" launch_dashboard.py

pause