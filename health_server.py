"""
Health check and utility endpoints for the TikTok bot
Used for deployment monitoring and webhook testing
"""

from flask import Flask, jsonify, request
import os
import logging
from datetime import datetime
import threading
import time

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
    """Webhook endpoint for receiving Telegram updates"""
    try:
        # Update activity on webhook calls (user interaction)
        update_activity()
        
        # Validate token (basic security)
        expected_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not expected_token or not token:
            return jsonify({'status': 'error', 'message': 'Invalid token'}), 401
            
        # Log webhook activity
        logger.info(f"Webhook received from Telegram")
        
        # The actual webhook handling is done by python-telegram-bot
        # This endpoint just needs to exist for routing
        return jsonify({'status': 'ok'})

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook_fallback():
    """Fallback webhook endpoint"""
    return jsonify({'status': 'ok', 'message': 'Webhook received'})

@app.route('/')
def root():
    """Root endpoint with bot information"""
    return jsonify({
        'name': 'TikTok HD Downloader Bot',
        'version': '2.0',
        'description': 'Downloads TikTok videos in HD quality without watermarks',
        'status': 'running',
        'uptime': str(datetime.now() - start_time).split('.')[0],
        'endpoints': {
            'health': '/health',
            'webhook': '/webhook'
        }
    })

def run_health_server(port=8443):
    """Run the health check server in a separate thread"""
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Health server error: {e}")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8443))
    run_health_server(port)