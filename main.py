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
    """Run the Telegram bot"""
    try:
        from bot import TikTokBot
        bot = TikTokBot()

        logger.info("🤖 Starting Telegram bot...")
        bot.run()

    except Exception as e:
        logger.error(f"❌ Telegram bot failed: {e}")
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
        # Production mode - Initialize bot and run Flask server
        logger.info("🌐 Production mode detected - Starting Flask server with webhook...")
        logger.info(f"🔗 Webhook URL: {webhook_url}")

        # Initialize bot and store globally for Flask webhook handling
        from bot import TikTokBot
        bot_instance = TikTokBot()
        
        # Configure webhook and store bot reference
        import sys
        import bot
        from telegram.ext import Application
        app = Application.builder().token(bot_instance.token).build()
        bot_instance._add_handlers(app)
        
        # Store the application globally for Flask to access
        bot.telegram_app = app
        sys.modules['bot'].telegram_app = app

        # Set webhook URL
        webhook_path = f"webhook/{bot_instance.token}"
        full_webhook_url = f"{webhook_url}/{webhook_path}" if webhook_url else None

        if full_webhook_url:
            # Configure webhook asynchronously
            import asyncio
            async def setup_webhook():
                await app.bot.set_webhook(
                    url=full_webhook_url,
                    drop_pending_updates=True
                )
                logger.info(f"✅ Webhook configured: {full_webhook_url}")

            # Run webhook setup
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(setup_webhook())
            finally:
                loop.close()

        # Start keep-alive service for Render free tier
        if os.getenv('RENDER'):
            try:
                from keepalive import start_keepalive
                start_keepalive()
                logger.info("⏰ Keep-alive service started")
            except Exception as e:
                logger.warning(f"Keep-alive failed: {e}")

        # Run Flask server in main thread (handles both health checks and webhooks)
        logger.info("🚀 Starting Flask server (main thread)...")
        run_health_server()
        
    else:
        # Development mode - Bot polling with health server in background
        logger.info("💻 Development mode - Starting polling bot...")

        # Start health server in background for local testing
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()

        # Small delay for health server to start
        time.sleep(1)

        # Bot runs in main thread with polling
        run_telegram_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        raise