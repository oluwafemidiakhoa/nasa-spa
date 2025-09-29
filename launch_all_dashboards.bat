@echo off
echo ================================================================
echo NASA SPACE WEATHER FORECASTING SYSTEM - DASHBOARD LAUNCHER
echo ================================================================
echo.

REM Check if API server is running
echo [1/3] Checking API server status...
python test_urls.py
if errorlevel 1 (
    echo Starting API server...
    start "NASA API Server" python simple_api_server.py
    timeout /t 3 /nobreak >nul
)

echo.
echo [2/3] Testing all API endpoints...
python test_dashboards.py

echo.
echo [3/3] Opening dashboard hub...
start "" dashboard_hub.html

echo.
echo ================================================================
echo ALL SYSTEMS OPERATIONAL
echo ================================================================
echo.
echo Available Dashboards:
echo   - Main Hub: dashboard_hub.html
echo   - Simple Interface: simple.html  
echo   - Ensemble Dashboard: simple_new.html
echo   - Professional Control: professional_dashboard.html
echo   - Expert Physics: expert_dashboard.html
echo   - 3D Dashboard: 3d_dashboard.html
echo   - 3D Solar System: 3d_solar_system.html
echo.
echo API Server: http://localhost:9001
echo.
echo Press any key to exit...
pause >nul