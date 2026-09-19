"""
LORE — Base AI Story Provider Interface & Response Parser
"""

import re
import json
import logging

logger = logging.getLogger("lore.story_generation")


class StoryGenerationError(Exception):
    """Raised when story generation encounters an unrecoverable failure."""
    def __init__(self, message: str, code: str = "GENERATION_FAILED", status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class BaseStoryProvider:
    """
    Abstract interface for AI Story Generation Providers.
    """

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key
        self.model = model

    def is_available(self) -> bool:
        """Returns True if the provider has necessary API credentials configured."""
        return bool(self.api_key and str(self.api_key).strip())

    def generate_story(
        self,
        prompt: str = "",
        category: str = None,
        length: str = "default",
        is_another: bool = False,
        previous_titles: list = None,
        **kwargs
    ) -> dict:
        """
        Generates a complete story from a user prompt, category preset, and length specification.
        Returns a dictionary matching the LORE story schema:
        {
            "title": str,
            "genre": str,
            "summary": str,
            "content": str,
            "tags": list[str],
            "word_count": int,
            "reading_time_min": int,
            "model": str,
            "provider": str
        }
        """
        raise NotImplementedError("Subclasses must implement generate_story()")

    @staticmethod
    def clean_and_parse_json(raw_response: str) -> dict:
        """
        Extracts and parses JSON from raw LLM output, handling markdown blocks,
        leading/trailing commentary, and common escaping glitches.
        """
        if not raw_response or not isinstance(raw_response, str):
            raise StoryGenerationError("Received empty response from AI model.")

        text = raw_response.strip()

        # Remove markdown fences if present
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()

        # If there are surrounding braces, isolate the outermost JSON object
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            text = text[brace_start:brace_end + 1]

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            try:
                cleaned_text = re.sub(r'(?<!\\)\n', r'\\n', text)
                parsed = json.loads(cleaned_text)
            except Exception as e:
                logger.error(f"[LORE AI] Failed to parse model JSON: {e}\nRaw output: {raw_response[:400]}")
                raise StoryGenerationError("Model returned invalid structured output format.", code="INVALID_JSON")

        # Validate required schema fields
        if not isinstance(parsed, dict):
            raise StoryGenerationError("Model response was not a JSON dictionary.")

        title = str(parsed.get("title", "")).strip() or "An Untitled Tale"
        genre = str(parsed.get("genre", "")).strip() or "Story"
        summary = str(parsed.get("summary", "")).strip()
        content = str(parsed.get("content", "")).strip()
        tags = parsed.get("tags", [])
        if not isinstance(tags, list):
            tags = [str(tags)] if tags else []
        tags = [str(t).strip() for t in tags if str(t).strip()]

        if not content:
            raise StoryGenerationError("Story content was empty in the AI response.")

        # Compute word count and reading time
        words = content.split()
        word_count = len(words)
        reading_time_min = max(1, round(word_count / 200))

        if not summary:
            # Generate a brief 2-sentence summary from the first 2 sentences if missing
            summary_sentences = re.split(r'(?<=[.!?])\s+', content)[:2]
            summary = " ".join(summary_sentences)

        return {
            "title": title,
            "genre": genre,
            "summary": summary,
            "content": content,
            "tags": tags,
            "word_count": word_count,
            "reading_time_min": reading_time_min
        }
