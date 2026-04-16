@echo off
REM Sales API Quick Start Script for Windows

setlocal enabledelayedexpansion

echo ================================
echo Sales API - Quick Start (Windows)
echo ================================

REM Check if Docker is running
echo.
echo [*] Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [X] Docker is not installed. Please install Docker first.
    exit /b 1
)

REM Start Docker containers
echo [*] Starting Docker services (PostgreSQL ^& Redis)...
docker-compose up -d

REM Wait for services to be healthy
echo [*] Waiting for services to be healthy...
timeout /t 5 /nobreak

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [*] Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo [*] Installing dependencies...
pip install -q -r requirements.txt

REM Run migrations
echo [*] Running Alembic migrations...
alembic upgrade head

REM Start the application
echo.
echo ================================
echo [+] All set! Starting application...
echo ================================
echo.
echo API Documentation: http://localhost:8000/docs
echo API: http://localhost:8000
echo.

uvicorn app.main:app --reload

pause
