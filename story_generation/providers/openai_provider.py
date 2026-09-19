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
        clean_key = str(api_key).strip().strip("'\"").strip() if api_key else None
        super().__init__(api_key=clean_key, model=model or DEFAULT_OPENAI_MODEL)
        self.base_url = (base_url or os.getenv("STORY_AI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")

    def is_available(self) -> bool:
        """Returns True if a non-empty, non-placeholder API key is configured."""
        if not self.api_key:
            return False
        k = str(self.api_key).strip().lower()
        if not k:
            return False
        # Guard against placeholder values in .env files
        if any(p in k for p in ["your_", "your-", "placeholder", "example", "insert_", "enter_", "replace_"]):
            return False
        return len(k) >= 10

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

        clean_token = str(self.api_key).strip().strip("'\"").strip()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {clean_token}"
        }

        # Determine token limit parameter name (newer reasoning models like o1/o3 use max_completion_tokens)
        is_reasoning_model = any(self.model.startswith(m) for m in ["o1", "o3", "o4"])

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            "temperature": None if is_reasoning_model else temperature,
            "max_tokens": None if is_reasoning_model else 4096,
            "max_completion_tokens": 4096 if is_reasoning_model else None,
            "response_format": {"type": "json_object"} if ("gpt-4" in self.model or "gpt-3.5" in self.model) else None
        }

        # Clean out None fields
        payload = {k: v for k, v in payload.items() if v is not None}

        # Safe diagnostic logging (NEVER exposing the secret key)
        key_len = len(clean_token)
        key_prefix = clean_token[:7] if key_len >= 7 else clean_token[:3]
        logger.info(
            f"[LORE OpenAI Provider] Dispatching request to {url} (model: {self.model}, key_len: {key_len}, prefix: {key_prefix}...)"
        )

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)

            if response.status_code != 200:
                err_details = "Unknown error"
                err_code = None
                err_type = None
                try:
                    err_json = response.json()
                    error_obj = err_json.get("error", {})
                    if isinstance(error_obj, dict):
                        err_details = error_obj.get("message", response.text[:200])
                        err_code = error_obj.get("code")
                        err_type = error_obj.get("type")
                    else:
                        err_details = str(error_obj)
                except Exception:
                    err_details = response.text[:200]

                logger.error(
                    f"[LORE OpenAI Provider] HTTP {response.status_code} (type: {err_type}, code: {err_code}) on model '{self.model}': {err_details}"
                )

                if response.status_code == 401:
                    raise StoryGenerationError(
                        "The configured OPENAI_API_KEY was rejected by OpenAI. Please verify your API key in environment or .env.",
                        code="INVALID_API_KEY",
                        status_code=503
                    )
                elif response.status_code == 429:
                    if err_code == "insufficient_quota" or "quota" in str(err_details).lower():
                        raise StoryGenerationError(
                            "OpenAI account quota exceeded. Please check your OpenAI billing plan and credits at platform.openai.com.",
                            code="QUOTA_EXCEEDED",
                            status_code=429
                        )
                    raise StoryGenerationError(
                        "OpenAI rate limit reached. Please wait a moment and try again.",
                        code="RATE_LIMIT",
                        status_code=429
                    )
                elif response.status_code == 404 or err_code == "model_not_found":
                    raise StoryGenerationError(
                        f"Model '{self.model}' was not found or your OpenAI key does not have access to it. Please verify your STORY_AI_MODEL setting.",
                        code="MODEL_NOT_FOUND",
                        status_code=404
                    )
                elif response.status_code == 403 or err_code == "permission_denied":
                    raise StoryGenerationError(
                        f"Access to OpenAI model '{self.model}' was denied. Your API key or Project does not have permission for this model.",
                        code="PERMISSION_DENIED",
                        status_code=403
                    )
                elif response.status_code == 400:
                    raise StoryGenerationError(
                        f"OpenAI request validation failed: {err_details}",
                        code="INVALID_REQUEST",
                        status_code=400
                    )
                elif response.status_code >= 500:
                    raise StoryGenerationError(
                        "OpenAI servers are currently experiencing issues. Please try again in a few moments.",
                        code="OPENAI_SERVER_ERROR",
                        status_code=502
                    )

                raise StoryGenerationError(
                    f"OpenAI service error: {err_details}",
                    code="PROVIDER_ERROR",
                    status_code=response.status_code
                )

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                logger.error("[LORE OpenAI Provider] Zero choices returned by model.")
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
            raise StoryGenerationError("Network connection error to AI provider. Please try again.", code="NETWORK_ERROR", status_code=503)
        except StoryGenerationError:
            raise
        except Exception as e:
            logger.error(f"[LORE OpenAI Provider] Unexpected processing exception: {e}", exc_info=True)
            raise StoryGenerationError("LORE couldn't create the story right now. Please try again.", code="UNKNOWN_ERROR", status_code=500)
