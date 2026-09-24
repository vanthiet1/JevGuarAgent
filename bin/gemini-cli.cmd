@echo off
setlocal
set "SHIM_DIR=%~dp0"
python "%SHIM_DIR%..\guar.py" wrap gemini-cli %*
exit /b %ERRORLEVEL%
