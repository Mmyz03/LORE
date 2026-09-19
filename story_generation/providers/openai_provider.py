"""
LORE — OpenAI-Compatible AI Story Provider (OpenAI, Groq, OpenRouter, etc.)
"""

import os
import logging
import requests
from .base import BaseStoryProvider, StoryGenerationError
from ..prompts import build_story_prompt

logger = logging.getLogger("lore.openai_provider")

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class OpenAIStoryProvider(BaseStoryProvider):
    """
    OpenAI-compatible Chat Completion Provider.
    Works seamlessly with OpenAI, Groq, OpenRouter, DeepSeek, and local endpoints.
    """

    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        clean_key = str(api_key).strip() if api_key else None
        super().__init__(api_key=clean_key, model=model or DEFAULT_OPENAI_MODEL)
        self.base_url = (base_url or os.getenv("STORY_AI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")

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
                "Story generation requires an active AI provider key. Please configure OPENAI_API_KEY (or STORY_AI_API_KEY) in your environment or .env file.",
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

        url = f"{self.base_url}/chat/completions"
        temperature = 0.92 if is_another else 0.80

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {str(self.api_key).strip()}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            "temperature": temperature,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"} if ("gpt-4" in self.model or "gpt-3.5" in self.model) else None
        }

        # Clean out None fields
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)

            if response.status_code != 200:
                err_details = "Unknown error"
                try:
                    err_json = response.json()
                    err_details = err_json.get("error", {}).get("message", response.text[:200])
                except Exception:
                    err_details = response.text[:200]

                logger.error(
                    f"[LORE OpenAI Provider] HTTP {response.status_code} on model '{self.model}': {err_details}"
                )

                if response.status_code == 401:
                    raise StoryGenerationError("The configured OPENAI_API_KEY was rejected by OpenAI. Please check your key in your .env file or environment.", code="INVALID_API_KEY", status_code=503)
                elif response.status_code == 404:
                    raise StoryGenerationError(f"Model '{self.model}' was not found. Please verify your STORY_AI_MODEL setting.", code="MODEL_NOT_FOUND", status_code=500)
                elif response.status_code == 429:
                    raise StoryGenerationError("AI rate limit reached. Please wait a moment and try again.", code="RATE_LIMIT", status_code=429)

                raise StoryGenerationError("LORE couldn't create the story right now. Please try again.", code="PROVIDER_ERROR")

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                logger.error(f"[LORE OpenAI Provider] Zero choices returned.")
                raise StoryGenerationError("LORE couldn't create the story right now. Please try again.", code="EMPTY_CHOICES")

            raw_text = choices[0].get("message", {}).get("content", "")
            parsed_story = self.clean_and_parse_json(raw_text)
            parsed_story["model"] = self.model
            parsed_story["provider"] = "OpenAI" if "openai.com" in self.base_url else "OpenAI-Compatible"

            return parsed_story

        except requests.Timeout:
            logger.error(f"[LORE OpenAI Provider] Request timed out after 60s on model '{self.model}'.")
            raise StoryGenerationError("Story generation timed out. Please try again.", code="TIMEOUT", status_code=504)
        except requests.RequestException as e:
            logger.error(f"[LORE OpenAI Provider] Network connection error: {type(e).__name__}")
            raise StoryGenerationError("LORE couldn't create the story right now. Please try again.", code="NETWORK_ERROR")
        except StoryGenerationError:
            raise
        except Exception as e:
            logger.error(f"[LORE OpenAI Provider] Unexpected processing exception: {e}", exc_info=True)
            raise StoryGenerationError("LORE couldn't create the story right now. Please try again.", code="UNKNOWN_ERROR")
