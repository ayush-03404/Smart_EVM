@echo off
title SMART EVM Launcher
color 0A
echo.
echo  ==========================================
echo   SMART EVM -- Electronic Voting Machine
echo  ==========================================
echo.

:: Change to the folder this batch file lives in
cd /d "%~dp0"

:: ---- Check Python is installed ----------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo.
    echo  Please install Python 3.11 or newer from:
    echo    https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During installation, tick the checkbox
    echo  "Add Python to PATH" before clicking Install.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%V in ('python --version 2^>^&1') do set PYVER=%%V
echo  Python %PYVER% found.

:: ---- Create virtual environment (once) ---------------------------------
if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo  First run: creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo  [ERROR] Could not create virtual environment.
        pause
        exit /b 1
    )
    echo  Done.
)

:: ---- Activate venv ------------------------------------------------------
call .venv\Scripts\activate.bat

:: ---- Install / upgrade dependencies (once) ------------------------------
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  First run: installing dependencies (this may take a minute)...
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo.
        echo  [ERROR] Failed to install dependencies.
        echo  Try running this file as Administrator, or check your internet connection.
        pause
        exit /b 1
    )
    echo  Dependencies installed successfully.
)

:: ---- Launch the application ---------------------------------------------
echo.
echo  Starting SMART EVM...
echo.
python main.py

:: If the app closes with an error, keep the window open so you can read it
if errorlevel 1 (
    echo.
    echo  [ERROR] The application exited with an error.
    pause
)
