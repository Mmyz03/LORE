"""
Vercel Serverless Function Entry Point for LORE (Flask)
Exports the WSGI `app` object for Vercel deployment.
"""

import os
import sys

# Ensure the project root directory is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.app import app

# Export for Vercel WSGI runner
__all__ = ["app"]
