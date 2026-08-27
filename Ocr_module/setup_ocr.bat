@echo off
REM One-time environment setup for a fresh clone of this project.
REM Creates a local venv (isolated — nothing installed globally) and installs
REM all pinned dependencies into it. Run this once, then use run_ocr.bat.
REM Note: this window stays open on error/finish (see "pause" below) so
REM double-clicking this file never just flashes and disappears.

setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] Python was not found on PATH. Install Python 3.12 first:
    echo         https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

if exist "venv\Scripts\python.exe" (
    echo A virtual environment already exists at "%~dp0venv".
    echo Delete that folder first if you want to rebuild it from scratch.
    goto :install
)

echo Creating virtual environment in "%~dp0venv" ...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create the virtual environment.
    pause
    exit /b 1
)

:install
echo Installing dependencies from requirements.txt ...
echo (This downloads PaddleOCR/PaddlePaddle — it can take several minutes.)
"venv\Scripts\python.exe" -m pip install --upgrade pip
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed. See the output above.
    pause
    exit /b 1
)

echo.
echo Setup complete. Start the server with run_ocr.bat.
pause
endlocal
