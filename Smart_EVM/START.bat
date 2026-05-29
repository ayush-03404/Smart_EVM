@echo off
title SMART EVM Launcher
color 0A
echo.
echo  ==========================================
echo    SMART EVM  --  Electronic Voting Machine
echo  ==========================================
echo.

cd /d "%~dp0"

:: ── Step 1: Check Python ──────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo.
    echo  Please run SETUP.bat first — it will install Python automatically.
    echo.
    pause
    exit /b 1
)

:: ── Step 2: Create venv on first run ─────────────────────────────
if not exist ".venv\Scripts\activate.bat" (
    echo  First run: creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo  [ERROR] Could not create virtual environment.
        echo  Try running SETUP.bat instead.
        pause
        exit /b 1
    )
    echo  Done.
    echo.
)

:: ── Step 3: Activate venv ────────────────────────────────────────
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo  [ERROR] Could not activate virtual environment.
    echo  Deleting broken .venv and retrying — please wait...
    rmdir /s /q .venv
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

:: ── Step 4: Install dependencies if missing ───────────────────────
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo  Installing dependencies (this takes about 1 minute on first run)...
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo.
        echo  [ERROR] Failed to install dependencies.
        echo  Check your internet connection and try again.
        pause
        exit /b 1
    )
    echo  Dependencies installed.
    echo.
)

:: ── Step 5: Launch app with pythonw (no console window) ──────────
echo  Starting SMART EVM...
echo  (This window will close automatically once the app opens)
echo.

:: Use pythonw so no second CMD window appears during app runtime
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" main.py
) else (
    :: Fallback: run with python and keep this window as the only console
    python main.py
    if errorlevel 1 (
        echo.
        echo  [ERROR] The application exited with an error.
        echo  Go to the Debugging Log page inside the app for details,
        echo  or open a Command Prompt here and run:  python main.py
        pause
    )
    exit /b 0
)

:: Give pythonw a moment to start, then close this launcher window
timeout /t 3 /nobreak >nul
exit
