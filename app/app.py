"""
LORE — AI-Powered Story Generation Platform
Module: Flask Web Backend & REST API
"""

import os
import sys
import time
import logging
from flask import Flask, render_template, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("lore.app")

# Resolve robust absolute paths relative to this file
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
TEMPLATE_DIR = os.path.join(APP_DIR, "templates")
STATIC_DIR = os.path.join(APP_DIR, "static")

# Ensure project root is in sys.path for cross-module imports
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from story_generation.generator import StoryGenerator
from story_generation.providers.base import StoryGenerationError

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR
)

# AI Genre Presets
CATEGORY_PRESETS = [
    {
        "id": "mystery",
        "name": "Mystery",
        "icon": "🔍",
        "tagline": "Secrets, clues, suspects, and deduction",
        "sample_prompt": "A locked-room mystery during a storm at an isolated seaside lighthouse."
    },
    {
        "id": "horror",
        "name": "Horror",
        "icon": "👻",
        "tagline": "Atmospheric dread, psychological chills, and the unknown",
        "sample_prompt": "An antique mirror reflecting a room that does not exist."
    },
    {
        "id": "romance",
        "name": "Romance",
        "icon": "💖",
        "tagline": "Devotion, heartfelt bonds, and tender connections",
        "sample_prompt": "Two estranged sweethearts who cross paths on a midnight train through the Alps."
    },
    {
        "id": "fantasy",
        "name": "Fantasy",
        "icon": "🔮",
        "tagline": "Mythical realms, ancient wonder, and enchanted lore",
        "sample_prompt": "An apprentice cartographer who discovers an uncharted kingdom living inside a storm."
    },
    {
        "id": "adventure",
        "name": "Adventure",
        "icon": "🧭",
        "tagline": "Expeditions, wilderness survival, and daring quests",
        "sample_prompt": "A lone traveler in the sub-zero Yukon fighting for survival against the frost."
    },
    {
        "id": "sci-fi",
        "name": "Science Fiction",
        "icon": "🚀",
        "tagline": "Cosmic frontiers, futuristic technology, and deep space",
        "sample_prompt": "A lone engineer on a deep-space outpost receives a transmission sent from yesterday."
    },
    {
        "id": "thriller",
        "name": "Thriller",
        "icon": "⚡",
        "tagline": "Cat-and-mouse suspense, ticking clocks, and high stakes",
        "sample_prompt": "A cybersecurity agent who discovers an intruder operating from inside their own safehouse."
    },
    {
        "id": "comedy",
        "name": "Comedy",
        "icon": "🎭",
        "tagline": "Wit, playful mischief, and delightful irony",
        "sample_prompt": "A chaotic dinner party where every guest is secretly impersonating a royal diplomat."
    },
    {
        "id": "emotional",
        "name": "Emotional",
        "icon": "🍃",
        "tagline": "Bittersweet memories, human empathy, and heartfelt depth",
        "sample_prompt": "An aging violinist preparing to perform one final secret waltz for his lost love."
    },
    {
        "id": "friendship",
        "name": "Friendship",
        "icon": "🤝",
        "tagline": "Loyalty, lifelong promises, and unshakable bonds",
        "sample_prompt": "Two lifelong friends returning to their hometown to fulfill a pact made thirty years ago."
    },
    {
        "id": "moral",
        "name": "Moral",
        "icon": "⚖️",
        "tagline": "Timeless wisdom, ethical crossroads, and profound fables",
        "sample_prompt": "A proud merchant who learns the unexpected true cost of getting everything he desired."
    },
    {
        "id": "bedtime",
        "name": "Bedtime",
        "icon": "🌙",
        "tagline": "Gentle, tranquil, and soothing nighttime tales",
        "sample_prompt": "A quiet journey of a guardian star guiding woodland creatures through a peaceful forest."
    }
]

# Global AI Generator Instance
GENERATOR = None


def get_generator() -> StoryGenerator:
    """Lazily initializes and returns the StoryGenerator controller."""
    global GENERATOR
    if GENERATOR is None:
        GENERATOR = StoryGenerator()
        logger.info(f"[+] StoryGenerator initialized. Status: {GENERATOR.get_status()}")
    return GENERATOR


# Initialize at boot
get_generator()


@app.route("/")
def index():
    """Renders the LORE AI Story Generation web application."""
    return render_template("index.html")


# =============================================================================
# AI STORY GENERATION REST API
# =============================================================================

@app.route("/api/generate-story", methods=["POST"])
def generate_story():
    """
    Primary AI Story Generation Endpoint.
    Receives JSON:
    {
        "prompt": str (optional if category is present),
        "category": str (optional),
        "length": str (optional: "default", "short", "long", or custom),
        "is_another": bool (optional),
        "previous_titles": list (optional)
    }
    Returns JSON:
    {
        "success": true,
        "story": {
            "title": str,
            "genre": str,
            "summary": str,
            "content": str,
            "tags": list[str],
            "word_count": int,
            "reading_time_min": int,
            "model": str,
            "provider": str,
            "latency_ms": float
        }
    }
    """
    generator = get_generator()

    data = request.get_json() or {}
    prompt = (data.get("prompt") or "").strip()
    category = (data.get("category") or "").strip()
    length = (data.get("length") or "default").strip()
    is_another = bool(data.get("is_another", False))
    previous_titles = data.get("previous_titles", [])
    if not isinstance(previous_titles, list):
        previous_titles = []

    if not prompt and not category:
        return jsonify({
            "success": False,
            "error": "Please describe the story or select a genre preset.",
            "code": "EMPTY_PROMPT"
        }), 400

    if len(prompt) > 3000:
        prompt = prompt[:3000]

    start_time = time.time()

    try:
        story = generator.generate(
            prompt=prompt,
            category=category if category else None,
            length=length,
            is_another=is_another,
            previous_titles=previous_titles
        )
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        story["latency_ms"] = elapsed_ms

        return jsonify({
            "success": True,
            "story": story
        })

    except StoryGenerationError as sge:
        logger.error(f"[LORE AI Generation Error] {sge.code}: {sge.message}")
        return jsonify({
            "success": False,
            "error": sge.message,
            "code": sge.code
        }), sge.status_code

    except Exception as e:
        logger.error(f"[LORE Unexpected Generation Error] {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "LORE couldn't create the story right now. Please try again.",
            "code": "SERVER_ERROR"
        }), 500


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Returns the list of supported AI story genre presets and metadata."""
    return jsonify({
        "status": "success",
        "total": len(CATEGORY_PRESETS),
        "categories": CATEGORY_PRESETS
    })


@app.route("/api/info", methods=["GET"])
def get_info():
    """Returns application status, AI provider status, and engine readiness."""
    generator = get_generator()
    gen_status = generator.get_status() if generator else {"available": False, "provider": "None"}

    return jsonify({
        "status": "success",
        "engine": "LORE AI Story Generation Platform",
        "ai_generation_available": gen_status.get("available", False),
        "ai_provider": gen_status.get("provider", "None"),
        "ai_model": gen_status.get("model", "None"),
        "total_presets": len(CATEGORY_PRESETS),
        "features": [
            "AI Story Generation (LLM)",
            "Genre Presets & Custom Natural Language Requests",
            "Dynamic Length Calibration (~2 Pages Normal, Quick, Extended)",
            "Audiobook Voice Narration (Web Speech API)",
            "Anti-Repetition Session Memory",
            "Cross-Platform Copy"
        ]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
