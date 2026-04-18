@echo off
:: AURA install script — Windows
:: Run once after cloning: install.bat

echo.
echo   ██████╗ ██╗   ██╗██████╗  █████╗
echo  ██╔══██╗██║   ██║██╔══██╗██╔══██╗
echo  ███████║██║   ██║██████╔╝███████║
echo  ██╔══██║██║   ██║██╔══██╗██╔══██║
echo  ██║  ██║╚██████╔╝██║  ██║██║  ██║
echo  ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
echo.
echo   Installing AURA for Windows...
echo.

:: ── Python version check ────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo   X Python not found. Install Python 3.10+ from https://python.org
    exit /b 1
)
echo   + Python found

:: ── Create virtual environment ───────────────────────────────────────────────
if not exist ".venv" (
    python -m venv .venv
    echo   + Virtual environment created ^(.venv^)
) else (
    echo   + Virtual environment already exists
)

:: Activate venv
call .venv\Scripts\activate.bat

:: ── Install Python dependencies ──────────────────────────────────────────────
pip install -e . --quiet
if errorlevel 1 (
    echo   X Failed to install AURA. Check the error above.
    exit /b 1
)
echo   + AURA package installed

:: ── Note about PyAudio on Windows ────────────────────────────────────────────
echo.
echo   NOTE: If voice ^(/voice^) fails, install PyAudio manually:
echo     pip install pipwin
echo     pipwin install pyaudio
echo.

:: ── Playwright browsers ────────────────────────────────────────────────────
echo   Installing Playwright browsers ^(for browser tools^)...
playwright install chromium
if errorlevel 1 (
    echo   ^ Playwright install skipped ^(browser tools may not work^)
) else (
    echo   + Playwright chromium installed
)

:: ── .env setup ────────────────────────────────────────────────────────────────
if not exist ".env" (
    copy .env.example .env >nul
    echo   + .env created from template
    echo.
    echo   ^ ACTION REQUIRED:
    echo      Edit .env and fill in your API endpoint URL and key.
) else (
    echo   + .env already exists
)

echo.
echo   + Installation complete.
echo.
echo   Quick start:
echo     .venv\Scripts\activate
echo     aura run
echo.
