"""
LORE — AI-Powered Story Recommendation & Discovery System
Root Application Entry Point for Vercel Native Flask Framework Detection & WSGI Servers.
Loads the canonical Flask `app` object directly from `app/app.py` using importlib to prevent module namespace collision.
"""

import os
import sys
import importlib.util

# Ensure the project root directory is on the Python module search path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Path to the canonical Flask application file
FLASK_FILE = os.path.join(PROJECT_ROOT, "app", "app.py")

# Dynamically load app/app.py under a distinct namespace to prevent 'app' module collision
spec = importlib.util.spec_from_file_location("lore_flask_backend", FLASK_FILE)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load module specification from: {FLASK_FILE}")

module = importlib.util.module_from_spec(spec)
sys.modules["lore_flask_backend"] = module
spec.loader.exec_module(module)

# Expose canonical Flask application instance for Vercel WSGI
app = module.app

__all__ = ["app"]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
