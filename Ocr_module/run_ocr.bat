@echo off
REM Starts the OCR Flask server using this project's own virtual environment.
REM Safe to run from any directory / any terminal — it locates itself first.
REM Note: this window stays open on error/exit (see the "pause" calls below)
REM so double-clicking this file never just flashes and disappears.

setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo.
    echo [ERROR] No virtual environment found at "%~dp0venv".
    echo         Run setup_ocr.bat first to create it and install dependencies.
    echo.
    pause
    exit /b 1
)

echo Starting PClaimAssist OCR service from %cd% ...
echo (Press CTRL+C to stop the server. This window must stay open while it runs.)
echo.
"venv\Scripts\python.exe" app.py
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" (
    echo [ERROR] The OCR server exited with code %EXIT_CODE% — see the output above for details.
) else (
    echo Server stopped.
)
pause

endlocal
