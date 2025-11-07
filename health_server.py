"""
Health check and utility endpoints for the TikTok bot
Used for deployment monitoring and webhook testing
"""

from flask import Flask, jsonify, request
from telegram import Update
import asyncio
import sys
import threading
import os
import logging
from datetime import datetime

# Create Flask app for health checks
app = Flask(__name__)
logger = logging.getLogger(__name__)

# Bot start time for uptime calculation
start_time = datetime.now()
last_activity = datetime.now()

def update_activity():
    """Update last activity timestamp"""
    global last_activity
    last_activity = datetime.now()

@app.route('/')
def root():
    """Root endpoint with bot information"""
    uptime = datetime.now() - start_time

    return jsonify({
        'service': 'TikTok HD Downloader Bot',
        'status': 'online',
        'uptime': str(uptime).split('.')[0],
        'version': '2.0.0',
        'features': [
            '🏆 Ultra HD Quality (42MB+ files)',
            '✅ No Watermarks',
            '🔄 Multi-API Fallback',
            '⚡ Fast Processing'
        ],
        'endpoints': {
            '/health': 'Health check',
            '/ping': 'Simple ping',
            '/webhook/<token>': 'Telegram webhook'
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint for deployment platforms"""
    uptime = datetime.now() - start_time
    idle_time = datetime.now() - last_activity

    # Update activity on health checks (keeps service active)
    update_activity()

    return jsonify({
        'status': 'healthy',
        'uptime': str(uptime).split('.')[0],
        'last_activity': str(idle_time).split('.')[0],
        'timestamp': datetime.now().isoformat(),
        'bot': 'TikTok Downloader Bot',
        'version': '2.0.0',
        'memory_usage': 'ok',
        'platform': os.getenv('RENDER', 'local')
    })

@app.route('/ping')
def ping():
    """Simple ping endpoint for keep-alive requests"""
    update_activity()
    return 'pong'

@app.route('/wake')
def wake():
    """Wake up endpoint to prevent sleep"""
    update_activity()
    uptime = datetime.now() - start_time
    return jsonify({
        'status': 'awake',
        'message': 'Service is active',
        'uptime': str(uptime).split('.')[0]
    })

@app.route('/webhook/<token>', methods=['POST'])
def webhook(token):
    """Webhook endpoint to receive updates from Telegram."""
    update_activity()

    # Use the globally stored app instance from wsgi.py
    if 'bot' in sys.modules and hasattr(sys.modules['bot'], 'telegram_app'):
        telegram_app = sys.modules['bot'].telegram_app
        if telegram_app and telegram_app.bot.token == token:
            try:
                update_json = request.get_json(force=True)
                update = Update.de_json(update_json, telegram_app.bot)
                logger.info(f"Processing Telegram update: {update.update_id}")

                # Get the bot's persistent event loop from wsgi module
                try:
                    bot_loop = None
                    if 'wsgi' in sys.modules and hasattr(sys.modules['wsgi'], 'get_bot_loop'):
                        bot_loop = sys.modules['wsgi'].get_bot_loop()

                    if bot_loop and not bot_loop.is_closed():
                        # Schedule the update processing in the bot's event loop
                        future = asyncio.run_coroutine_threadsafe(
                            telegram_app.process_update(update),
                            bot_loop
                        )
                        # Don't wait for completion - just schedule it
                        # The result will be processed asynchronously
                        logger.debug(f"Update {update.update_id} scheduled in bot's event loop")
                    else:
                        # Fallback: Process in a new thread with its own loop
                        # This shouldn't normally happen in production
                        logger.warning("Bot loop not available, using fallback processing")

                        def process_update_safely():
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                try:
                                    loop.run_until_complete(telegram_app.process_update(update))
                                    loop.run_until_complete(asyncio.sleep(0.1))
                                finally:
                                    try:
                                        pending = asyncio.all_tasks(loop)
                                        for task in pending:
                                            task.cancel()
                                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                                    except Exception:
                                        pass
                                    loop.close()
                            except Exception as e:
                                logger.error(f"Error processing update: {e}", exc_info=True)

                        threading.Thread(target=process_update_safely, daemon=True).start()

                except Exception as processing_error:
                    logger.error(f"Error scheduling update: {processing_error}", exc_info=True)

                return jsonify(status='ok'), 200

            except Exception as e:
                logger.error(f"Webhook processing error: {e}", exc_info=True)
                return jsonify(status='error', message=str(e)), 500

    logger.warning("Webhook called with invalid token or uninitialized app")
    return jsonify(status='error', message='Invalid token or uninitialized app'), 403@app.route('/webhook', methods=['POST'])
def webhook_fallback():
    """Fallback webhook endpoint"""
    return jsonify({'status': 'ok', 'message': 'Webhook received'})

def run_health_server(port=8443):
    """Run the health check server in a separate thread"""
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Health server error: {e}")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8443))
    run_health_server(port)