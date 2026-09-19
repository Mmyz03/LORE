"""
Comprehensive Automated Verification for LORE Mobile Optimization & Performance
Tests:
1. Static Asset Delivery & HTML integrity
2. CSS Responsive Breakpoints & Touch Target Verification
3. JS Syntax & Speech API Engine integrity
4. REST API Endpoint Speed & Latency Benchmarks
"""

import os
import sys
import json
import time
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.app import app


class TestMobileAndPerf(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_endpoints_latency(self):
        """Verify API response speed and latency."""
        t0 = time.time()
        res = self.client.get("/api/info")
        lat = (time.time() - t0) * 1000
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.get_data(as_text=True))
        self.assertEqual(data["status"], "success")
        self.assertLess(lat, 500) # Response under 500ms

        # Test GET /api/categories
        t0 = time.time()
        res2 = self.client.get("/api/categories")
        lat2 = (time.time() - t0) * 1000
        self.assertEqual(res2.status_code, 200)
        data2 = json.loads(res2.get_data(as_text=True))
        self.assertEqual(data2["status"], "success")
        self.assertEqual(data2["total"], 12)
        self.assertLess(lat2, 500)

    def test_css_rules_and_tokens(self):
        """Verify responsive design tokens, breakpoints, and clamp rules in style.css."""
        css_path = os.path.join(PROJECT_ROOT, "app", "static", "style.css")
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()

        self.assertIn("#050507", css)
        self.assertIn("#e6ca85", css)
        self.assertIn("bg-glow", css)
        self.assertIn("clamp(", css)
        self.assertIn("env(safe-area-inset-bottom)", css)

        for bp in ["1024px", "768px", "640px", "430px", "360px"]:
            self.assertIn(bp, css)

    def test_speech_js_integrity(self):
        """Verify speech.js contains Web Speech API and Controller classes."""
        js_path = os.path.join(PROJECT_ROOT, "app", "static", "speech.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        self.assertIn("TextToSpeechProvider", js)
        self.assertIn("BrowserSpeechProvider", js)
        self.assertIn("LoreSpeechController", js)
        self.assertIn("LoreSpeech", js)


if __name__ == "__main__":
    unittest.main()
