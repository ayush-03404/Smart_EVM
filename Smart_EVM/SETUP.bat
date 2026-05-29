@echo off
title SMART EVM -- Setup
color 0B
echo.
echo  ==========================================
echo    SMART EVM  --  First-Time Setup
echo  ==========================================
echo.
echo  This will install Python (if missing) and all required packages.
echo  An internet connection is required.
echo.

cd /d "%~dp0"

:: ── Step 1: Check for Python ──────────────────────────────────────
python --version >nul 2>&1
if NOT errorlevel 1 goto :python_found

echo  Python not found on this PC.
echo  Attempting automatic installation...
echo.

:: Try winget (Windows 10 1709+ and all Windows 11)
winget --version >nul 2>&1
if NOT errorlevel 1 (
    echo  Installing Python 3.11 via Windows Package Manager...
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    if NOT errorlevel 1 (
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
        goto :check_python_again
    )
    echo  winget failed — trying direct download...
)

:: Fallback: PowerShell download
echo  Downloading Python 3.11 from python.org...
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_setup.exe' -UseBasicParsing"
if NOT exist "%TEMP%\python_setup.exe" (
    echo.
    echo  [ERROR] Download failed. Please install Python 3.11 manually from:
    echo    https://www.python.org/downloads/
    echo  IMPORTANT: tick "Add Python to PATH" during installation.
    pause & exit /b 1
)
echo  Installing Python silently...
"%TEMP%\python_setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_test=0
del "%TEMP%\python_setup.exe" >nul 2>&1
set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"

:check_python_again
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Python still not found after installation.
    echo  Please restart this script or install manually from python.org.
    pause & exit /b 1
)

:python_found
for /f "tokens=2 delims= " %%V in ('python --version 2^>^&1') do set PYVER=%%V
echo  Python %PYVER% found.
echo.

:: ── Step 2: Remove old venv only if it looks broken ──────────────
if exist ".venv\Scripts\python.exe" (
    echo  Existing environment found — checking health...
    .venv\Scripts\python.exe -c "import PyQt6, websockets, openpyxl, matplotlib" >nul 2>&1
    if NOT errorlevel 1 (
        echo  All packages already installed. Nothing to do.
        echo.
        goto :done
    )
    echo  Some packages are missing — rebuilding environment...
    rmdir /s /q ".venv"
) else (
    if exist ".venv" rmdir /s /q ".venv"
)

:: ── Step 3: Create fresh venv ─────────────────────────────────────
echo  Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo  [ERROR] Could not create virtual environment.
    pause & exit /b 1
)
call .venv\Scripts\activate.bat

:: ── Step 4: Install packages (no pip upgrade — saves ~15 seconds) ─
echo  Installing packages: PyQt6, websockets, openpyxl, matplotlib...
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo  [ERROR] Package installation failed.
    echo  Check your internet connection and run this script again.
    pause & exit /b 1
)

:done
echo.
echo  ==========================================
echo    Setup complete!
echo.
echo    To launch the app:
echo      Double-click  launch.vbs    (no CMD window -- recommended)
echo      Double-click  START.bat     (brief green window, then app opens)
echo      Double-click  launch.pyw    (silent, requires Python association)
echo.
echo    To build launch.exe (optional, once):
echo      Double-click  make_exe.bat
echo  ==========================================
echo.
pause
