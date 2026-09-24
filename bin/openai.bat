@echo off
call "%~dp0openai.cmd" %*
exit /b %ERRORLEVEL%
