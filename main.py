"""
Main launcher for the TikTok Downloader Bot (MTProto / Pyrogram)
Handles both the MTProto Telegram bot and the background health server for cloud platforms.
"""

import os
import logging
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if not os.getenv('DEBUG') else logging.DEBUG
)
logger = logging.getLogger(__name__)

# Import the Flask health server runner
from health_server import run_health_server
from bot import TikTokBot


def main():
    """Main function to run health server and bot"""
    logger.info("🚀 Starting TikTok Downloader Bot (MTProto 2GB Edition)...")

    # Start background health server for deployment monitoring (Render, Railway, etc.)
    port = int(os.getenv('PORT', 8443))
    health_thread = threading.Thread(
        target=run_health_server,
        args=(port,),
        daemon=True,
        name="HealthServerThread"
    )
    health_thread.start()
    logger.info(f"🌐 Health server started in background on port {port}")

    # Start keep-alive service if configured for Render
    if os.getenv('RENDER'):
        try:
            from keepalive import start_keepalive
            start_keepalive()
            logger.info("⏰ Keep-alive service started")
        except Exception as e:
            logger.warning(f"Could not start keep-alive service: {e}")

    # Run the Pyrogram bot client
    try:
        bot = TikTokBot()
        bot.run()
    except Exception as e:
        logger.critical(f"❌ TikTok Bot failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()