# LORE — AI-First Story Generation Platform Transformation Plan

## 🏛️ Executive Summary & Architectural Vision

**LORE** is transitioning from a hybrid story recommendation and public-domain library system into a dedicated, **AI-first story generation platform**.

### The New Paradigm
- **User Journey**: The reader chooses a story category preset, inputs a natural-language prompt (with optional custom length and style constraints), or combines both.
- **AI Narrative Synthesis**: LORE orchestrates requests to state-of-the-art LLMs (Google Gemini or OpenAI) using a strict structural schema that guarantees complete, publication-quality narratives (~800–2500 words or user-specified length).
- **Presentation & Immersion**: The generated story is rendered inside a luxury, dark-first reading interface equipped with real-time text-to-speech narration (Web Speech API), clipboard sharing, reading metrics, and intelligent "Generate Another" iteration that preserves thematic intent while generating completely fresh plots, characters, and conflicts.
- **De-cluttering & Optimization**: All legacy recommendation models, TF-IDF vectorizers, 520-story synthetic datasets, public-domain corpora, and heavy data science dependencies (`scikit-learn`, `nltk`, `pandas`, `numpy`) are completely deprecated and safely removed.

---

## 🔍 Codebase Audit & Reference Mapping

### 1. Components to REUSE
| Component / File | Reason for Reuse | Required Adaptations |
| :--- | :--- | :--- |
| `story_generation/providers/base.py` | Robust `BaseStoryProvider` interface, JSON extractor, markdown fence cleaner, and `StoryGenerationError`. | Add support for explicit `category` and `length` parameters in method signatures. |
| `story_generation/providers/gemini_provider.py` | Native Google Gemini REST integration with token and error management. | Pass enhanced system prompts and length parameters. |
| `story_generation/providers/openai_provider.py` | Native OpenAI / Groq / OpenRouter REST integration. | Pass enhanced system prompts and length parameters. |
| `story_generation/generator.py` | Master controller, environment loader (`.env`), provider auto-detection, and status reporting. | Enhance `generate()` to accept `category`, `length`, and `custom_instructions`. |
| `app/static/speech.js` | Full-featured Web Speech API narration controller with 5-voice scoring, 8-speed options, and 10s seek. | 100% reusable without modification. |
| `app/static/style.css` | Dark luxury design system (`#050507`, champagne gold accents `#d4af37`, glassmorphism, responsive breakpoints). | Streamline layout by removing library drawer and modal styles while optimizing the hero generator and reader view. |
| `app/static/assets/` | Brand assets (`lore-emblem.svg`, `favicon.ico`). | 100% reusable. |

---

### 2. Components to MODIFY
| Component / File | Current Role | Target Role in New Architecture |
| :--- | :--- | :--- |
| `app/app.py` | Flask backend hosting both recommendation APIs (`/api/recommend`, `/api/categories`, `/api/stories`) and generation (`/api/generate-story`). | Pure AI generation backend. Remove all recommender imports; expose clean endpoints: `POST /api/generate-story`, `GET /api/categories`, `GET /api/info`. |
| `story_generation/prompts.py` | System prompt and basic user message builder. | Add dynamic length calibration (~2-page default vs. explicit page/word requests), genre preset guidance, and anti-repetition directives. |
| `app/templates/index.html` | Dual-experience page with hero input, library drawer, featured classics, and modal reader. | Unified single-page AI Story Generator: Hero with Category Preset Cards + Natural Language Prompt + Length Selector + Dynamic Reader View + Voice Toolbar. Remove old library sections. |
| `app/static/script.js` | Frontend controller managing generation, drawer navigation, and modal rendering. | Refactor into a streamlined controller managing category preset selection, prompt dispatch, length options, story rendering, voice loading, and "Generate Another". |
| `requirements.txt` | Contains `scikit-learn`, `nltk`, `pandas`, `numpy`, `flask`, `requests`. | Trim down to lightweight core dependencies: `flask>=3.0.0`, `requests>=2.31.0` (eliminating hundreds of megabytes of ML packages). |
| `AGENTS.md` / `README.md` | Documents dual-pillar architecture and recommendation pipeline. | Update to reflect the AI-first story generation platform architecture and setup. |

---

### 3. Components to REMOVE / DEPRECATE
| Obsolete Component | Path | Reason for Removal | Lingering Reference Check |
| :--- | :--- | :--- | :--- |
| Old Recommender Engine | `recommendation/story_recommender.py`, `recommendation/tfidf_model.py`, `recommendation/__init__.py` | TF-IDF cosine similarity search is no longer part of the product. | Only imported in `app/app.py`, `pipeline.py`, `evaluation/`, and `tests/test_random_category_recommendation.py`. |
| Serialized Model Artifacts | `models/tfidf_vectorizer.pkl`, `models/story_index.pkl` | Static pickled index files are obsolete. | Referenced only by `recommendation/` and `pipeline.py`. |
| Preprocessing Pipeline | `preprocessing/preprocess.py`, `preprocessing/__init__.py` | Dataset cleaning and tokenization are no longer needed. | Referenced only by `pipeline.py` and `recommendation/`. |
| Legacy Datasets | `data/raw/curated_library.json`, `data/processed/processed_stories.csv` | Static short stories are replaced by real-time AI generation. | Referenced only by data build scripts. |
| Build & Indexing Scripts | `pipeline.py`, `generate_dataset.py`, `scripts/build_curated_library.py` | No static corpus generation or index building needed. | Standalone scripts. |
| Evaluation Suite | `evaluation/evaluate.py`, `evaluation/evaluation_results.json`, `evaluation/test_queries.py`, `evaluation/test_voice_narration.py` | Tests retrieval accuracy of old TF-IDF index. | Standalone evaluation scripts. |
| Obsolete Unit Tests | `tests/test_random_category_recommendation.py` | Tests recommendation category matching. | Replaced by new API and generation tests. |

---

## 🎯 Target System Architecture

```
                                    USER
                                     │
             ┌───────────────────────┴───────────────────────┐
             ▼                                               ▼
   1. Category Preset                              2. Natural-Language Request
   (e.g., Horror, Sci-Fi, Mystery)                 (e.g., "A tense sci-fi mystery on Europa...")
             │                                               │
             └───────────────────────┬───────────────────────┘
                                     │
                                     ▼
                       Optional Length Constraint
                   (Default ~2 pages / Custom Length)
                                     │
                                     ▼
                         POST /api/generate-story
                                     │
                                     ▼
                        [ LORE Story Generator ]
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
       [ Google Gemini API ]                   [ OpenAI / Groq API ]
      (gemini-1.5-flash / pro)                 (gpt-4o / llama-3.3)
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     │
                                     ▼
                         Strict JSON Response Schema
                  { title, genre, summary, content, tags }
                                     │
                                     ▼
                     [ LORE Reader & Audio Experience ]
             • Formatted Typography & Multi-Paragraph Layout
             • In-Browser Voice Narration (speech.js)
             • Reading Metrics (Word count, read time)
             • Copy to Clipboard & "Generate Another"
```

---

## 📐 Detailed Technical Specifications

### 1. API Contracts & Schema

#### Endpoint 1: `POST /api/generate-story`
Primary generation endpoint supporting both quick preset generation and detailed natural language requests.

**Request Payload:**
```json
{
  "prompt": "A psychological horror story about an archivist who finds a tape recorded in the future.",
  "category": "Horror",
  "length": "default",
  "is_another": false,
  "previous_titles": ["The Silent Reel"]
}
```

**Field Specifications:**
- `prompt` (*string, optional if category is supplied*): Natural-language premise, setting, characters, tone, or constraints.
- `category` (*string, optional*): AI preset genre (e.g., `Mystery`, `Horror`, `Romance`, `Fantasy`, `Adventure`, `Sci-Fi`, `Thriller`, `Comedy`, `Emotional`, `Friendship`, `Moral`, `Bedtime`).
- `length` (*string, default: `"default"`*): Target story length indicator:
  - `"default"`: ~2 readable pages (~800–1,500 words).
  - `"short"` or `"1-page"`: ~400–700 words (~1 readable page).
  - `"long"` or `"3-5 pages"`: ~1,800–2,500 words.
  - Or raw user string (e.g. `"around 1200 words"`).
- `is_another` (*boolean, default: `false`*): Signals regeneration with thematic preservation and narrative divergence.
- `previous_titles` (*array of strings, optional*): Past story titles in the current session to prevent repetition.

**Response Payload (Success - 200 OK):**
```json
{
  "success": true,
  "story": {
    "title": "The Future Frequency",
    "genre": "Horror",
    "summary": "While restoring magnetic reels in the basement archives, Arthur plays a cassette dated fifty years from tomorrow.",
    "content": "The magnetic tape hissed with the dry whisper of old static...\n\nParagraph 2...\n\nParagraph 3...",
    "tags": ["Psychological Horror", "Time Slip", "Archivist", "Suspense"],
    "word_count": 1120,
    "reading_time_min": 6,
    "model": "gemini-1.5-flash",
    "provider": "Google Gemini",
    "latency_ms": 1420.5
  }
}
```

**Error Response Payload (400 / 503 / 504):**
```json
{
  "success": false,
  "error": "Story generation is temporarily unavailable. Please verify API key configuration.",
  "code": "NO_API_KEY"
}
```

---

#### Endpoint 2: `GET /api/categories`
Provides the frontend with available AI genre presets, descriptions, icons, and suggested creative themes.

**Response Payload:**
```json
{
  "status": "success",
  "categories": [
    {
      "id": "mystery",
      "name": "Mystery",
      "icon": "🔍",
      "tagline": "Deduction, puzzling crimes, secrets, and cunning investigators.",
      "sample_prompt": "A locked-room mystery during a storm at an isolated lighthouse."
    },
    {
      "id": "horror",
      "name": "Horror",
      "icon": "👻",
      "tagline": "Psychological dread, eerie atmospheres, and chilling encounters.",
      "sample_prompt": "An antique mirror reflecting a room that does not exist."
    },
    {
      "id": "romance",
      "name": "Romance",
      "icon": "💖",
      "tagline": "Deep emotional bonds, heartfelt reunions, and bittersweet devotion.",
      "sample_prompt": "Two estranged sweethearts who meet on a midnight alpine train."
    },
    {
      "id": "fantasy",
      "name": "Fantasy",
      "icon": "🔮",
      "tagline": "Mythical kingdoms, ancient lore, wondrous magic, and heroic journeys.",
      "sample_prompt": "A young cartographer who discovers a hidden floating realm inside a storm."
    },
    {
      "id": "adventure",
      "name": "Adventure",
      "icon": "🧭",
      "tagline": "Daring expeditions, wilderness survival, and high-stakes quests.",
      "sample_prompt": "An explorer searching for a forgotten temple in the deep jungle."
    },
    {
      "id": "sci-fi",
      "name": "Science Fiction",
      "icon": "🚀",
      "tagline": "Futuristic concepts, deep space exploration, AI, and alien frontiers.",
      "sample_prompt": "A lone engineer on a deep-space station receives a transmission from yesterday."
    },
    {
      "id": "thriller",
      "name": "Thriller",
      "icon": "⚡",
      "tagline": "High-octane suspense, ticking clocks, and relentless cat-and-mouse tension.",
      "sample_prompt": "A cybersecurity agent realizing the intruder is operating from inside their safehouse."
    },
    {
      "id": "comedy",
      "name": "Comedy",
      "icon": "🎭",
      "tagline": "Witty irony, hilarious misadventures, and delightful banter.",
      "sample_prompt": "A chaotic dinner party where every guest is pretending to be someone else."
    },
    {
      "id": "emotional",
      "name": "Emotional",
      "icon": "🍃",
      "tagline": "Bittersweet reflections, human resilience, and moving life stories.",
      "sample_prompt": "An aging violinist preparing to perform one final secret waltz."
    },
    {
      "id": "friendship",
      "name": "Friendship",
      "icon": "🤝",
      "tagline": "Unshakable loyalty, childhood promises, and enduring companionship.",
      "sample_prompt": "Two lifelong friends fulfilling a pact made thirty years ago."
    },
    {
      "id": "moral",
      "name": "Moral",
      "icon": "⚖️",
      "tagline": "Timeless fables, ethical crossroads, and wisdom about life.",
      "sample_prompt": "A merchant who learns the true cost of getting everything he ever wished for."
    },
    {
      "id": "bedtime",
      "name": "Bedtime",
      "icon": "🌙",
      "tagline": "Gentle, tranquil, and soothing tales designed for restful contemplation.",
      "sample_prompt": "A quiet journey of a star guiding nocturnal creatures through a calm forest."
    }
  ]
}
```

---

#### Endpoint 3: `GET /api/info`
Returns system status, active provider metadata, and engine readiness.

**Response Payload:**
```json
{
  "status": "success",
  "engine": "LORE AI Story Generation Platform",
  "ai_generation_available": true,
  "ai_provider": "Google Gemini",
  "ai_model": "gemini-1.5-flash",
  "total_presets": 12,
  "features": [
    "AI Story Generation (LLM)",
    "Genre Presets & Custom Natural Language Requests",
    "Dynamic Length Calibration",
    "Audiobook Voice Narration (Web Speech API)",
    "Anti-Repetition Session Memory"
  ]
}
```

---

### 2. Prompt Engineering & Narrative Calibration

To fulfill the requirements of high quality, complete narrative arcs, and precise length control, `story_generation/prompts.py` will be structured with distinct modular layers:

#### A. Master System Prompt
Enforces authorial voice, complete 6-stage narrative arcs (Hook → Exposition → Inciting Conflict → Rising Action/Tension → Climax → Resolution/Deliberate Ending), sensory richness, natural dialogue, zero AI self-reference, and strict JSON output formatting.

#### B. Dynamic Length Calibration
- **Default (~2 pages)**: Instructs model to produce ~900–1,400 words (4–6 rich paragraphs, ~5–7 min read).
- **Short (~1 page)**: Instructs model to produce ~450–700 words (tight, punchy short story).
- **Long / Epic (~3–5 pages)**: Instructs model to produce ~1,800–2,500 words with expansive world-building, subplot development, and extended dialogue.
- **Explicit User Word Count**: If the user writes "Write around 1000 words" or "500 words", the prompt dynamically extracts or injects this specific constraint into the prompt payload.

#### C. "Generate Another" Diversity Safeguard
When `is_another=true`:
- The prompt explicitly instructs the LLM:
  *"The reader is requesting ANOTHER unique, fresh story within this theme/genre. You MUST construct a completely new plotline, different character names, a distinct setting, an altered conflict, and an original climax/resolution. Do NOT reuse elements from: [Previous Titles]."*
- Higher temperature sampling is activated (e.g., `0.92–0.95`).

---

### 3. Frontend Experience & UI Flow

```
[ Navigation Bar ]
LORE Logo • Brand Tagline • "AI Engine Ready" Status Pill • About Modal Link

[ Hero Generation Section ]
1. "What story shall we weave today?"
2. Category Presets Ribbon (12 Interactive Cards: Mystery, Horror, Sci-Fi, Romance, etc.)
   - Clicking a card badges the active category and fills an inspiring placeholder.
3. Natural-Language Input Card:
   - Expandable Textarea (Supports full premises: characters, setting, tone, twists).
   - Story Length Selector Tabs: [ Normal (~2 Pages) | Quick (~1 Page) | Extended (3-5 Pages) ]
   - Clear button & "Generate Story" CTA button with glowing shimmer & loading state.
4. "Try an Idea" Ingestion Chips.

[ Dynamic Story Reader Card ]
- Story Title & Genre Badge
- Reading Time & Word Count Indicators
- 2-Sentence Synopsis Callout Box
- Audio Narration Toolbar:
  - Play / Pause / Resume / Stop
  - ↶ 10s & 10s ↷ Seek Granularity
  - Top 5 Natural Voice Selector & 8-Speed Controls (0.25× to 2.0×)
  - Animated Waveform & Visual Paragraph Highlighting
- Story Narrative Paragraphs (with responsive typography and A- / A+ font sizing controls)
- Action Footer:
  - 🔄 "Generate Another Story" (preserves prompt & length, builds fresh tale)
  - 📋 "Copy Story" (with clipboard confirmation)
  - ✍️ "New Request" (smooth-scrolls back to prompt input)
```

---

## 🗑️ Safe Subsystem Deprecation & File Removal Plan

### Execution Steps for Safe Deprecation:
1. **Verify References in Code**:
   Confirm that no remaining file in `app/`, `story_generation/`, or `tests/` imports from `recommendation/`, `preprocessing/`, or `models/`.
2. **Remove Deprecated Files & Folders**:
   - `recommendation/` (all files)
   - `models/` (`tfidf_vectorizer.pkl`, `story_index.pkl`)
   - `preprocessing/` (all files)
   - `data/` (`raw/curated_library.json`, `processed/processed_stories.csv`)
   - `scripts/` (`build_curated_library.py`)
   - `evaluation/` (all files)
   - Root files: `pipeline.py`, `generate_dataset.py`
3. **Clean Dependencies in `requirements.txt`**:
   Remove `scikit-learn`, `nltk`, `pandas`, `numpy`.
   Retain `flask>=3.0.0` and `requests>=2.31.0`.

---

## 🧪 Testing Strategy & QA Plan

### Automated Test Suite Overhaul

| Test File | Scope of Coverage |
| :--- | :--- |
| `tests/test_story_generation.py` | • `BaseStoryProvider` JSON parsing & markdown cleanup.<br>• `StoryGenerator` provider auto-detection (Gemini, OpenAI, Groq).<br>• Custom length and category parameter handling.<br>• Full narrative structure verification.<br>• Anti-repetition behavior on "Generate Another". |
| `tests/test_api_endpoints.py` (replacing `test_vercel_entrypoint.py`) | • `GET /` (Homepage delivery).<br>• `GET /api/info` (Engine status & provider metadata).<br>• `GET /api/categories` (12 AI genre presets).<br>• `POST /api/generate-story` (Validation, missing keys, mock success). |
| `tests/test_mobile_and_perf.py` | • CSS luxury tokens, responsive media queries.<br>• `speech.js` Web Speech API controller integrity.<br>• Fast API response benchmarks. |

---

## ⚠️ Risk Assessment & Mitigation Matrix

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Provider API Outages or Invalid Keys** | User cannot generate stories. | Structured `StoryGenerationError` responses with clear user-friendly messages and HTTP 503 status; zero stack trace exposure. |
| **LLM Output Formatting Glitches** | JSON parsing failure from LLM. | Multi-stage regex extraction in `clean_and_parse_json()`; unescaped character repairs; markdown fence stripping. |
| **Slow LLM Response Time (Latency)** | User perceives interface as frozen. | Multi-stage skeleton loading animation with pulsing LORE emblem and dynamic progress messages ("Weaving atmosphere...", "Refining character dialogue..."). |
| **Repetitive Plots on "Generate Another"** | Degraded user novelty experience. | Session tracking of recent titles + elevated sampling temperature (`0.92–0.95`) + explicit negative prompt directives against reusing past characters or settings. |

---

## 🗺️ Step-by-Step Implementation Roadmap

1. **Step 1: AI Engine & Prompts Modernization**
   - Update `story_generation/prompts.py` to support category presets, length constraints, and anti-repetition memory.
   - Update `story_generation/generator.py` and providers to pass category and length parameters cleanly.
2. **Step 2: Backend API Refactoring**
   - Clean `app/app.py`: remove recommender dependencies; update `/api/generate-story`, `/api/categories`, and `/api/info`.
3. **Step 3: Frontend Unification**
   - Refactor `app/templates/index.html` into a dedicated AI Story Generation interface with category presets and length options.
   - Refactor `app/static/script.js` to manage preset clicks, prompt submission, length toggles, and narrative rendering.
   - Adjust `app/static/style.css` to remove legacy drawer/modal styles and polish the streamlined layout.
4. **Step 4: Deprecation of Obsolete Subsystems**
   - Safely remove `recommendation/`, `preprocessing/`, `models/`, `data/`, `pipeline.py`, `generate_dataset.py`, `evaluation/`, and `scripts/`.
   - Update `requirements.txt` to remove unused ML dependencies.
5. **Step 5: Test Suite Modernization & Verification**
   - Update all unit tests and run `py -m unittest discover -s tests` to ensure 100% pass rate.
   - Update `README.md` and `AGENTS.md` to reflect the new AI-first architecture.
