"""
Test Suite: Vercel Entry Point & Serverless Routing Compatibility
Verifies that:
1. api/index.py properly exports the Flask app instance.
2. Root URL '/' is served with 200 OK and index.html content.
3. Vercel rewritten paths (/api/index, /api/index.py) are correctly handled.
4. HTTP_X_FORWARDED_URI header preservation restores real paths (/api/info, /api/recommend, /static/...).
5. Static files (CSS, JS) are properly returned through WSGI.
6. Recommendation API continues to return valid JSON results.
"""

import os
import sys
import json
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api.index import app


class TestVercelEntryPoint(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_direct_root_route(self):
        """Visiting '/' directly should return 200 OK with the LORE homepage."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("LORE", html)
        self.assertIn("Stories worth getting lost in", html)

    def test_vercel_rewritten_root_path(self):
        """When Vercel rewrites '/' to '/api/index', it should return 200 OK with the LORE homepage."""
        response = self.client.get("/api/index")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("LORE", html)
        self.assertIn("Stories worth getting lost in", html)

    def test_vercel_rewritten_py_path(self):
        """When Vercel passes '/api/index.py', it should return 200 OK with the LORE homepage."""
        response = self.client.get("/api/index.py")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("LORE", html)

    def test_forwarded_uri_root(self):
        """When Vercel sets HTTP_X_FORWARDED_URI to '/', it should resolve to the homepage."""
        response = self.client.get(
            "/api/index",
            headers={"X-Forwarded-Uri": "/"}
        )
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("LORE", html)

    def test_forwarded_uri_api_info(self):
        """When user requests '/api/info', Vercel rewrites to /api/index with X-Forwarded-Uri."""
        response = self.client.get(
            "/api/index",
            headers={"X-Forwarded-Uri": "/api/info"}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["model_loaded"])
        self.assertGreaterEqual(data["total_stories"], 500)

    def test_forwarded_uri_api_recommend(self):
        """When user requests '/api/recommend', Vercel rewrites to /api/index with X-Forwarded-Uri."""
        payload = {
            "query": "A brave astronaut discovering an alien signal on Mars",
            "category": "Sci-Fi"
        }
        response = self.client.post(
            "/api/index",
            headers={"X-Forwarded-Uri": "/api/recommend", "Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "success")
        self.assertIn("story", data)
        self.assertIn("title", data["story"])
        self.assertIn("category", data["story"])

    def test_forwarded_uri_static_css(self):
        """When user requests '/static/style.css', static assets should be served."""
        response = self.client.get(
            "/api/index",
            headers={"X-Forwarded-Uri": "/static/style.css"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/css", response.content_type)
        css = response.get_data(as_text=True)
        self.assertIn("body", css)

    def test_forwarded_uri_static_script(self):
        """When user requests '/static/script.js', JS assets should be served."""
        response = self.client.get(
            "/api/index",
            headers={"X-Forwarded-Uri": "/static/script.js"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("javascript", response.content_type)
        js = response.get_data(as_text=True)
        self.assertIn("DOMContentLoaded", js)

    def test_forwarded_uri_static_speech(self):
        """When user requests '/static/speech.js', voice assets should be served."""
        response = self.client.get(
            "/api/index",
            headers={"X-Forwarded-Uri": "/static/speech.js"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("javascript", response.content_type)
        js = response.get_data(as_text=True)
        self.assertIn("LoreSpeech", js)


if __name__ == "__main__":
    unittest.main()
