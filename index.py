"""
LORE — AI-Powered Story Recommendation & Discovery System
Vercel Native Entry Point & WSGI Runner
Exposes the Flask `app` object from `app/app.py`.
"""

import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.app import app

__all__ = ["app"]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
