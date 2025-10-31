#!/bin/bash

# 🚀 Railway Deployment Script for TikTok Bot
# This script helps you deploy the TikTok bot to Railway

echo "🚀 TikTok Bot - Railway Deployment Script"
echo "========================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found!"
    echo "📥 Installing Railway CLI..."
    
    # Detect OS and install accordingly
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        curl -fsSL https://railway.app/install.sh | sh
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://railway.app/install.sh | sh
    else
        echo "Please install Railway CLI manually: https://docs.railway.app/develop/cli"
        exit 1
    fi
fi

echo "✅ Railway CLI found!"

# Login to Railway
echo "🔑 Logging in to Railway..."
railway login

# Create new project
echo "📦 Creating new Railway project..."
railway new

# Set up environment variables
echo "⚙️ Setting up environment variables..."
echo ""
echo "Please enter your Telegram bot token (from @BotFather):"
read -r BOT_TOKEN

if [ -z "$BOT_TOKEN" ]; then
    echo "❌ Bot token is required!"
    exit 1
fi

# Set environment variables
railway variables set TELEGRAM_BOT_TOKEN="$BOT_TOKEN"

# Optional: Set webhook URL (will be auto-configured by Railway)
echo ""
echo "🌐 Railway will automatically set up the webhook URL."
echo "If you need a custom domain, you can set it later in the Railway dashboard."

# Deploy
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Check your deployment status: railway status"
echo "2. View logs: railway logs"
echo "3. Open dashboard: railway open"
echo "4. Test your bot on Telegram!"
echo ""
echo "🎉 Your TikTok downloader bot should now be running!"
echo "🔗 Railway Dashboard: https://railway.app/dashboard"