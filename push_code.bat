@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0push_code.ps1" %*
set ERR=%ERRORLEVEL%
if not "%ERR%"=="0" exit /b %ERR%
endlocal
exit /b 0
