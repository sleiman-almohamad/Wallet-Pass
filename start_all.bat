@echo off
REM Windows Batch Script to Start Google Wallet Verifier & Preview Application
REM This script starts Docker services, FastAPI backend, and Flet GUI

echo ==========================================
echo Starting Wallet Passes Application
echo ==========================================
echo.

REM Check if Docker is running
echo Checking Docker services status...
docker ps >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

REM Start Docker Compose services
echo.
echo Starting Docker services...
docker compose up -d

REM Wait for services to be ready
echo Waiting for services to start...
timeout /t 5 /nobreak >nul

echo.
echo Services started successfully!

echo.
echo ==========================================
echo Services Available:
echo ==========================================
echo phpMyAdmin:  http://localhost:8080
echo    Username: root
echo    Password: 123456789
echo.
echo FastAPI:     http://localhost:8000
echo    Docs:     http://localhost:8000/docs
echo.
echo MariaDB:     localhost:3306
echo    Database: wallet_passes
echo.
echo ==========================================
echo.

REM Start FastAPI server in a new window
echo Starting FastAPI server in background...
start "FastAPI Server" /MIN cmd /c "uv run python -m uvicorn api.api:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for API to start
timeout /t 3 /nobreak >nul

REM Start the Flet GUI application
echo.
echo Starting Flet application...
uv run python main.py

REM When Flet app closes
echo.
echo Flet application closed.
echo.
set /p STOP_API="Do you want to stop the API server? (y/n): "
if /i "%STOP_API%"=="y" (
    echo Stopping API server...
    taskkill /FI "WINDOWTITLE eq FastAPI Server*" /T /F >nul 2>&1
    echo API server stopped.
)

echo.
pause

