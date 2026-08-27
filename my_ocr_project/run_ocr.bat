@echo off
REM Starts the OCR Flask server using this project's own virtual environment.
REM Safe to run from any directory / any terminal — it locates itself first.

setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo.
    echo [ERROR] No virtual environment found at "%~dp0venv".
    echo         Run setup_ocr.bat first to create it and install dependencies.
    echo.
    exit /b 1
)

echo Starting PClaimAssist OCR service from %cd% ...
"venv\Scripts\python.exe" app.py

endlocal
