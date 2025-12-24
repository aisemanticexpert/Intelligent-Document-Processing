"""
WSGI Entry Point for Financial IDR API
=======================================

This module serves as the entry point for WSGI servers like Gunicorn.
It creates and exposes the Flask application instance.

Author: Rajesh Kumar Gupta
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and create the API server
try:
    from src.api.server import create_api_server

    # Create the API server instance
    server = create_api_server()

    # Expose the Flask app for WSGI
    app = server.app

    logger.info("Financial IDR API application initialized successfully")

except Exception as e:
    logger.error(f"Failed to initialize application: {e}")
    raise


if __name__ == "__main__":
    # Run with Flask development server if executed directly
    app.run(host="0.0.0.0", port=5000, debug=False)
