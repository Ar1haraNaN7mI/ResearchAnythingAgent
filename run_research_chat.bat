@echo off
setlocal
cd /d "%~dp0"
python -m pip install -r research_agent\requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)
python -m research_agent
if errorlevel 1 (
    echo Server failed.
    pause
)
endlocal
