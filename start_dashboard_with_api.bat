@echo off
echo Starting NASA Space Weather Dashboard with API Server
echo =====================================================
echo.

cd /d "%~dp0"

echo [1/3] Starting API Server...
start "NASA API Server" cmd /k "C:\Users\adminidiakhoa\AppData\Local\miniconda3\python.exe" dashboard_api.py

echo [2/3] Waiting for API to start...
timeout /t 5 /nobreak

echo [3/3] Opening Dashboard...
start professional_dashboard.html

echo.
echo Dashboard launched successfully!
echo - API Server: http://localhost:8001
echo - Dashboard: professional_dashboard.html
echo.
echo Press any key to close this window...
pause