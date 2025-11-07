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
from telegram import Update

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if not os.getenv('DEBUG') else logging.DEBUG
)
logger = logging.getLogger(__name__)

# Import the Flask app runner
from health_server import run_health_server

async def initialize_bot_for_production():
    """
    Initializes the bot, sets the webhook, and prepares the application
    for running in a production environment. This is called by wsgi.py.
    """
    webhook_url = os.getenv('WEBHOOK_URL')
    logger.info(f"🔗 Production Webhook URL: {webhook_url}")

    from bot import TikTokBot
    from telegram.ext import Application
    import sys
    import bot

    # Initialize bot and application with proper HTTP client configuration
    from telegram.request import HTTPXRequest

    bot_instance = TikTokBot()

    # Create application with custom HTTP request handler to avoid event loop issues
    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=30,
        write_timeout=60,
        connect_timeout=10,
        pool_timeout=5,
    )

    app = Application.builder().token(bot_instance.token).request(request).build()
    bot_instance._add_handlers(app)

    # Store the application globally for Flask/WSGI to access
    bot.telegram_app = app
    sys.modules['bot'].telegram_app = app

    # CRITICAL: Initialize the application
    await app.initialize()

    # Configure the webhook
    webhook_path = f"webhook/{bot_instance.token}"
    full_webhook_url = f"{webhook_url}/{webhook_path}" if webhook_url else None

    if full_webhook_url:
        await app.bot.set_webhook(
            url=full_webhook_url,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        logger.info(f"✅ Webhook configured: {full_webhook_url}")

    # Start the application's background tasks (e.g., job queue)
    await app.start()
    logger.info("✅ Telegram Application started and ready for updates")

    # Start keep-alive service if on Render
    if os.getenv('RENDER'):
        try:
            from keepalive import start_keepalive
            start_keepalive()
            logger.info("⏰ Keep-alive service started")
        except Exception as e:
            logger.warning(f"Could not start keep-alive service: {e}")


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
    """Main function to run the bot in development mode."""
    logger.info("🚀 Starting TikTok Downloader Bot...")

    # In production, the bot is initialized by the WSGI server (see wsgi.py).
    # This main function is now only for development (polling mode).
    is_production = os.getenv('IS_PRODUCTION') == 'true'

    if is_production:
        logger.critical("main.py should not be run directly in production!")
        logger.critical("Use 'gunicorn wsgi:app' to start the server.")
        return

    # Development mode - Bot polling with health server in background
    logger.info("💻 Development mode - Starting polling bot...")
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    from bot import TikTokBot
    bot_instance = TikTokBot()
    bot_instance.run()


if __name__ == '__main__':
    main()