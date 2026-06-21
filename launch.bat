@echo off
REM Hassad ERP Quick Launch Script
REM ================================

echo.
set PYTHONIOENCODING=utf-8
echo ========================================
echo   Hassad ERP System Launcher
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: .\venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [1/3] Checking database connection...
venv\Scripts\python.exe check_db.py
if errorlevel 1 (
    echo.
    echo [ERROR] Database check failed!
    echo Please verify database configuration in .env file
    pause
    exit /b 1
)

echo.
echo [2/3] Starting Hassad ERP Application...
echo.
echo ========================================
echo   Login Credentials
echo ========================================
echo   Username: admin
echo   Password: admin123
echo ========================================
echo.

REM Launch application in new window
start "Hassad ERP" venv\Scripts\python.exe main.py

echo [3/3] Application launched in new window!
echo.
echo To stop the application:
echo   - Close the application window, or
echo   - Press Ctrl+C in the application console
echo.
echo To view routing logs:
echo   type logs\ui_routing.log
echo.
echo Launch complete!
echo.
pause
