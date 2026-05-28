@echo off
title SMART EVM -- Fresh Setup
color 0B
echo.
echo  ==========================================
echo   SMART EVM -- Fresh Setup / Re-install
echo  ==========================================
echo.
cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Please install Python 3.11+ from python.org
    echo  and tick "Add Python to PATH" during setup.
    pause
    exit /b 1
)

echo  Removing old virtual environment (if any)...
if exist ".venv" rmdir /s /q ".venv"

echo  Creating fresh virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

echo  Upgrading pip...
pip install --upgrade pip --quiet

echo  Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo  [ERROR] Installation failed. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo  ==========================================
echo   Setup complete!  Run START.bat to launch.
echo  ==========================================
echo.
pause
