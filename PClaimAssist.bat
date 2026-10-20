@echo off
REM ====================================================================
REM  Start PClaimAssist
REM
REM  One double-click for clinic staff. Starts the database and the
REM  application if they are not already running, waits until the system
REM  answers, then opens it in the browser.
REM
REM  Safe to run when things are already started - it checks first and
REM  skips whatever is already up, so staff can click it any time.
REM
REM  PClaimAssist.bat /background  - the same, without opening the browser
REM  (used when Windows starts it at sign-in, see tools\autostart.ps1).
REM ====================================================================

setlocal
cd /d "%~dp0"

set "BACKGROUND="
if /I "%~1"=="/background" set "BACKGROUND=1"

set "XAMPP_DIR=C:\xampp"
set "APP_URL=http://127.0.0.1:5000/"

REM Flask's auto-reloader is a development convenience: it spawns extra
REM processes and restarts on file changes. A clinic install wants neither.
set "OCR_DEBUG=false"

echo.
echo   Starting PClaimAssist. Please wait...
echo.

REM ── 1. Database ────────────────────────────────────────────────────
tasklist /FI "IMAGENAME eq mysqld.exe" 2>nul | find /I "mysqld.exe" >nul
if errorlevel 1 (
    if not exist "%XAMPP_DIR%\mysql\bin\mysqld.exe" (
        echo   [ERROR] MariaDB was not found at "%XAMPP_DIR%\mysql".
        echo           Install XAMPP, or edit XAMPP_DIR at the top of this file.
        echo.
        pause
        exit /b 1
    )
    echo   Starting the database...
    start "PClaimAssist database" /MIN "%XAMPP_DIR%\mysql\bin\mysqld.exe" --defaults-file="%XAMPP_DIR%\mysql\bin\my.ini" --standalone
) else (
    echo   Database already running.
)

REM ── 2. Application ─────────────────────────────────────────────────
if not exist "Ocr_module\venv\Scripts\python.exe" (
    echo   [ERROR] Python environment missing.
    echo           Run Ocr_module\setup_ocr.bat once, then try again.
    echo.
    pause
    exit /b 1
)

curl -s -o nul --max-time 3 "%APP_URL%db_health"
if errorlevel 1 (
    echo   Starting the application...
    start "PClaimAssist" /MIN /D "%~dp0Ocr_module" "%~dp0Ocr_module\venv\Scripts\python.exe" app.py
) else (
    echo   Application already running.
)

REM ── 3. Wait for it to answer, then open the browser ────────────────
REM  First start loads the OCR engine, which takes a little while.
echo   Waiting for the system to be ready...
set /a TRIES=0
:waitloop
set /a TRIES+=1
curl -s -o nul --max-time 3 "%APP_URL%db_health"
if not errorlevel 1 goto ready
if %TRIES% GEQ 40 goto timeout
ping -n 3 127.0.0.1 >nul
goto waitloop

:ready
if defined BACKGROUND exit /b 0
echo.
echo   PClaimAssist is ready. Opening it now.
echo.
echo   Address: %APP_URL%
echo.
echo   Leave the two small windows in the taskbar running while you work.
echo   Closing them shuts PClaimAssist down.
echo.
start "" "%APP_URL%"
timeout /t 8 >nul
exit /b 0

:timeout
echo.
echo   [ERROR] PClaimAssist did not start in time.
echo.
echo   Check the minimised "PClaimAssist" window in the taskbar for the
echo   reason, then show it to whoever set this system up.
echo.
pause
exit /b 1
