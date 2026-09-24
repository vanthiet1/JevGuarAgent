@echo off
rem =============================================================================
rem guar.cmd - Trình khởi chạy nhanh JevGuarAgent trên Windows (Command Prompt)
rem =============================================================================
setlocal
set "SCRIPT_DIR=%~dp0"

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python "%SCRIPT_DIR%guar.py" %*
    exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py "%SCRIPT_DIR%guar.py" %*
    exit /b %ERRORLEVEL%
)

where python3 >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python3 "%SCRIPT_DIR%guar.py" %*
    exit /b %ERRORLEVEL%
)

echo [LOI] Khong tim thay Python tren he thong! Vui long cai dat Python 3 va them vao PATH.
exit /b 1
