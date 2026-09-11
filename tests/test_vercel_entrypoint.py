"""
Test Suite: Root Application Entry Point & Native Flask Routing
Verifies that:
1. Root index.py and app.py properly expose the canonical Flask `app` object.
2. Direct root route '/' returns 200 OK with the LORE homepage.
3. Static files (CSS, JS, SVG) are properly served by Flask.
4. Info and Categories endpoints return full dataset metrics (520 stories across 13 genres).
5. Recommendation endpoint (/api/recommend) operates seamlessly.
"""

import os
import sys
import json
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app


class TestRootFlaskEntryPoint(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_root_route(self):
        """Visiting '/' directly should return 200 OK with the LORE homepage."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("LORE", html)
        self.assertIn("Stories worth getting lost in", html)

    def test_api_info(self):
        """Visiting '/api/info' should return status success and 520 stories."""
        response = self.client.get("/api/info")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["model_loaded"])
        self.assertEqual(data["total_stories"], 520)
        self.assertEqual(data["total_categories"], 13)

    def test_api_categories(self):
        """Visiting '/api/categories' should return all 13 story categories."""
        response = self.client.get("/api/categories")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["categories"]), 13)

    def test_api_recommend(self):
        """POST '/api/recommend' should return a recommended story."""
        payload = {
            "query": "A brave astronaut discovering an alien signal on Mars",
            "category": "Sci-Fi"
        }
        response = self.client.post(
            "/api/recommend",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "success")
        self.assertIn("story", data)
        self.assertIn("title", data["story"])
        self.assertEqual(data["story"]["category"], "Sci-Fi")

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


if __name__ == "__main__":
    unittest.main()
