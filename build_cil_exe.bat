@echo off
setlocal
cd /d "%~dp0"
python -m pip install pyinstaller
if errorlevel 1 (
    echo Failed to install pyinstaller.
    pause
    exit /b 1
)
pyinstaller --noconfirm --onefile --name CILAnything "cil_anything.py"
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)
echo Build complete: dist\CILAnything.exe
pause
endlocal
