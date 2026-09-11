"""
Automated Verification Suite for Vercel Deployment Entry Point & Flask WSGI
"""

import os
import sys
import unittest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api.index import app


class TestVercelDeployment(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_root_route(self):
        """Verify root route returns 200 and loads LORE HTML with templates."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"LORE", res.data)
        self.assertIn(b"Stories worth getting lost in", res.data)
        print("  [PASS] Root route / rendered index.html successfully.")

    def test_static_assets(self):
        """Verify static files (CSS, JS, SVG) are served correctly through WSGI app."""
        css_res = self.client.get("/static/style.css")
        self.assertEqual(css_res.status_code, 200)
        self.assertIn(b"--gold-primary", css_res.data)

        js_res = self.client.get("/static/script.js")
        self.assertEqual(js_res.status_code, 200)

        speech_res = self.client.get("/static/speech.js")
        self.assertEqual(speech_res.status_code, 200)

        svg_res = self.client.get("/static/assets/lore-emblem.svg")
        self.assertEqual(svg_res.status_code, 200)
        print("  [PASS] Static assets (CSS, JS, SVG) served properly.")

    def test_api_info(self):
        """Verify /api/info returns full 520-story dataset info and categories."""
        res = self.client.get("/api/info")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_stories"], 520)
        self.assertEqual(data["total_categories"], 13)
        print(f"  [PASS] /api/info returned {data['total_stories']} stories across {data['total_categories']} categories.")

    def test_api_categories(self):
        """Verify /api/categories returns the 13 supported genres."""
        res = self.client.get("/api/categories")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["categories"]), 13)
        print(f"  [PASS] /api/categories returned {len(data['categories'])} genres.")

    def test_api_recommend(self):
        """Verify /api/recommend endpoint executes TF-IDF recommendation."""
        payload = {
            "query": "A spooky abandoned asylum at midnight",
            "category": "Horror"
        }
        res = self.client.post("/api/recommend", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["story"]["category"], "Horror")
        self.assertIn("title", data["story"])
        self.assertIn("story_text", data["story"])
        print(f"  [PASS] /api/recommend returned story '{data['story']['title']}' (Category: {data['story']['category']}).")

    def test_find_another_story(self):
        """Verify find another story retains category and excludes first story."""
        payload1 = {
            "query": "space alien expedition",
            "category": "Sci-Fi"
        }
        res1 = self.client.post("/api/recommend", json=payload1)
        self.assertEqual(res1.status_code, 200)
        story1 = res1.get_json()["story"]

        payload2 = {
            "query": "space alien expedition",
            "category": "Sci-Fi",
            "exclude_ids": [story1["id"]],
            "is_find_another": True
        }
        res2 = self.client.post("/api/recommend", json=payload2)
        self.assertEqual(res2.status_code, 200)
        story2 = res2.get_json()["story"]

        self.assertEqual(story2["category"], "Sci-Fi")
        self.assertNotEqual(story1["id"], story2["id"])
        print(f"  [PASS] Find Another Story returned distinct story '{story2['title']}' within Sci-Fi.")


if __name__ == "__main__":
    unittest.main()
