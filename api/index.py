"""
Vercel Serverless Function Entry Point for LORE (Flask)
Exports the WSGI `app` object for Vercel deployment.
Includes robust path routing middleware to handle Vercel's rewrite mechanism.
"""

import os
import sys

# Ensure the project root directory is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.app import app


class VercelPathMiddleware:
    """
    WSGI Middleware to normalize Vercel serverless request paths.
    When vercel.json rewrites incoming paths (e.g. /(.*) -> /api/index),
    Vercel sets PATH_INFO to /api/index or /api/index.py while passing
    the user's original URL in HTTP_X_FORWARDED_URI, HTTP_X_MATCHED_PATH, or REQUEST_URI.
    This middleware restores the original requested path into PATH_INFO so Flask routes properly.
    """

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # 1. Retrieve the original URI from Vercel proxy headers if present
        raw_uri = (
            environ.get("HTTP_X_FORWARDED_URI")
            or environ.get("HTTP_X_MATCHED_PATH")
            or environ.get("HTTP_X_REAL_PATH")
            or environ.get("REQUEST_URI")
        )

        if raw_uri:
            # Strip query string if present
            path = raw_uri.split("?")[0]
            if path:
                environ["PATH_INFO"] = path

        # 2. Normalize /api/index or /api/index.py down to root / if unforwarded
        path_info = environ.get("PATH_INFO", "")
        if path_info in ("/api/index", "/api/index.py", "/api/index/"):
            environ["PATH_INFO"] = "/"
        elif path_info.startswith("/api/index/"):
            environ["PATH_INFO"] = path_info[len("/api/index"):]

        return self.wsgi_app(environ, start_response)


# Wrap Flask's WSGI callable with path normalization middleware
app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

# Export for Vercel Python WSGI runner
__all__ = ["app"]
