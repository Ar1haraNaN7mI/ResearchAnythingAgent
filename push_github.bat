@echo off
setlocal
cd /d "%~dp0"
echo Pushing to origin main ...
git push -u origin main
if errorlevel 1 (
    echo.
    echo If the remote already has commits, try:
    echo   git pull origin main --allow-unrelated-histories
    echo   git push -u origin main
    pause
    exit /b 1
)
echo Done.
pause
endlocal
