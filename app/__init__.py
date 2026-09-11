"""
LORE Application Package
Exposes the single canonical Flask `app` instance from `app.app`.
"""

from app.app import app

__all__ = ["app"]
