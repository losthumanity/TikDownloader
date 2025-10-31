@echo off
REM 🚀 Railway Deployment Script for TikTok Bot (Windows)
REM This script helps you deploy the TikTok bot to Railway on Windows

echo 🚀 TikTok Bot - Railway Deployment Script
echo =========================================

REM Check if Railway CLI is installed
railway --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Railway CLI not found!
    echo 📥 Please install Railway CLI from: https://docs.railway.app/develop/cli
    echo After installation, run this script again.
    pause
    exit /b 1
)

echo ✅ Railway CLI found!

REM Login to Railway
echo 🔑 Logging in to Railway...
railway login

REM Create new project
echo 📦 Creating new Railway project...
railway new

REM Set up environment variables
echo ⚙️ Setting up environment variables...
echo.
set /p BOT_TOKEN="Please enter your Telegram bot token (from @BotFather): "

if "%BOT_TOKEN%"=="" (
    echo ❌ Bot token is required!
    pause
    exit /b 1
)

REM Set environment variables
railway variables set TELEGRAM_BOT_TOKEN=%BOT_TOKEN%

echo.
echo 🌐 Railway will automatically set up the webhook URL.
echo If you need a custom domain, you can set it later in the Railway dashboard.

REM Deploy
echo 🚀 Deploying to Railway...
railway up

echo.
echo ✅ Deployment complete!
echo.
echo 📋 Next steps:
echo 1. Check your deployment status: railway status
echo 2. View logs: railway logs
echo 3. Open dashboard: railway open
echo 4. Test your bot on Telegram!
echo.
echo 🎉 Your TikTok downloader bot should now be running!
echo 🔗 Railway Dashboard: https://railway.app/dashboard
pause