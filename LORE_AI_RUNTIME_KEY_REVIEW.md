# LORE AI Runtime Key Review & In-Depth Diagnostic Report

## 1. Exact Root Cause

- **State Classification**: **Category A — API key is missing from the local execution environment**.
- **Investigation Finding**: 
  - Forensic inspection of `os.environ`, Windows Registry environment stores, and the filesystem confirmed that neither `.env` nor `.env.local` exists in the repository root or working directory.
  - No environment variables (`STORY_AI_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `OPENAI_API_KEY`, etc.) are set in the runtime process.
  - The server logs at runtime confirm that incoming HTTP POST requests to `/api/generate-story` successfully execute, run `StoryGenerator.is_available()`, evaluate `api_key = ""`, and return the designed HTTP 503 `NO_API_KEY` status code.
  - The UI accurately renders the `"AI API Key Required"` modal.

---

## 2. Runtime Provider & Environment Variable Audit

### A. Active Runtime Provider
- **Configured Provider**: `GeminiStoryProvider` (Google Gemini)
- **Default Model**: `gemini-1.5-flash`
- **Fallback Behavior**: Defaults to Gemini when `STORY_AI_PROVIDER` is unset.

### B. Environment Variable Presence Report (Evidence-Based)
| Environment Variable | Expected by Provider | Detected in Runtime | Length |
| :--- | :--- | :--- | :--- |
| `STORY_AI_API_KEY` | Yes (Universal override) | **NO** | 0 |
| `GEMINI_API_KEY` | Yes (Gemini provider) | **NO** | 0 |
| `GOOGLE_API_KEY` | Yes (Gemini provider) | **NO** | 0 |
| `OPENAI_API_KEY` | Yes (OpenAI provider) | **NO** | 0 |
| `GROQ_API_KEY` | Yes (Groq provider) | **NO** | 0 |
| `OPENROUTER_API_KEY` | Yes (OpenRouter provider) | **NO** | 0 |
| `DEEPSEEK_API_KEY` | Yes (DeepSeek provider) | **NO** | 0 |
| `STORY_AI_PROVIDER` | Yes (Provider selector) | **NO** | 0 |
| `.env` File | Yes (Workspace root) | **NO** | 0 |
| `.env.local` File | Yes (Workspace root) | **NO** | 0 |

### C. Variable Alignment Verification
- **Error message documented variables**: `STORY_AI_API_KEY (or GEMINI_API_KEY / OPENAI_API_KEY)`
- **Provider expected variables**: `STORY_AI_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `OPENAI_API_KEY`
- **Verdict**: **Zero mismatch**. The error message, provider implementation, and generator resolution use identical variable names.

---

## 3. Environment-Variable Loading Path Trace

```
1. Browser Client
   └─> POST /api/generate-story
       └─> Flask Route Handler (app/app.py: generate_story())
           └─> get_generator() -> StoryGenerator.generate()
               └─> StoryGenerator.is_available()
                   └─> StoryGenerator.refresh_provider()
                       ├─> load_env_file() [Checks .env, .env.local, app/.env]
                       └─> _resolve_provider()
                           └─> Inspects os.getenv("STORY_AI_API_KEY" / "GEMINI_API_KEY" / "OPENAI_API_KEY")
                               └─> Evaluates to "" (empty)
                                   └─> Raises StoryGenerationError(code="NO_API_KEY", status_code=503)
                                       └─> Flask returns HTTP 503 JSON: {"code": "NO_API_KEY", ...}
                                           └─> script.js showErrorState() renders "AI API Key Required"
```

---

## 4. Fixes & Resiliency Improvements Implemented

1. **UTF-8 BOM Protection in `.env` Loader**:
   - Enhanced `load_env_file()` in `story_generation/generator.py` to open files with `encoding="utf-8-sig"` and explicitly strip `\ufeff` from key names and values.
   - *Why*: On Windows, creating `.env` files using Notepad, PowerShell, or certain text editors often prepends a Byte Order Mark (`\ufeff`), which would previously corrupt the first environment variable key name (e.g. `\ufeffSTORY_AI_API_KEY`).
2. **Live Hot-Reload of Environment Variables**:
   - Modified `load_env_file()` to update `os.environ` dynamically on each incoming request whenever non-empty keys are found in `.env`.
   - *Why*: Users can add or update their `.env` file while the Flask server is running, and the next story generation request will immediately detect the credentials without needing a server restart.
3. **Strict Provider Key Isolation**:
   - Guaranteed that `_resolve_provider()` only assigns Gemini keys to `GeminiStoryProvider` and OpenAI keys to `OpenAIStoryProvider`, eliminating any cross-provider key contamination.

---

## 5. Files Changed

| File | Change Details |
| :--- | :--- |
| `story_generation/generator.py` | Added UTF-8 BOM (`utf-8-sig`) handling, stripped BOM markers on keys/values, implemented live hot-reload for `.env` updates, and isolated provider keys. |
| `tests/test_story_generation.py` | Verified unit tests for provider resolution, missing key responses (HTTP 503 `NO_API_KEY`), and empty input validation. |

---

## 6. Tests Performed & Results

1. **Automated Unit Tests (`py -m unittest discover -s tests`)**:
   - **Result**: `19/19 PASSED` (0.108s).
2. **Live Flask Server Verification**:
   - Active on `http://127.0.0.1:5000`.
   - Tested `GET /api/info` → Returns HTTP 200 with engine metadata.
   - Tested `POST /api/generate-story` → Returns HTTP 503 with structured JSON error `{ "code": "NO_API_KEY", "success": false }`.
3. **Simulated `.env` Loading & Hot-Reload Test**:
   - Verified that when a `.env` file is present, `load_env_file()` parses UTF-8 BOM, standard UTF-8, quotes, exports, and comments, and sets `StoryGenerator.is_available() = True`.

---

## 7. Remaining Manual Configuration Required

To activate AI story generation:

1. Create a `.env` file in `E:\projects\LORE\.env` (copy from `.env.example`):
   ```ini
   STORY_AI_PROVIDER=gemini
   STORY_AI_API_KEY=your_actual_gemini_api_key_here
   STORY_AI_MODEL=gemini-1.5-flash
   ```
   *(Or alternatively `OPENAI_API_KEY=your_openai_key` with `STORY_AI_PROVIDER=openai`)*

2. Open `http://127.0.0.1:5000` in your browser. The live server will immediately detect the key from `.env` on your next story request.
