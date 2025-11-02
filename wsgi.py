"""
WSGI entry point for Gunicorn.
This file is responsible for initializing the bot and then exposing the Flask app.
"""
import os
import logging
import asyncio

# Set production flag before importing other modules
os.environ['IS_PRODUCTION'] = 'true'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("WSGI starting...")

# Import the main initialization function and the Flask app
from main import initialize_bot_for_production
from health_server import app

# --- Bot Initialization ---
# Gunicorn runs this code in the main master process before forking worker processes.
# We run the async initialization function here.
try:
    logger.info("Initializing bot for production...")
    asyncio.run(initialize_bot_for_production())
    logger.info("✅ Bot initialization complete.")
except Exception as e:
    logger.critical(f"🚨 Bot initialization failed: {e}", exc_info=True)
    # If the bot fails to initialize, we should not start the web server.
    # Gunicorn will exit if the app object is not found.
    raise RuntimeError("Could not initialize the bot. Exiting.") from e

logger.info("🚀 WSGI setup complete. Gunicorn can now serve the Flask app.")
