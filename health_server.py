"""
Health check and utility endpoints for the TikTok bot
Used for deployment monitoring, uptime tracking, and Render keep-alive
"""

from flask import Flask, jsonify, request
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
        'service': 'TikTok HD Downloader Bot (MTProto)',
        'status': 'online',
        'uptime': str(uptime).split('.')[0],
        'version': '3.0.0',
        'max_file_size': '2,000 MB (2 GB)',
        'features': [
            '🏆 Ultra HD Quality (up to 2 GB)',
            '✅ No Watermarks',
            '⚡ MTProto Native Speed',
            '🔄 Multi-API Fallback'
        ],
        'endpoints': {
            '/health': 'Health check',
            '/ping': 'Simple ping',
            '/wake': 'Wake up keep-alive'
        }
    })


@app.route('/health')
def health_check():
    """Health check endpoint for deployment platforms (Render, Railway, etc.)"""
    uptime = datetime.now() - start_time
    idle_time = datetime.now() - last_activity

    update_activity()

    return jsonify({
        'status': 'healthy',
        'uptime': str(uptime).split('.')[0],
        'last_activity': str(idle_time).split('.')[0],
        'timestamp': datetime.now().isoformat(),
        'bot': 'TikTok Downloader Bot (MTProto)',
        'version': '3.0.0',
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
    """Wake up endpoint to prevent cloud sleep"""
    update_activity()
    uptime = datetime.now() - start_time
    return jsonify({
        'status': 'awake',
        'message': 'Service is active',
        'uptime': str(uptime).split('.')[0]
    })


def run_health_server(port=None):
    """Run the health check server in a separate thread"""
    if port is None:
        port = int(os.getenv('PORT', 8443))
    try:
        logger.info(f"🌐 Health server running on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Health server error: {e}")


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8443))
    run_health_server(port)