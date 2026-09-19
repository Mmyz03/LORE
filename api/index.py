"""
LORE — Vercel Serverless Function & WSGI Entry Point
Exposes the canonical Flask `app` object from `app/app.py` with Vercel URL rewrite compatibility.
"""

import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.app import app


class VercelWSGIMiddleware:
    """
    WSGI Middleware for Vercel Serverless Function routing.
    Restores the original client URL path from Vercel's rewrite headers (X-Forwarded-Uri, X-Matched-Path)
    and removes any internal '/api/index' prefix from PATH_INFO.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        forwarded_uri = (
            environ.get("HTTP_X_FORWARDED_URI") or
            environ.get("HTTP_X_MATCHED_PATH") or
            environ.get("HTTP_X_VERCEL_MATCHED_PATH") or
            ""
        )
        if forwarded_uri:
            # Strip query parameters if present
            path = forwarded_uri.split("?", 1)[0]
            if path:
                environ["PATH_INFO"] = path
        else:
            path_info = environ.get("PATH_INFO", "")
            if path_info.startswith("/api/index.py"):
                path_info = path_info[len("/api/index.py"):] or "/"
                environ["PATH_INFO"] = path_info
            elif path_info.startswith("/api/index"):
                path_info = path_info[len("/api/index"):] or "/"
                environ["PATH_INFO"] = path_info

        return self.wsgi_app(environ, start_response)


# Wrap Flask's WSGI callable with Vercel rewrite middleware
app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)

# Export for Vercel Serverless Function runtime
__all__ = ["app"]
