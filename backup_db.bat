@echo off
REM ====================================================================
REM  Back up the PClaimAssist database
REM
REM  Writes a dump of pclaimassist_db (every table and row) to
REM  backups\pclaimassist_db_YYYY-MM-DD_HHMMSS.sql, using XAMPP's
REM  mysqldump, and keeps only the newest 14 dumps.
REM
REM  Next to each dump it saves the encryption key as
REM  backups\pclaimassist_db_YYYY-MM-DD_HHMMSS.key: the same key the app
REM  uses (DATA_ENCRYPTION_KEY from the environment or Ocr_module\.env,
REM  else the file Ocr_module\.data_key). Without it the encrypted patient
REM  details in a dump cannot be read. To restore it, copy the .key file
REM  to Ocr_module\.data_key (or put its text in DATA_ENCRYPTION_KEY).
REM  Keep both files private: backups\ is git-ignored.
REM
REM  The database must be running (start PClaimAssist.bat first).
REM  To restore a dump: phpMyAdmin > Import, or
REM    "%XAMPP_DIR%\mysql\bin\mysql.exe" -u root < backups\<file>.sql
REM
REM  Settings, first found wins: the environment, Ocr_module\.env, then
REM  XAMPP's defaults. XAMPP_DIR is where XAMPP is installed, as in
REM  PClaimAssist.bat.
REM ====================================================================

setlocal
cd /d "%~dp0"

REM -- Settings ---------------------------------------------------------
if exist "Ocr_module\.env" (
    for /f "usebackq eol=# tokens=1,* delims==" %%a in ("Ocr_module\.env") do (
        if /I "%%a"=="DB_HOST"     if not defined DB_HOST     set "DB_HOST=%%b"
        if /I "%%a"=="DB_PORT"     if not defined DB_PORT     set "DB_PORT=%%b"
        if /I "%%a"=="DB_NAME"     if not defined DB_NAME     set "DB_NAME=%%b"
        if /I "%%a"=="DB_USER"     if not defined DB_USER     set "DB_USER=%%b"
        if /I "%%a"=="DB_PASSWORD" if not defined DB_PASSWORD set "DB_PASSWORD=%%b"
        if /I "%%a"=="DATA_ENCRYPTION_KEY" if not defined DATA_ENCRYPTION_KEY set "DATA_ENCRYPTION_KEY=%%b"
    )
)
if not defined XAMPP_DIR   set "XAMPP_DIR=C:\xampp"
if not defined DB_HOST     set "DB_HOST=127.0.0.1"
if not defined DB_PORT     set "DB_PORT=3306"
if not defined DB_NAME     set "DB_NAME=pclaimassist_db"
if not defined DB_USER     set "DB_USER=root"
set "KEEP=14"
set "BACKUP_DIR=%~dp0backups"
set "DUMP=%XAMPP_DIR%\mysql\bin\mysqldump.exe"

if not exist "%DUMP%" (
    echo   [ERROR] mysqldump was not found at "%DUMP%".
    echo           Install XAMPP, or set XAMPP_DIR to where it is installed.
    exit /b 1
)
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM -- Dump -------------------------------------------------------------
for /f %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HHmmss"') do set "STAMP=%%t"
set "OUT=%BACKUP_DIR%\%DB_NAME%_%STAMP%.sql"

REM  The password goes in MYSQL_PWD, not on the command line.
if defined DB_PASSWORD set "MYSQL_PWD=%DB_PASSWORD%"
"%DUMP%" --host=%DB_HOST% --port=%DB_PORT% --user=%DB_USER% --single-transaction --routines --triggers --databases %DB_NAME% --result-file="%OUT%"
if errorlevel 1 (
    echo   [ERROR] The backup failed - is the database running?
    if exist "%OUT%" del "%OUT%"
    exit /b 1
)
echo   Backup saved: %OUT%

REM -- Encryption key, next to the dump ------------------------------------
REM  Same order as the app (Ocr_module\field_crypto.py): DATA_ENCRYPTION_KEY
REM  first, else Ocr_module\.data_key.
set "KEYOUT=%BACKUP_DIR%\%DB_NAME%_%STAMP%.key"
if defined DATA_ENCRYPTION_KEY (
    > "%KEYOUT%" echo %DATA_ENCRYPTION_KEY%
) else if exist "Ocr_module\.data_key" (
    copy /y "Ocr_module\.data_key" "%KEYOUT%" >nul
)
if exist "%KEYOUT%" (
    echo   Key saved:    %KEYOUT%
) else (
    echo   [WARNING] The encryption key was NOT saved with this backup.
    echo             Look for Ocr_module\.data_key or DATA_ENCRYPTION_KEY in Ocr_module\.env.
)

REM -- Keep only the newest %KEEP% ---------------------------------------
REM  An old dump's key goes with it; a key left without its dump is
REM  removed by the same newest-%KEEP% rule.
for /f "skip=%KEEP% delims=" %%f in ('dir /b /o-d "%BACKUP_DIR%\%DB_NAME%_*.sql" 2^>nul') do (
    del "%BACKUP_DIR%\%%f"
    if exist "%BACKUP_DIR%\%%~nf.key" del "%BACKUP_DIR%\%%~nf.key"
    echo   Removed old backup: %%f
)
for /f "skip=%KEEP% delims=" %%f in ('dir /b /o-d "%BACKUP_DIR%\%DB_NAME%_*.key" 2^>nul') do (
    del "%BACKUP_DIR%\%%f"
)

endlocal
exit /b 0
