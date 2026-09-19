# LORE — Production OpenAI API Key & Request Diagnostic Review

## 1. Executive Summary

This diagnostic review investigates the request flow and configuration pipeline for OpenAI story generation in **LORE**. It addresses why the application returned `"Invalid AI API Key — The configured OPENAI_API_KEY was rejected by OpenAI."`, traces the end-to-end request lifecycle from frontend to OpenAI's REST endpoint, hardens environment-variable loading and provider resolution, and adds granular error classification (distinguishing missing keys, quota limits, rate limits, model permissions, and authentication failures).

---

## 2. Root Cause Analysis

### Investigation Findings
1. **Placeholder Key Was Treated as Active**:
   - The local `.env` and default deployment templates contained placeholder values (`your_new_openai_api_key_here`).
   - The previous `is_available()` check only verified `bool(self.api_key and str(self.api_key).strip())`.
   - As a result, the placeholder string was considered a configured key and dispatched to `https://api.openai.com/v1/chat/completions`.
   - OpenAI's authentication gateway rejected the placeholder token with `HTTP 401 Unauthorized` (`type: "invalid_request_error"`, `code: "invalid_api_key"`).
   - The frontend accurately displayed what the backend received from OpenAI: *"Invalid AI API Key"*.
2. **Environment Variable Precedence**:
   - In `story_generation/generator.py`, `openai_key` was previously resolved as `story_ai_key or os.getenv("OPENAI_API_KEY")`.
   - If `STORY_AI_API_KEY` was set to a legacy or placeholder value, it took precedence over `OPENAI_API_KEY`.
   - This was corrected so that `OPENAI_API_KEY` has primary priority for OpenAI, with `STORY_AI_API_KEY` as universal fallback.
3. **Coarse Error Code Mapping**:
   - HTTP 429 quota exhaustion (`insufficient_quota`) was previously grouped with temporary rate limits.
   - HTTP 403 model permissions and HTTP 404 model not found were previously mapped to a generic `PROVIDER_ERROR`.
   - This was overhauled to provide granular error mapping (`QUOTA_EXCEEDED`, `RATE_LIMIT`, `MODEL_NOT_FOUND`, `PERMISSION_DENIED`, `NO_API_KEY`, `INVALID_API_KEY`).

---

## 3. End-to-End OpenAI Request Flow

```
[ Reader UI (index.html / script.js) ]
                │
                ▼ (POST /api/generate-story with {prompt, category, length})
[ Flask API Route (app/app.py:generate_story) ]
                │
                ▼ (Calls get_generator().generate(...))
[ StoryGenerator Controller (story_generation/generator.py) ]
                │  - Loads .env / os.environ
                │  - Resolves OPENAI_API_KEY (priority) & STORY_AI_API_KEY (fallback)
                │  - Validates key is non-empty and not a placeholder
                │  - Builds structured prompts via prompts.py
                ▼
[ OpenAIStoryProvider (story_generation/providers/openai_provider.py) ]
                │  - Normalizes token: str(api_key).strip().strip("'\"")
                │  - Headers: {"Authorization": "Bearer sk-...", "Content-Type": "application/json"}
                │  - Model: gpt-4o-mini (or STORY_AI_MODEL)
                │  - Payload: {model, messages, temperature, max_tokens, response_format}
                │  - Safe metadata logging (key length & safe prefix only; zero secrets)
                ▼
[ OpenAI REST API Endpoint (https://api.openai.com/v1/chat/completions) ]
                │
                ├── HTTP 200: Parses JSON story object -> Returns {success: true, story: {...}}
                ├── HTTP 401: INVALID_API_KEY -> "The configured OPENAI_API_KEY was rejected by OpenAI."
                ├── HTTP 429 (quota): QUOTA_EXCEEDED -> "OpenAI account quota exceeded. Check billing plan."
                ├── HTTP 429 (rate): RATE_LIMIT -> "OpenAI rate limit reached. Please wait a moment."
                ├── HTTP 403: PERMISSION_DENIED -> "Project or API key lacks permission for this model."
                └── HTTP 404: MODEL_NOT_FOUND -> "Model 'gpt-4o-mini' was not found or not accessible."
```

---

## 4. Environment-Variable Flow & Precedence

| Environment Variable | Role | Resolution Precedence |
| :--- | :--- | :--- |
| **`OPENAI_API_KEY`** | Canonical OpenAI API Secret Key (`sk-proj-...` / `sk-...`) | **Primary** for OpenAI provider |
| **`STORY_AI_API_KEY`** | Universal Fallback API Key | **Fallback** when specific key is unset |
| **`STORY_AI_PROVIDER`** | Provider Selector (`openai`, `gemini`, `groq`, `openrouter`, `deepseek`) | Defaults to `openai` |
| **`STORY_AI_MODEL`** | LLM Model Name (e.g. `gpt-4o-mini`, `gpt-4o`) | Defaults to `gpt-4o-mini` |
| **`STORY_AI_BASE_URL`** | Custom Base URL for OpenAI-compatible proxies | Defaults to `https://api.openai.com/v1` |

---

## 5. SDK & Dependency Architecture

- **Direct HTTP REST Transport**:
  - LORE uses Python `requests` directly against the official OpenAI endpoint (`https://api.openai.com/v1/chat/completions`).
  - This eliminates SDK version mismatches (e.g. `openai.ChatCompletion.create` v0.28 vs `openai.OpenAI()` v1.0+).
  - Dependencies in [`requirements.txt`](file:///e:/projects/LORE/requirements.txt) remain minimal, fast, and serverless-friendly: `flask>=3.0.0` and `requests>=2.31.0`.

---

## 6. Code Changes Made

1. **[`story_generation/providers/openai_provider.py`](file:///e:/projects/LORE/story_generation/providers/openai_provider.py)**:
   - Added `is_available()` placeholder filter to prevent dispatching dummy keys to OpenAI.
   - Added sanitization (`clean_token.strip().strip("'\"").strip()`) to handle quoted keys or trailing whitespace.
   - Added adaptive token parameter (`max_tokens` vs `max_completion_tokens` for reasoning models).
   - Added safe diagnostic logging (logs `key_len` and safe 4-character prefix only; never logs secret values).
   - Added granular OpenAI HTTP error status and error code handling.
2. **[`story_generation/generator.py`](file:///e:/projects/LORE/story_generation/generator.py)**:
   - Prioritized `OPENAI_API_KEY` over `STORY_AI_API_KEY` for OpenAI provider lookups.
   - Ensured `load_env_file()` does not overwrite explicit runtime environment variables.
3. **[`app/static/script.js`](file:///e:/projects/LORE/app/static/script.js)**:
   - Added explicit error title and message handling in `showErrorState()` for `QUOTA_EXCEEDED`, `RATE_LIMIT`, `MODEL_NOT_FOUND`, and `PERMISSION_DENIED`.
4. **[`tests/test_story_generation.py`](file:///e:/projects/LORE/tests/test_story_generation.py)**:
   - Added unit tests for placeholder rejection, 401, 429 (quota), 404, and 403 error classifications.

---

## 7. Verification & Test Results

All **25 automated tests** pass cleanly:
```bash
py -m unittest discover -s tests
```
- **Test Output**: `Ran 25 tests in 0.212s — OK`

### Local Pipeline Verification

| Probe | Condition | Status Code | Error Code | Behavior |
| :--- | :--- | :--- | :--- | :--- |
| `GET /api/info` | Placeholder in `.env` | `200 OK` | `ai_generation_available: false` | Safe status returned; secrets hidden |
| `POST /api/generate-story` | Placeholder in `.env` | `503 Service Unavailable` | `NO_API_KEY` | Promptly asks user to configure real key |
| `POST /api/generate-story` | Mock 401 from OpenAI | `503 Service Unavailable` | `INVALID_API_KEY` | Explicit key rejection card |
| `POST /api/generate-story` | Mock 429 quota from OpenAI | `429 Too Many Requests` | `QUOTA_EXCEEDED` | Directs user to OpenAI billing |
| `POST /api/generate-story` | Mock 404 from OpenAI | `404 Not Found` | `MODEL_NOT_FOUND` | Alerts model availability |

---

## 8. Production (Vercel) Configuration Checklist

To verify your OpenAI key on Vercel production:

1. Go to **Vercel Dashboard → Project Settings → Environment Variables**.
2. Verify that **`OPENAI_API_KEY`** is set for the **Production** environment:
   - Key Name: `OPENAI_API_KEY`
   - Value: `sk-proj-...` (or `sk-...`)
   - Ensure there are no surrounding quote marks (`"` or `'`) or leading/trailing spaces.
3. If you have an entry for `STORY_AI_API_KEY` in Vercel, either update it to match `OPENAI_API_KEY` or remove it so `OPENAI_API_KEY` is used directly.
4. Redeploy or promote deployment on Vercel to activate the updated environment variables.
