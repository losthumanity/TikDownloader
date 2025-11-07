"""
WSGI entry point for Gunicorn.
This file is responsible for initializing the bot and then exposing the Flask app.
"""
import os
import logging
import asyncio
import threading

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
# We need to run the bot in a background thread with its own event loop
# that stays alive to handle webhook updates

_bot_loop = None
_bot_thread = None

def start_bot_in_background():
    """Start the bot in a background thread with a persistent event loop"""
    global _bot_loop
    
    def run_bot_loop():
        global _bot_loop
        # Create a new event loop for this thread
        _bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_bot_loop)
        
        try:
            logger.info("Starting bot initialization in background thread...")
            _bot_loop.run_until_complete(initialize_bot_for_production())
            logger.info("✅ Bot initialization complete. Event loop will stay alive.")
            
            # Keep the loop running to handle webhook updates
            _bot_loop.run_forever()
        except Exception as e:
            logger.critical(f"🚨 Bot loop failed: {e}", exc_info=True)
        finally:
            _bot_loop.close()
    
    # Start the bot thread
    _bot_thread = threading.Thread(target=run_bot_loop, daemon=True, name="BotEventLoop")
    _bot_thread.start()
    
    # Wait for initialization to complete (give it a few seconds)
    import time
    timeout = 10
    start_time = time.time()
    while _bot_loop is None or not _bot_loop.is_running():
        if time.time() - start_time > timeout:
            raise RuntimeError("Bot initialization timed out")
        time.sleep(0.1)
    
    logger.info("✅ Bot thread started with persistent event loop")

try:
    start_bot_in_background()
except Exception as e:
    logger.critical(f"🚨 Bot initialization failed: {e}", exc_info=True)
    raise RuntimeError("Could not initialize the bot. Exiting.") from e

# Export the loop so webhook handler can access it
def get_bot_loop():
    """Get the bot's event loop for webhook processing"""
    return _bot_loop

# Make it accessible from health_server
import sys
sys.modules['wsgi'].get_bot_loop = get_bot_loop

logger.info("🚀 WSGI setup complete. Gunicorn can now serve the Flask app.")
