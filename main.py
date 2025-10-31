"""
Main launcher for the TikTok Downloader Bot
Handles both the Telegram bot and health server for deployment
"""

import os
import logging
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if not os.getenv('DEBUG') else logging.DEBUG
)
logger = logging.getLogger(__name__)

def run_health_server():
    """Run the health check server"""
    try:
        from health_server import app
        port = int(os.getenv('PORT', 8443))
        
        # Use gunicorn for production, Flask dev server for local
        if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER') or os.getenv('DYNO'):
            # Production deployment
            import gunicorn.app.wsgiapp as wsgi
            wsgi.run()
        else:
            # Development
            app.run(host='0.0.0.0', port=port, debug=False)
            
    except Exception as e:
        logger.error(f"Health server failed to start: {e}")

def run_telegram_bot():
    """Run the Telegram bot"""
    try:
        # Small delay to ensure health server starts first
        time.sleep(2)
        
        from bot import TikTokBot
        bot = TikTokBot()
        bot.run()
        
    except Exception as e:
        logger.error(f"Telegram bot failed to start: {e}")
        raise

def main():
    """Main entry point"""
    logger.info("🚀 Starting TikTok Downloader Bot...")
    
    # Check if we have the required token
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        logger.error("❌ TELEGRAM_BOT_TOKEN is required!")
        print("\n" + "="*50)
        print("❌ TELEGRAM_BOT_TOKEN is required!")
        print("Please set it in your .env file or environment variables")
        print("Get your token from @BotFather on Telegram")
        print("="*50 + "\n")
        return
    
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if webhook_url:
        # Production mode with webhook
        logger.info("🌐 Running in webhook mode...")
        
        # Start health server in background thread
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        
        # Start Telegram bot
        run_telegram_bot()
    else:
        # Development mode with polling
        logger.info("🔄 Running in polling mode...")
        
        # Start health server in background thread for local development
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        
        # Start Telegram bot
        run_telegram_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        raise