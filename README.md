# LORE — Stories worth getting lost in.
### AI-Powered Story Generation Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-lightgrey.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**LORE** is a modern storytelling platform that transforms natural-language ideas and genre presets into complete, publication-quality original short stories powered by Google Gemini and OpenAI models.

---

## 📖 Table of Contents
1. [Core Features](#-core-features)
2. [Genre Presets](#-genre-presets)
3. [Story Length Calibration](#-story-length-calibration)
4. [Audiobook Voice Narration](#-audiobook-voice-narration)
5. [Environment Variables & Configuration](#-environment-variables--configuration)
6. [Project Structure](#-project-structure)
7. [Step-by-Step Setup & Execution](#-step-by-step-setup--execution)
8. [Automated Test Suite](#-automated-test-suite)
9. [License](#-license)

---

## 🏛️ Core Features

- **Rich Narrative Structure**: Stories are generated with a complete 6-stage arc — compelling hook, exposition, inciting conflict, rising tension, dramatic climax, and meaningful resolution.
- **Strict Output Schema**: Models return clean structured JSON containing title, genre, summary synopsis, reading time, word count, tags, and formatted paragraphs.
- **Provider Agnostic**: Pluggable backend supporting Google Gemini (`gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash`), OpenAI (`gpt-4o`, `gpt-4o-mini`), Groq (`llama-3.3-70b-versatile`), and OpenRouter.
- **Anti-Repetition Session Memory**: "Generate Another Story" preserves thematic intent while commanding the AI to produce completely fresh plots, characters, and settings.
- **Zero Client-Side Key Exposure**: API keys are securely managed on the backend with environment variables.

---

## 🎭 Genre Presets

LORE includes 12 instant genre presets:
- **Mystery**: Secrets, clues, suspects, and deduction
- **Horror**: Atmospheric dread, psychological chills, and the unknown
- **Romance**: Devotion, heartfelt bonds, and tender connections
- **Fantasy**: Mythical realms, ancient wonder, and enchanted lore
- **Adventure**: Expeditions, wilderness survival, and daring quests
- **Science Fiction**: Cosmic frontiers, futuristic technology, and space exploration
- **Thriller**: Cat-and-mouse suspense, ticking clocks, and high stakes
- **Comedy**: Wit, playful mischief, and delightful irony
- **Emotional**: Bittersweet memories, human empathy, and heartfelt depth
- **Friendship**: Loyalty, lifelong promises, and unshakable bonds
- **Moral**: Timeless wisdom, ethical crossroads, and profound fables
- **Bedtime**: Gentle, tranquil, and soothing nighttime tales

---

## 📏 Story Length Calibration

- **Normal (~2 Pages)**: Default length (~900–1,400 words, ~4–6 substantial paragraphs).
- **Quick (~1 Page)**: Concise short story (~450–750 words, 3–4 paragraphs).
- **Extended (3–5 Pages)**: Multi-page narrative (~1,800–2,500 words, 6–10 paragraphs).
- **Custom Length**: Natural language length constraints (e.g., *"Write around 1000 words"*) are seamlessly respected.

---

## 🎧 Audiobook Voice Narration

- **Browser-Native Web Speech API**: Zero audio streaming fees with instantaneous client-side playback.
- **Precision Controls**: Play, Pause, Resume, Stop, and 10-second skip back (`↶ 10s`) & forward (`10s ↷`).
- **Voice Customization**: Dynamically scores and provides top natural OS voices with pitch/rate adjustments (0.25× to 2.0×).

---

## ⚙️ Environment Variables & Configuration

Set the following environment variables in your `.env` file or deployment settings:

| Variable | Description | Default |
| :--- | :--- | :--- |
| **`STORY_AI_API_KEY`** | API key for your chosen AI provider | *(None — Generation disabled)* |
| **`STORY_AI_PROVIDER`** | AI provider name (`gemini`, `openai`, `groq`, `openrouter`) | `gemini` |
| **`STORY_AI_MODEL`** | Model identifier for the provider | `gemini-1.5-flash` |
| **`STORY_AI_BASE_URL`** | Custom base URL for OpenAI-compatible proxies | *(Standard provider URL)* |

### Example `.env`:
```env
STORY_AI_PROVIDER=gemini
STORY_AI_API_KEY=AIzaSy...your-gemini-key...
STORY_AI_MODEL=gemini-1.5-flash
```

---

## 📁 Project Structure

```
LORE/
├── app/
│   ├── app.py                        # Flask server & REST API
│   ├── templates/
│   │   └── index.html                # Single-page AI Story Generator interface
│   └── static/
│       ├── style.css                 # Dark luxury theme (#050507, champagne gold)
│       ├── script.js                 # Frontend application controller & preset manager
│       ├── speech.js                 # Audiobook voice narration engine
│       └── assets/                   # LORE emblem and brand assets
│
├── story_generation/
│   ├── __init__.py
│   ├── generator.py                  # StoryGenerator master controller
│   ├── prompts.py                    # Genre prompts, length calibration & JSON schema
│   └── providers/
│       ├── base.py                   # BaseStoryProvider & JSON parser
│       ├── gemini_provider.py        # Direct Google Gemini REST API integration
│       └── openai_provider.py        # OpenAI/Groq/OpenRouter API integration
│
├── requirements.txt                  # Python dependencies (flask, requests)
└── tests/                            # Automated unit & integration test suite
```

---

## 🚀 Step-by-Step Setup & Execution

### 1. Install Dependencies
```bash
# Windows
py -m pip install -r requirements.txt

# Linux / macOS
pip install -r requirements.txt
```

### 2. Run the Web Application
```bash
# Windows
py app/app.py

# Linux / macOS
python app/app.py
```

Open your browser at **`http://127.0.0.1:5000`**.

---

## 🧪 Automated Test Suite

Run the full automated test suite:
```bash
py -m unittest discover -s tests
```

---

## 📜 License
This project is open-source under the [MIT License](LICENSE).
