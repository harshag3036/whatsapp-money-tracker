#!/usr/bin/env python3
"""
Run script for the WhatsApp Money Tracker Bot with improved session management.
This script starts the Flask application with the fixed session management.
"""

import os
import logging
import time
import threading
from dotenv import load_dotenv
from src.app import app
from src.session_manager import cleanup_expired_sessions

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger('run_app')

def session_cleanup_task():
    """Background task to periodically clean up expired sessions."""
    while True:
        try:
            # Sleep for 15 minutes
            time.sleep(15 * 60)
            
            # Clean up expired sessions
            removed_count = cleanup_expired_sessions()
            logger.info(f"Session cleanup task removed {removed_count} expired sessions")
        except Exception as e:
            logger.error(f"Error in session cleanup task: {e}")

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.getenv('PORT', 5000))
    
    # Start the session cleanup task in a background thread
    cleanup_thread = threading.Thread(target=session_cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("Started session cleanup background task")
    
    # Log startup information
    logger.info(f"Starting WhatsApp Money Tracker Bot on port {port}")
    logger.info(f"Debug mode: {app.debug}")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port)
