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

@app.route('/health')
def health_check():
    """Health check endpoint for deployment platforms"""
    uptime = datetime.now() - start_time
    
    return jsonify({
        'status': 'healthy',
        'uptime': str(uptime).split('.')[0],
        'timestamp': datetime.now().isoformat(),
        'bot': 'TikTok Downloader Bot',
        'version': '2.0'
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for receiving Telegram updates"""
    try:
        # This will be handled by the main bot application
        update_data = request.get_json()
        logger.info(f"Received webhook update: {update_data}")
        
        # Forward to main bot handler (if needed)
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

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