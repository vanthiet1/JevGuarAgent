@echo off
rem =============================================================================
rem guar.bat - Alias cho guar.cmd tren Windows
rem =============================================================================
call "%~dp0guar.cmd" %*
exit /b %ERRORLEVEL%
