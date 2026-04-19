@echo off
REM run.bat - GST JSON Generator Pro Launcher for Windows

setlocal enabledelayedexpansion

echo ========================================================
echo GST JSON Generator Pro v2.0
echo ========================================================
echo.

REM Check Python
python3 --version >nul 2>&1
if errorlevel 1 (
    echo X Error: Python 3 is not installed or not in PATH
    echo   Please install Python 3.7+ from https://www.python.org
    pause
    exit /b 1
)

echo + Python version:
python3 --version
echo.

REM Check/Create venv
if not exist "venv" (
    echo + Creating virtual environment...
    python3 -m venv venv
    echo + Virtual environment created
    echo.
)

REM Activate venv
echo + Activating virtual environment...
call venv\Scripts\activate.bat
echo + Virtual environment activated
echo.

REM Install/Upgrade packages
echo + Installing dependencies...
python3 -m pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -q -r requirements.txt
echo + Dependencies installed
echo.

REM Create directories
if not exist "logs" mkdir logs
if not exist "output" mkdir output
if not exist "test_output" mkdir test_output

REM Run application
echo + Starting application...
echo.
python3 main.py

REM Deactivate venv
call venv\Scripts\deactivate.bat
echo.
echo Application closed
pause
