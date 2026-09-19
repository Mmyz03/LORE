"""
LORE — AI-Powered Story Generation Platform
Master Entry Point for Local Development & Vercel Deployment

Exposes the canonical Flask `app` object from `app/app.py`.
Discovered automatically by Vercel's zero-configuration Flask runtime.
"""

import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.app import app

# Export for WSGI servers and Vercel runtime
__all__ = ["app"]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
