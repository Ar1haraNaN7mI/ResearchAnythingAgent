@echo off
setlocal
cd /d "%~dp0"
git config http.version HTTP/1.1
git config http.postBuffer 524288000
echo Pushing with HTTP/1.1 and larger buffer ...
git push -u origin main
if errorlevel 1 (
    echo.
    echo See GITHUB_PUSH.md for SSH and proxy options.
    pause
    exit /b 1
)
echo Done.
pause
endlocal
