#!/bin/bash

# Configuration Check Script for TikTok Downloader Bot
# This script checks if all required environment variables are properly set

echo ""
echo "========================================"
echo "  TikTok Bot Configuration Checker"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[ERROR] .env file not found!"
    echo ""
    echo "Please create a .env file from .env.example:"
    echo "   cp .env.example .env"
    echo ""
    echo "Then edit .env with your bot token."
    echo ""
    exit 1
fi

echo "[OK] .env file found"
echo ""

# Check TELEGRAM_BOT_TOKEN
if ! grep -q "TELEGRAM_BOT_TOKEN=" .env; then
    echo "[ERROR] TELEGRAM_BOT_TOKEN not found in .env"
    echo ""
    echo "Please add your bot token to .env file:"
    echo "   TELEGRAM_BOT_TOKEN=your_bot_token_here"
    echo ""
    exit 1
fi

# Check if token is set to placeholder
if grep -q "TELEGRAM_BOT_TOKEN=your_bot_token_here" .env; then
    echo "[WARNING] TELEGRAM_BOT_TOKEN is still set to placeholder!"
    echo ""
    echo "Please replace 'your_bot_token_here' with your actual bot token from @BotFather"
    echo ""
    exit 1
fi

echo "[OK] TELEGRAM_BOT_TOKEN is configured"
echo ""

# Check STORAGE_CHANNEL_ID (optional but recommended)
if ! grep -q "STORAGE_CHANNEL_ID=" .env; then
    echo "[INFO] STORAGE_CHANNEL_ID not configured"
    echo "       Large files (>50MB) won't be supported"
    echo "       See STORAGE_SETUP.md for setup instructions"
    echo ""
else
    # Check if it's empty
    if grep -q "STORAGE_CHANNEL_ID=$" .env || grep -q "STORAGE_CHANNEL_ID= *$" .env; then
        echo "[INFO] STORAGE_CHANNEL_ID is empty"
        echo "       Large files (>50MB) won't be supported"
        echo "       See STORAGE_SETUP.md for setup instructions"
        echo ""
    else
        echo "[OK] STORAGE_CHANNEL_ID is configured"
        echo ""
    fi
fi

# Check WEBHOOK_URL (optional)
if ! grep -q "WEBHOOK_URL=" .env; then
    echo "[INFO] WEBHOOK_URL not set - Bot will run in polling mode"
    echo "       (This is fine for development)"
    echo ""
else
    if grep -q "WEBHOOK_URL=$" .env || grep -q "WEBHOOK_URL= *$" .env; then
        echo "[INFO] WEBHOOK_URL is empty - Bot will run in polling mode"
        echo "       (This is fine for development)"
        echo ""
    else
        echo "[OK] WEBHOOK_URL is configured - Bot will run in webhook mode"
        echo ""
    fi
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed!"
    echo ""
    echo "Please install Python 3.9+ from your package manager or https://python.org"
    echo ""
    exit 1
fi

echo "[OK] Python is installed"
python3 --version
echo ""

# Check if virtual environment exists
if [ ! -d venv ]; then
    echo "[WARNING] Virtual environment not found"
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "[OK] Virtual environment created"
    echo ""
fi

echo "[OK] Virtual environment exists"
echo ""

# Activate virtual environment and check dependencies
source venv/bin/activate

echo "Checking dependencies..."
if ! pip show python-telegram-bot &> /dev/null; then
    echo "[WARNING] Dependencies not installed"
    echo ""
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    echo ""
    echo "[OK] Dependencies installed"
    echo ""
else
    echo "[OK] Dependencies are installed"
    echo ""
fi

echo "========================================"
echo "  Configuration Check Complete"
echo "========================================"
echo ""
echo "All basic checks passed!"
echo ""
echo "Next steps:"
echo "  1. If you haven't set up STORAGE_CHANNEL_ID, see STORAGE_SETUP.md"
echo "  2. Run the bot: python3 bot.py"
echo "  3. Send a TikTok link to test"
echo ""
echo "For production deployment, see RENDER_SETUP.md"
echo ""
