# AGENTS.md — Agent & Developer Guide for LORE

Welcome to **LORE** (*Stories worth getting lost in*). This document serves as the authoritative operational, architectural, and development guideline for AI coding assistants and developers collaborating on this repository.

---

## 🏛️ Project Overview

**LORE** is a modern, full-stack **AI-Powered Story Generation Platform**.
- **User Experience**: Readers select an AI genre category preset (e.g. Mystery, Horror, Romance, Sci-Fi, Fantasy, etc.), describe their custom narrative ideas (characters, setting, atmosphere, twists), or combine both.
- **Narrative Synthesis**: LORE orchestrates requests to state-of-the-art LLMs (Google Gemini, OpenAI, Groq, OpenRouter) to write complete, publication-quality short stories with a full 6-stage narrative arc (Hook, Exposition, Conflict, Rising Tension, Climax, Resolution).
- **Immersion & Audio**: In-browser Web Speech API audio narration (`speech.js`) provides natural voice playback, 8-speed controls, 10-second skip granularity, and paragraph synchronization.
- **Novelty on Regeneration**: "Generate Another Story" preserves active thematic constraints while commanding the AI to produce completely new plots, distinct characters, and fresh resolutions.

---

## 📂 Repository Structure

```
LORE/
├── app/
│   ├── app.py                     # Flask server & REST API endpoints
│   ├── templates/
│   │   └── index.html             # Single-page AI Story Generator interface
│   └── static/
│       ├── style.css              # Dark luxury theme (#050507, champagne gold, glassmorphism)
│       ├── script.js              # Frontend application controller & preset dispatcher
│       ├── speech.js              # Web Speech API audiobook narration engine
│       └── assets/                # SVGs & brand icons (lore-emblem.svg)
│
├── story_generation/
│   ├── __init__.py
│   ├── generator.py               # StoryGenerator master controller & provider dispatcher
│   ├── prompts.py                 # System prompts, genre guidelines, length calibration & JSON schema
│   └── providers/
│       ├── base.py                # BaseStoryProvider interface, JSON parser & error types
│       ├── gemini_provider.py     # Google Gemini REST API integration
│       └── openai_provider.py     # OpenAI / Groq / OpenRouter API integration
│
├── tests/                         # Automated test suite
│   ├── test_story_generation.py   # AI generator unit, schema, length & provider tests
│   ├── test_vercel_entrypoint.py  # Server routing, endpoints & presets tests
│   └── test_mobile_and_perf.py    # Performance, asset integrity & responsive tokens
│
├── requirements.txt               # Core Python dependencies (flask, requests)
└── README.md                      # Public project documentation
```

---

## 🛠️ Environment & Setup

### Requirements
- **Python**: 3.10+ (On Windows, use the `py` launcher)
- **Key Libraries**: `flask`, `requests`

### Installation
```bash
# Windows
py -m pip install -r requirements.txt

# Linux / macOS
pip install -r requirements.txt
```

### Environment Variables
Configure the following in your environment or `.env` file when working with AI story generation:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `STORY_AI_PROVIDER` | AI provider name (`openai`, `gemini`, `groq`, `openrouter`, `deepseek`) | `openai` |
| `OPENAI_API_KEY` / `STORY_AI_API_KEY` | Provider API key | *(None — Generation disabled)* |
| `STORY_AI_MODEL` | Model ID (e.g., `gpt-4o-mini`, `gpt-4o`, `gemini-1.5-flash`, `llama-3.3-70b-versatile`) | `gpt-4o-mini` |
| `STORY_AI_BASE_URL` | Optional custom base URL for OpenAI-compatible proxies | `https://api.openai.com/v1` |

---

## 🚀 Key Commands

### 1. Run the Web Application
```bash
py app/app.py
# (or python app/app.py on Linux/macOS)
```
Default URL: `http://127.0.0.1:5000`

### 2. Run the Automated Test Suite
```bash
py -m unittest discover -s tests
# (or python -m unittest discover -s tests)
```

---

## 📐 Architecture & Coding Conventions

### 1. AI Story Generation Output Schema
All AI providers in `story_generation/providers/` enforce and output JSON matching the following schema:
```json
{
  "title": "A Compelling Title",
  "genre": "Genre Name",
  "summary": "1-2 sentence synopsis summarizing the story.",
  "content": "Paragraph 1\n\nParagraph 2\n\nParagraph 3...",
  "tags": ["Tag1", "Tag2", "Tag3", "Tag4"]
}
```

### 2. Length Calibration & Presets
- **Normal (~2 Pages)**: Default length (~900–1,400 words, 4–6 rich paragraphs).
- **Quick (~1 Page)**: Concise short story (~450–750 words, 3–4 paragraphs).
- **Extended (3–5 Pages)**: Expansive narrative (~1,800–2,500 words, 6–10 paragraphs).
- **Custom Constraints**: Explicit word/page limits requested in natural language are passed directly into prompt instructions.

### 3. Graceful Error Handling
- When `STORY_AI_API_KEY` is missing or invalid, the endpoint returns a structured JSON error response (`NO_API_KEY`, `INVALID_API_KEY`, `RATE_LIMIT`) with appropriate HTTP status codes (400, 503, 504), never raising unhandled 500 exceptions or leaking API keys.

### 4. Frontend Standards
- **Styling**: Vanilla CSS (`app/static/style.css`) using CSS variables for theme tokens (dark luxury palette: deep obsidian `#050507`, champagne gold accents `#d4af37`, subtle glassmorphism borders).
- **Scripts**: Modular vanilla JavaScript (`script.js`, `speech.js`).
- **Audiobook Voice Narration**: Uses browser-native Web Speech API (`speechSynthesis`) with play, pause, resume, paragraph highlighting, and 10s skip controls.

---

## 🧪 Testing Guidelines for Agents

When making changes to this repository:
1. **Always run unit tests** before and after making functional modifications:
   ```bash
   py -m unittest discover -s tests
   ```
2. **Mock External API Calls**: Never make live external HTTP calls in unit tests. Use `MockFullArcStoryProvider` or `unittest.mock` to mock API responses.
3. **Preserve Documentation & Comments**: Keep existing docstrings and comments intact unless directly updating the associated functionality.
