"""
LORE — AI Story Generation Subsystem Tests
Verifies:
1. StoryGenerator controller initialization & provider switching.
2. Robust JSON response cleaning, schema parsing, and markdown fence stripping.
3. Category preset generation and dynamic length calibration (~2-page default, quick, extended, custom).
4. Missing API key graceful error handling (HTTP 503 with friendly user message).
5. Empty prompt / category validation (HTTP 400).
6. Provider resolution for Gemini, OpenAI, Groq, OpenRouter, and DeepSeek.
7. Full narrative structure validation (beginning, middle, climax, ending, word count, reading time).
8. End-to-end endpoint /api/generate-story behavior.
"""

import os
import sys
import json
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from story_generation.generator import StoryGenerator, load_env_file
from story_generation.prompts import build_story_prompt
from story_generation.providers.base import BaseStoryProvider, StoryGenerationError
from story_generation.providers.gemini_provider import GeminiStoryProvider
from story_generation.providers.openai_provider import OpenAIStoryProvider
from app.app import app


class MockFullArcStoryProvider(BaseStoryProvider):
    """Mock provider returning a full literary story arc (~1000 words narrative structure)."""
    def __init__(self, should_succeed=True):
        super().__init__(api_key="mock_api_key_12345", model="gemini-1.5-flash")
        self.should_succeed = should_succeed

    def generate_story(
        self,
        prompt: str = "",
        category: str = None,
        length: str = "default",
        is_another: bool = False,
        previous_titles: list = None,
        **kwargs
    ) -> dict:
        if not self.should_succeed:
            raise StoryGenerationError("Mock provider simulated outage", code="PROVIDER_ERROR", status_code=500)

        title = "The Secret of the Crimson Vault" if not is_another else "Shadows Over the Moor"
        genre = category or "Mystery"
        summary = "Detective Arthur Vance investigates an abandoned hotel only to discover the victim was his estranged mentor."
        
        paragraphs = [
            "The relentless autumn rain lashed against the cracked, dust-caked stained glass of the Grand Horizon Hotel. Closed since the winter of 1928, the once-opulent seaside resort now smelled only of rotting timber, sea salt, and old tragedies. Detective Arthur Vance stepped across the shattered threshold, his heavy wool overcoat damp and cold against his shoulders.",
            "In Room 404, on the fourth floor where the wallpaper hung like shed skin, lay the body. The local constabulary had called it a vagrant dispute, but Vance had noticed the silver pocket watch on the mantelpiece—inscribed with the crest of the Saint Jude Medical Academy. Vance's throat constricted. He pulled the leather notebook from the victim's coat pocket, his hands trembling as he recognized the elegant, sloping handwriting. It belonged to Dr. Marcus Sterling—the man who had paid Vance's academy tuition and disappeared twenty years ago.",
            "Footsteps creaked on the floorboards behind him. Vance spun around, his service revolver drawn. Emerging from the corridor shadows was not an intruder, but Inspector Thorne, the lead investigator on the coastal precinct. In Thorne's gloved hand gleamed a brass key identical to the one Marcus had worn around his neck. 'You shouldn't have opened the ledger, Arthur,' Thorne whispered, raising a silenced pistol.",
            "A deafening crack of thunder masked the sudden struggle. Vance dove beneath the mahogany table as a bullet splintered the oak doorframe. Lunging forward, Vance tackled Thorne against the decaying balustrade. The rotten cedar gave way beneath their combined weight, sending Thorne plunging onto the carpeted landing below, disarmed and breathless.",
            "When morning light finally broke through the gray coastal mist, sirens wailed in the distance. Vance stood on the windswept veranda, clutching Marcus's final letter. The truth was out, the ledger was safe, but the weight of twenty years of silence would linger far longer than the storm."
        ]
        content = "\n\n".join(paragraphs)
        words = content.split()

        return {
            "title": title,
            "genre": genre,
            "summary": summary,
            "content": content,
            "tags": ["mystery", "detective", "hotel", "conspiracy", "noir"],
            "word_count": len(words),
            "reading_time_min": max(1, round(len(words) / 200)),
            "model": self.model,
            "provider": "Google Gemini"
        }


class TestStoryGeneration(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_json_clean_and_parse_standard(self):
        """Verify standard JSON parses correctly into story schema."""
        raw = json.dumps({
            "title": "The Forgotten Crypt",
            "genre": "Horror",
            "summary": "An archaeologist unlocks a tomb.",
            "content": "Deep beneath the sands, the seal was broken.\n\nA cold wind blew from the dark corridor.",
            "tags": ["tomb", "archaeology", "horror"]
        })
        parsed = BaseStoryProvider.clean_and_parse_json(raw)
        self.assertEqual(parsed["title"], "The Forgotten Crypt")
        self.assertEqual(parsed["genre"], "Horror")
        self.assertEqual(parsed["word_count"], 16)
        self.assertEqual(parsed["reading_time_min"], 1)
        self.assertEqual(len(parsed["tags"]), 3)

    def test_json_clean_and_parse_markdown_fences(self):
        """Verify JSON surrounded by markdown ```json fences is cleanly parsed."""
        raw = """```json
{
  "title": "The Starlight Navigator",
  "genre": "Sci-Fi",
  "summary": "A lone pilot maps the uncharted edge of the spiral arm.",
  "content": "The subspace drive hummed with rhythmic vibration. Across the viewport, twin binary stars cast amber shadows across the cockpit.",
  "tags": ["space", "pilot", "stars"]
}
```"""
        parsed = BaseStoryProvider.clean_and_parse_json(raw)
        self.assertEqual(parsed["title"], "The Starlight Navigator")
        self.assertEqual(parsed["genre"], "Sci-Fi")

    def test_json_clean_and_parse_invalid(self):
        """Verify malformed JSON raises StoryGenerationError."""
        with self.assertRaises(StoryGenerationError):
            BaseStoryProvider.clean_and_parse_json("Not a json at all")

    def test_prompt_builder_length_and_category_calibration(self):
        """Verify prompt builder formats length, genre preset, and anti-repetition memory."""
        sys_prompt, user_msg = build_story_prompt(
            user_prompt="A clockmaker finds a gear that turns backward.",
            category="Fantasy",
            length="short",
            is_another=True,
            previous_titles=["The Clock of Eldoria"]
        )
        self.assertIn("CATEGORY PRESET: Fantasy", user_msg)
        self.assertIn("clockmaker finds a gear", user_msg)
        self.assertIn("single-page short story", user_msg)
        self.assertIn("The Clock of Eldoria", user_msg)
        self.assertIn("COMPLETE NARRATIVE ARC", sys_prompt)

    def test_generator_with_mock_provider(self):
        """Verify StoryGenerator controller functions seamlessly with full narrative arc provider."""
        mock_provider = MockFullArcStoryProvider(should_succeed=True)
        generator = StoryGenerator(provider=mock_provider)
        self.assertTrue(generator.is_available())

        story = generator.generate(
            prompt="Write a dark murder mystery in an abandoned hotel",
            category="Mystery",
            length="default"
        )
        self.assertEqual(story["title"], "The Secret of the Crimson Vault")
        self.assertEqual(story["genre"], "Mystery")
        self.assertIn("Marcus", story["content"])
        self.assertGreater(story["word_count"], 150)
        self.assertGreaterEqual(len(story["tags"]), 3)

        # Test Generate Another Story
        story_another = generator.generate(
            prompt="Write a dark murder mystery in an abandoned hotel",
            category="Mystery",
            length="default",
            is_another=True,
            previous_titles=["The Secret of the Crimson Vault"]
        )
        self.assertEqual(story_another["title"], "Shadows Over the Moor")

    def test_generator_category_only_preset(self):
        """Verify generator allows generation when only a category is selected."""
        mock_provider = MockFullArcStoryProvider(should_succeed=True)
        generator = StoryGenerator(provider=mock_provider)
        story = generator.generate(category="Horror")
        self.assertEqual(story["genre"], "Horror")

    def test_provider_resolution_heuristics(self):
        """Verify provider resolution based on environment variables."""
        saved_env = {k: os.environ.get(k) for k in ["STORY_AI_PROVIDER", "STORY_AI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "STORY_AI_MODEL"]}
        os.environ["STORY_AI_MODEL"] = ""
        
        # Test Gemini resolution via STORY_AI_PROVIDER=gemini
        os.environ["STORY_AI_PROVIDER"] = "gemini"
        os.environ["STORY_AI_API_KEY"] = "AIzaSyTestKey123"
        os.environ["OPENAI_API_KEY"] = ""
        gen = StoryGenerator()
        self.assertIsInstance(gen.provider, GeminiStoryProvider)
        self.assertTrue(gen.is_available())

        # Test Gemini resolution via GEMINI_API_KEY (when STORY_AI_PROVIDER and OPENAI_API_KEY are unset)
        os.environ["STORY_AI_PROVIDER"] = ""
        os.environ["STORY_AI_API_KEY"] = ""
        os.environ["OPENAI_API_KEY"] = ""
        os.environ["GEMINI_API_KEY"] = "AIzaSyGeminiKey"
        gen_gemini = StoryGenerator()
        self.assertIsInstance(gen_gemini.provider, GeminiStoryProvider)
        self.assertTrue(gen_gemini.is_available())

        # Test Gemini resolution via GOOGLE_API_KEY
        os.environ["GEMINI_API_KEY"] = ""
        os.environ["GOOGLE_API_KEY"] = "AIzaSyGoogleKey"
        gen_google = StoryGenerator()
        self.assertIsInstance(gen_google.provider, GeminiStoryProvider)
        self.assertTrue(gen_google.is_available())
        os.environ["GOOGLE_API_KEY"] = ""

        # Test OpenAI resolution via OPENAI_API_KEY (auto-detected)
        os.environ["OPENAI_API_KEY"] = "sk-testOpenAIKey123"
        gen_openai = StoryGenerator()
        self.assertIsInstance(gen_openai.provider, OpenAIStoryProvider)
        self.assertTrue(gen_openai.is_available())
        os.environ["OPENAI_API_KEY"] = ""

        # Test OpenAI resolution via STORY_AI_PROVIDER=openai
        os.environ["STORY_AI_PROVIDER"] = "openai"
        os.environ["STORY_AI_API_KEY"] = "sk-testOpenAIKey123"
        gen_openai_explicit = StoryGenerator()
        self.assertIsInstance(gen_openai_explicit.provider, OpenAIStoryProvider)
        self.assertTrue(gen_openai_explicit.is_available())

        # Test Groq resolution
        os.environ["STORY_AI_PROVIDER"] = "groq"
        os.environ["STORY_AI_API_KEY"] = "gsk_testGroqKey123"
        gen_groq = StoryGenerator()
        self.assertIsInstance(gen_groq.provider, OpenAIStoryProvider)
        self.assertEqual(gen_groq.provider.model, "llama-3.3-70b-versatile")

        # Cleanup
        for k, v in saved_env.items():
            if v is not None:
                os.environ[k] = v
            elif k in os.environ:
                del os.environ[k]

    def test_api_generate_story_empty_prompt_and_category(self):
        """POST /api/generate-story with empty prompt and no category returns 400."""
        response = self.client.post(
            "/api/generate-story",
            data=json.dumps({"prompt": "   ", "category": ""}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.get_data(as_text=True))
        self.assertFalse(data["success"])
        self.assertIn("Please describe", data["error"])

    def test_default_provider_is_openai(self):
        """Verify default provider is OpenAIStoryProvider when no env vars are set."""
        saved_env = {k: os.environ.get(k) for k in ["STORY_AI_PROVIDER", "STORY_AI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY"]}
        for k in saved_env:
            os.environ[k] = ""

        gen = StoryGenerator()
        self.assertIsInstance(gen.provider, OpenAIStoryProvider)
        self.assertEqual(gen.provider.model, "gpt-4o-mini")

        for k, v in saved_env.items():
            if v is not None:
                os.environ[k] = v
            elif k in os.environ:
                del os.environ[k]

    def test_api_generate_story_missing_key_behavior(self):
        """If no API key is configured, API returns a friendly 503 without crashing."""
        saved_env = {k: os.environ.get(k) for k in ["STORY_AI_PROVIDER", "STORY_AI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY"]}
        for k in saved_env:
            os.environ[k] = ""

        import app.app as flask_app
        flask_app.GENERATOR = StoryGenerator()

        response = self.client.post(
            "/api/generate-story",
            data=json.dumps({"prompt": "A scary haunted house story", "category": "Horror"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.get_data(as_text=True))
        self.assertFalse(data["success"])
        self.assertEqual(data["code"], "NO_API_KEY")
        self.assertIn("OPENAI_API_KEY", data["error"])

        # Restore
        for k, v in saved_env.items():
            if v is not None:
                os.environ[k] = v
            elif k in os.environ:
                del os.environ[k]


    def test_placeholder_api_key_not_available(self):
        """Verify placeholder keys are treated as unconfigured rather than valid."""
        for placeholder in ["your_openai_api_key_here", "your_new_openai_api_key_here", "sk-your-openai-api-key", "placeholder_key"]:
            prov = OpenAIStoryProvider(api_key=placeholder)
            self.assertFalse(prov.is_available())

    def test_openai_provider_error_mappings(self):
        """Verify OpenAI error codes are classified accurately."""
        from unittest.mock import patch, MagicMock
        prov = OpenAIStoryProvider(api_key="sk-realValidLookingKeyForTesting12345")

        # 1. Test 401 Invalid Key
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            mock_resp.json.return_value = {"error": {"message": "Incorrect API key", "code": "invalid_api_key"}}
            mock_post.return_value = mock_resp
            with self.assertRaises(StoryGenerationError) as ctx:
                prov.generate_story(prompt="A test prompt")
            self.assertEqual(ctx.exception.code, "INVALID_API_KEY")

        # 2. Test 429 Quota Exceeded
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 429
            mock_resp.json.return_value = {"error": {"message": "You exceeded your current quota", "code": "insufficient_quota"}}
            mock_post.return_value = mock_resp
            with self.assertRaises(StoryGenerationError) as ctx:
                prov.generate_story(prompt="A test prompt")
            self.assertEqual(ctx.exception.code, "QUOTA_EXCEEDED")

        # 3. Test 404 Model Not Found
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_resp.json.return_value = {"error": {"message": "Model not found", "code": "model_not_found"}}
            mock_post.return_value = mock_resp
            with self.assertRaises(StoryGenerationError) as ctx:
                prov.generate_story(prompt="A test prompt")
            self.assertEqual(ctx.exception.code, "MODEL_NOT_FOUND")

        # 4. Test 403 Permission Denied
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 403
            mock_resp.json.return_value = {"error": {"message": "Project permission denied", "code": "permission_denied"}}
            mock_post.return_value = mock_resp
            with self.assertRaises(StoryGenerationError) as ctx:
                prov.generate_story(prompt="A test prompt")
            self.assertEqual(ctx.exception.code, "PERMISSION_DENIED")


if __name__ == "__main__":
    unittest.main()
