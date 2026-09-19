"""
LORE — Vercel Serverless Function & WSGI Entry Point
Exposes the canonical Flask `app` object from `app/app.py`.
"""

import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.app import app

# Export for Vercel Serverless Function runtime
app = app
