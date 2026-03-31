@echo off
REM Run vendored Scrapling CLI from repo root (cwd = parent of research_agent).
set "HERE=%~dp0"
cd /d "%HERE%.."
python "%HERE%scrapling_entry.py" %*
