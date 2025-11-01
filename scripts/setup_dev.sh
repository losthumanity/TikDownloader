#!/bin/bash

# 🧪 Local Development Setup Script for TikTok Bot
# This script sets up the development environment

echo "🧪 TikTok Bot - Local Development Setup"
echo "======================================="

# Check Python version
echo "🐍 Checking Python version..."
if ! command -v python &> /dev/null; then
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python not found! Please install Python 3.8+"
        exit 1
    else
        PYTHON_CMD="python3"
    fi
else
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
echo "✅ Python $PYTHON_VERSION found"

# Check if Python version is >= 3.8
if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Python 3.8+ is required!"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows (Git Bash)
    source venv/Scripts/activate
else
    # Linux/macOS
    source venv/bin/activate
fi

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env

    echo ""
    echo "⚙️ Please edit the .env file and add your Telegram bot token:"
    echo "   TELEGRAM_BOT_TOKEN=your_token_here"
    echo ""
    echo "Get your token from @BotFather on Telegram"
    echo ""

    # Try to open .env in default editor
    if command -v code &> /dev/null; then
        echo "🔧 Opening .env in VS Code..."
        code .env
    elif command -v nano &> /dev/null; then
        echo "🔧 Opening .env in nano..."
        nano .env
    else
        echo "Please edit .env manually with your preferred editor"
    fi
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your bot token (if not done already)"
echo "2. Run the bot: python main.py"
echo "3. Test with your bot on Telegram"
echo ""
echo "🛠️ Development commands:"
echo "  python main.py          - Start the bot"
echo "  python tiktok_downloader.py - Test downloader"
echo ""
echo "🎉 Happy coding!"