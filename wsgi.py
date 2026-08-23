"""
WSGI entry point for Gunicorn (if deploying as WSGI web service).
Initializes the Pyrogram bot in a background thread and exposes the Flask health app.
"""
import os
import logging
import threading
from dotenv import load_dotenv

load_dotenv()
os.environ['IS_PRODUCTION'] = 'true'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from health_server import app
from bot import TikTokBot

_bot_thread = None


def start_bot_in_background():
    """Start the Pyrogram bot in a background thread"""
    global _bot_thread

    def run_bot():
        try:
            logger.info("🤖 Starting Pyrogram MTProto Bot in background thread...")
            bot = TikTokBot()
            bot.run()
        except Exception as e:
            logger.critical(f"🚨 Bot thread failed: {e}", exc_info=True)

    _bot_thread = threading.Thread(target=run_bot, daemon=True, name="PyrogramBotThread")
    _bot_thread.start()
    logger.info("✅ Pyrogram Bot thread started")


try:
    start_bot_in_background()
except Exception as e:
    logger.critical(f"🚨 Bot initialization failed: {e}", exc_info=True)

logger.info("🚀 WSGI setup complete. Gunicorn serving Flask health endpoints.")
