"""
Keep-alive service to prevent Render free tier from sleeping
Sends periodic requests to keep the service active
"""

import requests
import time
import logging
import os
from datetime import datetime
import asyncio
import threading

logger = logging.getLogger(__name__)

class KeepAlive:
    def __init__(self, service_url=None, interval_minutes=10):
        self.service_url = service_url or os.getenv('RENDER_EXTERNAL_URL')
        self.interval = interval_minutes * 60  # Convert to seconds
        self.running = False
        self.thread = None

    def start(self):
        """Start the keep-alive service"""
        if not self.service_url:
            logger.warning("No service URL provided for keep-alive")
            return

        if self.running:
            logger.warning("Keep-alive already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._keep_alive_loop, daemon=True)
        self.thread.start()
        logger.info(f"Keep-alive started: pinging {self.service_url} every {self.interval//60} minutes")

    def stop(self):
        """Stop the keep-alive service"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Keep-alive stopped")

    def _keep_alive_loop(self):
        """Main keep-alive loop"""
        while self.running:
            try:
                # Sleep first to avoid immediate ping on startup
                time.sleep(self.interval)

                if not self.running:
                    break

                # Send keep-alive ping
                response = requests.get(
                    f"{self.service_url}/health",
                    timeout=30,
                    headers={'User-Agent': 'KeepAlive/1.0'}
                )

                if response.status_code == 200:
                    logger.info(f"Keep-alive ping successful at {datetime.now()}")
                else:
                    logger.warning(f"Keep-alive ping failed: {response.status_code}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Keep-alive ping error: {e}")
            except Exception as e:
                logger.error(f"Keep-alive unexpected error: {e}")

# Global keep-alive instance
keepalive = KeepAlive()

def start_keepalive():
    """Start keep-alive if in production"""
    if os.getenv('RENDER') and os.getenv('RENDER_EXTERNAL_URL'):
        keepalive.start()

def stop_keepalive():
    """Stop keep-alive"""
    keepalive.stop()