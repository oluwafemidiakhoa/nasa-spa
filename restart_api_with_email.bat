@echo off
echo ================================================================
echo NASA SPACE WEATHER API SERVER WITH EMAIL ALERTS
echo ================================================================
echo.
echo Stopping any existing API server...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq NASA API Server*" 2>nul

echo.
echo Starting enhanced API server with email alerts...
echo.
echo Features enabled:
echo   - Space weather forecasting
echo   - 3D visualization data
echo   - EMAIL ALERTS
echo   - Test email functionality
echo.
echo New endpoints:
echo   POST /api/v1/alerts/email  - Send space weather alert
echo   POST /api/v1/alerts/test   - Send test email
echo.

python simple_api_server.py

pause