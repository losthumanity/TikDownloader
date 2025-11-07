@echo off
REM Configuration Check Script for TikTok Downloader Bot
REM This script checks if all required environment variables are properly set

echo.
echo ========================================
echo  TikTok Bot Configuration Checker
echo ========================================
echo.

REM Check if .env file exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo.
    echo Please create a .env file from .env.example:
    echo    copy .env.example .env
    echo.
    echo Then edit .env with your bot token.
    echo.
    pause
    exit /b 1
)

echo [OK] .env file found
echo.

REM Load and check TELEGRAM_BOT_TOKEN
findstr /C:"TELEGRAM_BOT_TOKEN=" .env > nul
if errorlevel 1 (
    echo [ERROR] TELEGRAM_BOT_TOKEN not found in .env
    echo.
    echo Please add your bot token to .env file:
    echo    TELEGRAM_BOT_TOKEN=your_bot_token_here
    echo.
    pause
    exit /b 1
)

REM Check if token is set to placeholder
findstr /C:"TELEGRAM_BOT_TOKEN=your_bot_token_here" .env > nul
if not errorlevel 1 (
    echo [WARNING] TELEGRAM_BOT_TOKEN is still set to placeholder!
    echo.
    echo Please replace 'your_bot_token_here' with your actual bot token from @BotFather
    echo.
    pause
    exit /b 1
)

echo [OK] TELEGRAM_BOT_TOKEN is configured
echo.

REM Check STORAGE_CHANNEL_ID (optional but recommended)
findstr /C:"STORAGE_CHANNEL_ID=" .env > nul
if errorlevel 1 (
    echo [INFO] STORAGE_CHANNEL_ID not configured
    echo       Large files ^(^>50MB^) won't be supported
    echo       See STORAGE_SETUP.md for setup instructions
    echo.
) else (
    REM Check if it's set to placeholder or empty
    findstr /C:"STORAGE_CHANNEL_ID=$" .env > nul
    if not errorlevel 1 (
        echo [INFO] STORAGE_CHANNEL_ID is empty
        echo       Large files ^(^>50MB^) won't be supported
        echo       See STORAGE_SETUP.md for setup instructions
        echo.
    ) else (
        echo [OK] STORAGE_CHANNEL_ID is configured
        echo.
    )
)

REM Check WEBHOOK_URL (optional)
findstr /C:"WEBHOOK_URL=" .env > nul
if errorlevel 1 (
    echo [INFO] WEBHOOK_URL not set - Bot will run in polling mode
    echo       ^(This is fine for development^)
    echo.
) else (
    findstr /C:"WEBHOOK_URL=$" .env > nul
    if not errorlevel 1 (
        echo [INFO] WEBHOOK_URL is empty - Bot will run in polling mode
        echo       ^(This is fine for development^)
        echo.
    ) else (
        echo [OK] WEBHOOK_URL is configured - Bot will run in webhook mode
        echo.
    )
)

REM Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.9+ from https://python.org
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed
python --version
echo.

REM Check if virtual environment exists
if not exist venv (
    echo [WARNING] Virtual environment not found
    echo.
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
    echo.
)

REM Check if dependencies are installed
if not exist venv\Scripts\activate.bat (
    echo [ERROR] Virtual environment is corrupted
    echo.
    echo Please delete the venv folder and run this script again
    echo.
    pause
    exit /b 1
)

echo [OK] Virtual environment exists
echo.

REM Activate virtual environment and check dependencies
call venv\Scripts\activate.bat

echo Checking dependencies...
pip show python-telegram-bot > nul 2>&1
if errorlevel 1 (
    echo [WARNING] Dependencies not installed
    echo.
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    echo.
    echo [OK] Dependencies installed
    echo.
) else (
    echo [OK] Dependencies are installed
    echo.
)

echo ========================================
echo  Configuration Check Complete
echo ========================================
echo.
echo All basic checks passed!
echo.
echo Next steps:
echo   1. If you haven't set up STORAGE_CHANNEL_ID, see STORAGE_SETUP.md
echo   2. Run the bot: python bot.py
echo   3. Send a TikTok link to test
echo.
echo For production deployment, see RENDER_SETUP.md
echo.

pause
