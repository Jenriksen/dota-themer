@echo off
REM Dota Themer - Run Discord Bot (Windows)
REM This script starts the Discord bot with your token

REM Check if DISCORD_TOKEN is set
if "%DISCORD_TOKEN%"=="" (
    echo ERROR: DISCORD_TOKEN environment variable is not set.
    echo Please set it before running this script:
    echo   set DISCORD_TOKEN=your-bot-token-here
    echo.
    echo Or create a .env file with your token.
    pause
    exit /b 1
)

echo Starting Dota Themer Discord Bot...
echo ==================================
echo Token: %DISCORD_TOKEN% (hidden for security)
echo.

python bot.py

echo.
echo Bot stopped. Press any key to exit.
pause
