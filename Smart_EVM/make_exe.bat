@echo off
title Build launch.exe
color 0B
echo.
echo  ==========================================
echo    SMART EVM  --  Build launch.exe
echo  ==========================================
echo.

cd /d "%~dp0"

:: ── Activate venv ─────────────────────────────────────────────────
if not exist ".venv\Scripts\activate.bat" (
    echo  [ERROR] Virtual environment not found.
    echo  Please run SETUP.bat first, then try again.
    echo.
    pause & exit /b 1
)
call .venv\Scripts\activate.bat

:: ── Install PyInstaller if missing ────────────────────────────────
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo  Installing PyInstaller...
    pip install pyinstaller --quiet --disable-pip-version-check
)

:: ── Delegate to Python (handles spaces/special chars in path) ─────
python build_exe.py
if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed. Check the messages above.
    pause & exit /b 1
)

:: ── Done ──────────────────────────────────────────────────────────
echo.
echo  ==========================================
echo    launch.exe built successfully!
echo.
if exist "%~dp0icon.ico" (
    echo    Icon used: icon.ico
) else (
    echo    No icon  (add icon.ico and re-run to set one^)
)
echo.
echo    Double-click launch.exe to start SMART EVM
echo    with no CMD window.
echo  ==========================================
echo.
pause
