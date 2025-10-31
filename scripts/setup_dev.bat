@echo off
REM 🧪 Local Development Setup Script for TikTok Bot (Windows)
REM This script sets up the development environment on Windows

echo 🧪 TikTok Bot - Local Development Setup
echo =======================================

REM Check Python version
echo 🐍 Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% found

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file...
    copy .env.example .env
    
    echo.
    echo ⚙️ Please edit the .env file and add your Telegram bot token:
    echo    TELEGRAM_BOT_TOKEN=your_token_here
    echo.
    echo Get your token from @BotFather on Telegram
    echo.
    
    REM Try to open .env in default editor
    if exist "C:\Program Files\Microsoft VS Code\bin\code.cmd" (
        echo 🔧 Opening .env in VS Code...
        "C:\Program Files\Microsoft VS Code\bin\code.cmd" .env
    ) else (
        echo Please edit .env manually with your preferred editor
        notepad .env
    )
) else (
    echo ✅ .env file already exists
)

echo.
echo ✅ Setup complete!
echo.
echo 📋 Next steps:
echo 1. Edit .env file with your bot token (if not done already)
echo 2. Run the bot: python main.py
echo 3. Test with your bot on Telegram
echo.
echo 🛠️ Development commands:
echo   python main.py                    - Start the bot
echo   python tiktok_downloader.py      - Test downloader
echo.
echo 🎉 Happy coding!
pause