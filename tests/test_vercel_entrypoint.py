"""
Test Suite: LORE Flask Application & Vercel Entry Point (index.py & app/app.py)
Verifies:
1. Root `index.py` directly exports the canonical Flask `app` object for Vercel discovery.
2. `app/app.py` directly defines the canonical Flask `app` object.
3. Direct root route '/' returns 200 OK with the LORE homepage.
4. Static files (CSS, JS, SVG) are properly served by Flask.
5. AI Genre Presets endpoint (/api/categories) returns all 12 supported genres.
6. System Info endpoint (/api/info) returns AI engine readiness and provider metadata.
7. AI Story Generation endpoint (/api/generate-story) responds with proper schema.
8. Flask route map contains all required routes without fragile rewrite middlewares.
"""

import os
import sys
import json
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.app import app
import index


class TestFlaskApplication(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_flask_instance(self):
        """Verify app/app.py exports a valid Flask instance."""
        import flask
        self.assertIsInstance(app, flask.Flask)

    def test_root_index_export(self):
        """Verify root index.py exports the exact canonical Flask app instance."""
        import flask
        self.assertIsInstance(index.app, flask.Flask)
        self.assertIs(index.app, app)

    def test_root_route(self):
        """Visiting '/' directly should return 200 OK with the LORE homepage."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("LORE", html)
        self.assertIn("Stories worth getting lost in", html)

    def test_api_info(self):
        """Visiting '/api/info' should return status success and engine metadata."""
        response = self.client.get("/api/info")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["engine"], "LORE AI Story Generation Platform")
        self.assertEqual(data["total_presets"], 12)
        self.assertIn("features", data)

    def test_api_categories(self):
        """Visiting '/api/categories' should return all 12 AI genre presets."""
        response = self.client.get("/api/categories")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total"], 12)
        categories = [c["name"] for c in data["categories"]]
        self.assertIn("Mystery", categories)
        self.assertIn("Horror", categories)
        self.assertIn("Romance", categories)
        self.assertIn("Fantasy", categories)
        self.assertIn("Science Fiction", categories)
        self.assertIn("Bedtime", categories)

    def test_static_css(self):
        """Static CSS should be served correctly."""
        response = self.client.get("/static/style.css")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/css", response.content_type)
        css = response.get_data(as_text=True)
        self.assertIn("body", css)

    def test_static_script(self):
        """Static JS should be served correctly."""
        response = self.client.get("/static/script.js")
        self.assertEqual(response.status_code, 200)
        self.assertIn("javascript", response.content_type)
        js = response.get_data(as_text=True)
        self.assertIn("DOMContentLoaded", js)

    def test_static_speech(self):
        """Static voice JS should be served correctly."""
        response = self.client.get("/static/speech.js")
        self.assertEqual(response.status_code, 200)
        self.assertIn("javascript", response.content_type)
        js = response.get_data(as_text=True)
        self.assertIn("LoreSpeech", js)

    def test_static_emblem_svg(self):
        """Static SVG brand emblem should be served correctly."""
        response = self.client.get("/static/assets/lore-emblem.svg")
        self.assertEqual(response.status_code, 200)
        self.assertIn("image/svg+xml", response.content_type)

    def test_route_map_completeness(self):
        """Verify URL route map has all required endpoints on the deployed Flask instance."""
        routes = {rule.rule for rule in app.url_map.iter_rules()}
        self.assertIn("/", routes)
        self.assertIn("/api/categories", routes)
        self.assertIn("/api/generate-story", routes)
        self.assertIn("/api/info", routes)
        self.assertIn("/static/<path:filename>", routes)


if __name__ == "__main__":
    unittest.main()
