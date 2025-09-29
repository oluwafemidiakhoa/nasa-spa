@echo off
echo ================================================================
echo NASA SPACE WEATHER FORECASTER - EMAIL ALERT SETUP
echo ================================================================
echo.
echo This will help you configure email notifications for space weather alerts.
echo.
echo Requirements:
echo   - An email account (Gmail, Zoho, Outlook, etc.)
echo   - App password (for Gmail/Outlook) or regular password
echo.
pause

python setup_email_alerts.py

echo.
echo ================================================================
echo SETUP COMPLETE
echo ================================================================
echo.
echo To test your email alerts:
echo   1. Run: start_api_server.bat
echo   2. Open: professional_dashboard.html
echo   3. Click the "EMAIL ALERT" button
echo.
pause