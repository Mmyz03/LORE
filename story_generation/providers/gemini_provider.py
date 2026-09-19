"""
LORE — Google Gemini AI Story Provider
"""

import logging
import requests
from .base import BaseStoryProvider, StoryGenerationError
from ..prompts import build_story_prompt

logger = logging.getLogger("lore.gemini_provider")

DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"


class GeminiStoryProvider(BaseStoryProvider):
    """
    Google Gemini API Story Provider via standard REST requests.
    Supports Gemini 1.5 Flash, Gemini 1.5 Pro, Gemini 2.0 Flash, etc.
    """

    def __init__(self, api_key: str = None, model: str = None):
        super().__init__(api_key=api_key, model=model or DEFAULT_GEMINI_MODEL)

    def generate_story(
        self,
        prompt: str = "",
        category: str = None,
        length: str = "default",
        is_another: bool = False,
        previous_titles: list = None,
        **kwargs
    ) -> dict:
        if not self.is_available():
            raise StoryGenerationError(
                "Story generation is temporarily unavailable.",
                code="NO_API_KEY",
                status_code=503
            )

        system_instruction, user_content = build_story_prompt(
            user_prompt=prompt,
            category=category,
            length=length,
            is_another=is_another,
            previous_titles=previous_titles
        )

        # Use header for authentication to prevent API key exposure in URLs or query strings
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": str(self.api_key).strip()
        }

        # Adjust temperature for diversity when generating another story
        temperature = 0.95 if is_another else 0.82

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_content}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "topP": 0.95,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json"
            }
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=60
            )

            if response.status_code != 200:
                err_details = "Unknown error"
                try:
                    err_json = response.json()
                    err_details = err_json.get("error", {}).get("message", response.text[:200])
                except Exception:
                    err_details = response.text[:200]

                logger.error(
                    f"[LORE Gemini] API Error HTTP {response.status_code} on model '{self.model}': {err_details}"
                )

                if response.status_code in (400, 401, 403) and ("API_KEY" in err_details or "PERMISSION_DENIED" in err_details):
                    raise StoryGenerationError("Story generation is temporarily unavailable. (Invalid or unauthorized API key)", code="INVALID_API_KEY", status_code=503)
                elif response.status_code == 404:
                    raise StoryGenerationError(f"Model '{self.model}' was not found. Please verify your STORY_AI_MODEL setting.", code="MODEL_NOT_FOUND", status_code=500)
                elif response.status_code == 429:
                    raise StoryGenerationError("AI rate limit reached. Please wait a moment and try again.", code="RATE_LIMIT", status_code=429)

                raise StoryGenerationError("LORE couldn't create the story right now. Please try again.", code="PROVIDER_ERROR")

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                logger.error(f"[LORE Gemini] Zero candidates returned. Prompt feedback: {data.get('promptFeedback')}")
                raise StoryGenerationError("LORE couldn't create the story right now. Please try again.", code="EMPTY_RESPONSE")

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                logger.error(f"[LORE Gemini] Candidate content had no parts. Finish reason: {candidates[0].get('finishReason')}")
                raise StoryGenerationError("LORE couldn't create the story right now. Please try again.", code="EMPTY_CONTENT")

            raw_text = parts[0].get("text", "")
            parsed_story = self.clean_and_parse_json(raw_text)
            parsed_story["model"] = self.model
            parsed_story["provider"] = "Google Gemini"

            return parsed_story

        except requests.Timeout:
            logger.error(f"[LORE Gemini] Request timed out after 60s for model '{self.model}'.")
            raise StoryGenerationError("Story generation timed out. Please try again.", code="TIMEOUT", status_code=504)
        except requests.RequestException as e:
            logger.error(f"[LORE Gemini] Network connection error: {type(e).__name__}")
            raise StoryGenerationError("LORE couldn't create the story right now. Please try again.", code="NETWORK_ERROR")
        except StoryGenerationError:
            raise
        except Exception as e:
            logger.error(f"[LORE Gemini] Unexpected processing exception: {e}", exc_info=True)
            raise StoryGenerationError("LORE couldn't create the story right now. Please try again.", code="UNKNOWN_ERROR")
