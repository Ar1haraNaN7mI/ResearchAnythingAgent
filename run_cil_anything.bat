@echo off
setlocal
cd /d "%~dp0"
python "cil_anything.py" %*
if errorlevel 1 (
    echo CIL Anything failed.
    pause
)
endlocal
