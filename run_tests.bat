@echo off
REM Dota Themer - Run All Tests (Windows)
REM This script runs all unit tests and displays the results

echo Running all Dota Themer tests...
echo ==================================
echo.

python -m unittest discover -v

echo.
echo ==================================
echo Tests complete. Press any key to exit.
pause
