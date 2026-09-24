@echo off
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

echo [JOG] May tinh chua co Python. Dang tu dong cai dat Python 3...
where winget >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [JOG] Dang cai dat Python qua winget...
    winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
) else (
    echo [JOG] Dang tai bo cai Python tu trang chu python.org...
    powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' -OutFile '%TEMP%\python_setup.exe'; Start-Process '%TEMP%\python_setup.exe' -ArgumentList '/quiet InstallAllUsers=0 PrependPath=1' -Wait; Remove-Item '%TEMP%\python_setup.exe'"
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [JOG] Da cai dat Python thanh cong! Tiep tuc khoi dong JOG...
    python "%SCRIPT_DIR%guar.py" %*
    exit /b %ERRORLEVEL%
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [JOG] Da cai dat Python thanh cong! Tiep tuc khoi dong JOG...
    py "%SCRIPT_DIR%guar.py" %*
    exit /b %ERRORLEVEL%
)

echo [LOI] Cai dat Python hoan tat nhung can mo lai Terminal de nhan PATH.
echo [JOG] Vui long mo lai Terminal va chay lai '.\guar active'.
exit /b 1
