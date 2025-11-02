"""
Main launcher for the TikTok Downloader Bot
Handles both the Telegram bot and health server for deployment
"""

import os
import logging
import threading
import time
import signal
import sys
import asyncio
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
    """Run the health check server with proper port binding"""
    try:
        from health_server import app
        # Render uses PORT 10000, Railway uses dynamic port
        port = int(os.getenv('PORT', 10000))
        
        logger.info(f"🏥 Starting health server on port {port}")
        
        # Always use Flask for simplicity and reliability
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
        
    except Exception as e:
        logger.error(f"❌ Health server failed to start: {e}")
        raise

def run_telegram_bot():
    """Run the Telegram bot with retry mechanism"""
    max_retries = 5
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            from bot import TikTokBot
            bot = TikTokBot()
            
            logger.info(f"🤖 Starting Telegram bot (attempt {attempt + 1}/{max_retries})")
            bot.run()
            
            # If we reach here, the bot ran successfully
            break
            
        except Exception as e:
            logger.error(f"❌ Telegram bot failed on attempt {attempt + 1}: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("💥 Max retries reached. Bot will be restarted by platform.")
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

    # Detect production environment
    is_production = any([
        os.getenv('RENDER'),
        os.getenv('RAILWAY_ENVIRONMENT'), 
        os.getenv('DYNO'),  # Heroku
        os.getenv('WEBHOOK_URL')
    ])
    
    webhook_url = os.getenv('WEBHOOK_URL') or os.getenv('RENDER_EXTERNAL_URL')

    if is_production:
        # Production mode - Health server in main thread, bot in background
        logger.info("🌐 Production mode detected - Starting webhook server...")
        logger.info(f"🔗 Webhook URL: {webhook_url}")
        
        # Start keep-alive service for Render free tier
        if os.getenv('RENDER'):
            try:
                from keepalive import start_keepalive
                start_keepalive()
                logger.info("⏰ Keep-alive service started (prevents free tier sleep)")
            except Exception as e:
                logger.warning(f"Keep-alive failed to start: {e}")
        
        # Start health server in background thread
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        
        # Small delay to let health server start
        time.sleep(2)
        
        # Bot runs in main thread (better for asyncio event loop)
        run_telegram_bot()
    else:
        # Development mode - Bot in main thread, health server in background
        logger.info("� Development mode - Starting polling bot...")
        
        # Start health server in background for local testing
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        
        # Bot runs in main thread
        run_telegram_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        raise