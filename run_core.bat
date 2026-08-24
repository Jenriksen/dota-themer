@echo off
REM Dota Themer - Run Core CLI (Windows)
REM This script runs the core theme suggestion CLI

echo Dota Themer - Theme Suggester
echo ==================================
echo.

set /p party_size="Enter party size (1-5), or press Enter for default (2): "

if "%party_size%"=="" (
    python core.py
) else (
    python core.py %party_size%
)

echo.
echo Press any key to exit.
pause
