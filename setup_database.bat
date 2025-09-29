@echo off
echo ================================================================
echo NASA SPACE WEATHER FORECASTER - DATABASE SETUP
echo ================================================================
echo.
echo This will initialize the SQLite database for storing:
echo   - Space weather forecasts and predictions
echo   - Historical data and trends
echo   - Active alerts and notifications
echo   - System logs and monitoring data
echo.
echo Requirements check...

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)

echo SUCCESS: Python is available
echo.
echo Installing database dependencies...
python -m pip install sqlalchemy aiosqlite

echo.
echo Initializing database...
python setup_database.py

echo.
echo Testing database API endpoints...
python test_database_api.py

echo.
echo ================================================================
echo DATABASE SETUP COMPLETE
echo ================================================================
echo.
echo The database is now ready for use. Key features:
echo   - Automatic forecast storage
echo   - Historical data tracking
echo   - Alert management
echo   - Accuracy monitoring
echo.
echo Database file: space_weather.db
echo.
echo Restart the API server to enable database features:
echo   python simple_api_server.py
echo.
pause