"""
LORE — Master StoryGenerator Controller & Factory
"""

import os
import re
import logging
from .providers.base import BaseStoryProvider, StoryGenerationError
from .providers.gemini_provider import GeminiStoryProvider
from .providers.openai_provider import OpenAIStoryProvider

logger = logging.getLogger("lore.story_generator")


def load_env_file(root_dir: str = None):
    """
    Robust zero-dependency .env and .env.local loader.
    Populates os.environ with variables defined in .env files.
    Handles UTF-8 BOM, 'export', comments, quotes, and hot updates.
    """
    if not root_dir:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    candidates = [
        os.path.join(root_dir, ".env"),
        os.path.join(root_dir, ".env.local"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.getcwd(), ".env.local"),
        os.path.join(root_dir, "app", ".env")
    ]

    loaded_paths = set()
    for env_path in candidates:
        norm_path = os.path.normpath(env_path)
        if norm_path in loaded_paths:
            continue
        if os.path.isfile(norm_path):
            loaded_paths.add(norm_path)
            try:
                with open(norm_path, "r", encoding="utf-8-sig") as f:
                    for line in f:
                        line = line.lstrip("\ufeff").strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        # Strip leading 'export ' if present
                        if line.startswith("export ") or line.startswith("export\t"):
                            line = line.split(maxsplit=1)[1].strip()
                        if "=" not in line:
                            continue

                        key, val = line.split("=", 1)
                        key = key.lstrip("\ufeff").strip("'\" \t")
                        val = val.strip()

                        # Strip inline comments or quotes
                        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                            val = val[1:-1]
                        elif val.startswith('"') and '"' in val[1:]:
                            val = val[1:val.index('"', 1)]
                        elif val.startswith("'") and "'" in val[1:]:
                            val = val[1:val.index("'", 1)]
                        else:
                            if " #" in val:
                                val = val.split(" #", 1)[0].strip()
                            elif "\t#" in val:
                                val = val.split("\t#", 1)[0].strip()
                            val = val.strip("'\"")

                        # Populate environment variable if not already set in process environment
                        if key and val and key not in os.environ:
                            os.environ[key] = val

                logger.info(f"[LORE] Loaded environment configuration from {os.path.basename(norm_path)}")
            except Exception as e:
                logger.warning(f"[LORE] Could not parse env file {norm_path}: {e}")


# Run initial env scan
load_env_file()


class StoryGenerator:
    """
    Master Story Generation Controller.
    Manages provider selection, environment configuration, generation workflows,
    genre preset dispatch, length calibration, and anti-repetition memory.
    """

    def __init__(self, provider: BaseStoryProvider = None):
        self._custom_provider = provider
        self.provider = provider or self._resolve_provider()

    def _resolve_provider(self) -> BaseStoryProvider:
        """
        Detects and initializes the active AI provider based on environment variables.
        Supports OpenAI (default), Gemini, Groq, OpenRouter, and DeepSeek.
        """
        load_env_file()

        provider_name = (os.getenv("STORY_AI_PROVIDER") or "").strip().lower()
        model = (os.getenv("STORY_AI_MODEL") or "").strip() or None
        custom_base_url = (os.getenv("STORY_AI_BASE_URL") or "").strip() or None

        # Universal key override
        story_ai_key = (os.getenv("STORY_AI_API_KEY") or "").strip()

        # Provider-specific key lookups
        openai_key = story_ai_key or (os.getenv("OPENAI_API_KEY") or "").strip()
        gemini_key = story_ai_key or (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        groq_key = story_ai_key or (os.getenv("GROQ_API_KEY") or "").strip()
        openrouter_key = story_ai_key or (os.getenv("OPENROUTER_API_KEY") or "").strip()
        deepseek_key = story_ai_key or (os.getenv("DEEPSEEK_API_KEY") or "").strip()

        # 1. Explicit provider configuration
        if provider_name == "openai":
            openai_model = model or "gpt-4o-mini"
            base_url = custom_base_url or "https://api.openai.com/v1"
            logger.info(f"[LORE AI] Initializing OpenAI Provider (model: {openai_model})")
            return OpenAIStoryProvider(api_key=openai_key, model=openai_model, base_url=base_url)

        if provider_name in ("gemini", "google"):
            gemini_model = model or "gemini-1.5-flash"
            logger.info(f"[LORE AI] Initializing Gemini Provider (model: {gemini_model})")
            return GeminiStoryProvider(api_key=gemini_key, model=gemini_model)

        if provider_name == "groq":
            groq_model = model or "llama-3.3-70b-versatile"
            base_url = custom_base_url or "https://api.groq.com/openai/v1"
            logger.info(f"[LORE AI] Initializing Groq Provider (model: {groq_model})")
            return OpenAIStoryProvider(api_key=groq_key, model=groq_model, base_url=base_url)

        if provider_name == "openrouter":
            or_model = model or "meta-llama/llama-3.3-70b-instruct"
            base_url = custom_base_url or "https://openrouter.ai/api/v1"
            logger.info(f"[LORE AI] Initializing OpenRouter Provider (model: {or_model})")
            return OpenAIStoryProvider(api_key=openrouter_key, model=or_model, base_url=base_url)

        if provider_name == "deepseek":
            ds_model = model or "deepseek-chat"
            base_url = custom_base_url or "https://api.deepseek.com/v1"
            logger.info(f"[LORE AI] Initializing DeepSeek Provider (model: {ds_model})")
            return OpenAIStoryProvider(api_key=deepseek_key, model=ds_model, base_url=base_url)

        # 2. Auto-detection if STORY_AI_PROVIDER is not explicitly specified
        if story_ai_key:
            if story_ai_key.startswith("gsk_"):
                return OpenAIStoryProvider(api_key=story_ai_key, model=model or "llama-3.3-70b-versatile", base_url=custom_base_url or "https://api.groq.com/openai/v1")
            if story_ai_key.startswith("sk-or-"):
                return OpenAIStoryProvider(api_key=story_ai_key, model=model or "meta-llama/llama-3.3-70b-instruct", base_url=custom_base_url or "https://openrouter.ai/api/v1")
            if story_ai_key.startswith("AIza"):
                return GeminiStoryProvider(api_key=story_ai_key, model=model or "gemini-1.5-flash")
            return OpenAIStoryProvider(api_key=story_ai_key, model=model or "gpt-4o-mini", base_url=custom_base_url or "https://api.openai.com/v1")

        # Inferred from specific keys when STORY_AI_PROVIDER is unset (OpenAI prioritized as default)
        if openai_key:
            return OpenAIStoryProvider(api_key=openai_key, model=model or "gpt-4o-mini", base_url=custom_base_url or "https://api.openai.com/v1")
        if gemini_key:
            return GeminiStoryProvider(api_key=gemini_key, model=model or "gemini-1.5-flash")
        if groq_key:
            return OpenAIStoryProvider(api_key=groq_key, model=model or "llama-3.3-70b-versatile", base_url=custom_base_url or "https://api.groq.com/openai/v1")
        if openrouter_key:
            return OpenAIStoryProvider(api_key=openrouter_key, model=model or "meta-llama/llama-3.3-70b-instruct", base_url=custom_base_url or "https://openrouter.ai/api/v1")
        if deepseek_key:
            return OpenAIStoryProvider(api_key=deepseek_key, model=model or "deepseek-chat", base_url=custom_base_url or "https://api.deepseek.com/v1")

        # Default fallback: OpenAI with empty key
        openai_model = model or "gpt-4o-mini"
        base_url = custom_base_url or "https://api.openai.com/v1"
        logger.info(f"[LORE AI] Initializing OpenAI Provider (model: {openai_model})")
        return OpenAIStoryProvider(api_key="", model=openai_model, base_url=base_url)

    def refresh_provider(self):
        """Re-evaluates environment variables and reconfigures provider if no custom provider was set."""
        if self._custom_provider is None:
            self.provider = self._resolve_provider()

    def is_available(self) -> bool:
        """Checks if the story generation system has valid credentials."""
        self.refresh_provider()
        return self.provider is not None and self.provider.is_available()

    def get_status(self) -> dict:
        """Returns safe status metadata about the generation engine (zero secrets)."""
        self.refresh_provider()
        return {
            "available": self.is_available(),
            "provider": self.provider.__class__.__name__ if self.provider else "None",
            "model": getattr(self.provider, "model", "Unknown") if self.provider else "None"
        }

    def generate(
        self,
        prompt: str = "",
        category: str = None,
        length: str = "default",
        is_another: bool = False,
        previous_titles: list = None
    ) -> dict:
        """
        Executes AI story generation with input validation and error wrapping.
        Accepts natural-language prompts, category presets, length requirements,
        and session anti-repetition memory.
        """
        prompt_clean = (prompt or "").strip()
        category_clean = (category or "").strip()
        length_clean = (length or "default").strip()

        if not prompt_clean and not category_clean:
            raise StoryGenerationError(
                "Please describe the story or choose a genre category preset.",
                code="EMPTY_PROMPT",
                status_code=400
            )

        if len(prompt_clean) > 3000:
            prompt_clean = prompt_clean[:3000]

        # Dynamic credential check
        if not self.is_available():
            active_provider = self.provider.__class__.__name__ if self.provider else "AI Provider"
            logger.warning(
                f"[LORE AI] Story generation requested but no API key is configured for {active_provider}. "
                "Set OPENAI_API_KEY (or STORY_AI_API_KEY) in environment or .env."
            )
            raise StoryGenerationError(
                "Story generation requires an active AI provider key. Please configure OPENAI_API_KEY (or STORY_AI_API_KEY) in your environment or .env file.",
                code="NO_API_KEY",
                status_code=503
            )

        return self.provider.generate_story(
            prompt=prompt_clean,
            category=category_clean if category_clean else None,
            length=length_clean,
            is_another=is_another,
            previous_titles=previous_titles or []
        )
