#!/usr/bin/env python3
"""
Entry point script for the WhatsApp Money Tracker Bot.
This script makes it easier to run the application.
"""

import os
from src.app import app

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting WhatsApp Money Tracker Bot on port {port}...")
    print("Press Ctrl+C to stop the server")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True)
