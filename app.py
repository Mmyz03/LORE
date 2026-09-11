"""
LORE — AI-Powered Story Recommendation & Discovery System
Root Application Entry Point for Vercel Native Flask Framework Detection & WSGI Servers.
Exposes the single canonical Flask `app` object from `app/app.py`.
"""

import os
import sys

# Ensure the project root directory is on the Python module search path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import the existing Flask application instance
from app.app import app

# Expose app for WSGI / Vercel native Flask detection
__all__ = ["app"]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
