# LORE — Vercel Routing & Serverless Entrypoint Review

## 1. Executive Summary

This document summarizes the root-cause diagnosis, architectural fix, test verification, and deployment instructions for resolving the **404 Not Found** error on the deployed Vercel application ([https://lore-lac.vercel.app/](https://lore-lac.vercel.app/)).

---

## 2. Root Cause Analysis

### What Happened
1. The Vercel project configuration (`vercel.json`) routes all incoming traffic via rewrite:
   ```json
   {
     "rewrites": [
       { "source": "/(.*)", "destination": "/api/index" }
     ]
   }
   ```
2. When Vercel executes the Python Serverless Function (`api/index.py`), the WSGI environment `PATH_INFO` was populated with the internal destination `/api/index` (or `/api/index.py`), while the user's requested path (e.g. `/`, `/api/categories`, `/static/style.css`) was stored in Vercel request headers such as `HTTP_X_FORWARDED_URI` / `HTTP_X_MATCHED_PATH`.
3. The underlying Flask application in `app/app.py` defines routes for `@app.route("/")`, `@app.route("/api/categories")`, `@app.route("/api/info")`, etc.
4. Because Flask matched incoming requests against `PATH_INFO = "/api/index"`, no route matched, and Werkzeug returned a standard **404 Not Found** ("*The requested URL was not found on the server.*").

---

## 3. Vercel & Flask Entrypoint Architecture

- **Canonical Flask Application**: `app/app.py` (`app = Flask(__name__, template_folder="templates", static_folder="static")`)
- **Vercel Serverless Function Entrypoint**: `api/index.py`
- **WSGI Middleware**: `VercelWSGIMiddleware` wraps Flask's `wsgi_app` in `api/index.py`:
  - Inspects `HTTP_X_FORWARDED_URI`, `HTTP_X_MATCHED_PATH`, and `HTTP_X_VERCEL_MATCHED_PATH`.
  - Strips query strings and restores the real client path to `environ["PATH_INFO"]`.
  - Strips `/api/index` or `/api/index.py` prefix if invoked directly without forwarding headers, defaulting cleanly to root (`/`).

---

## 4. Files Changed

1. **[`api/index.py`](file:///e:/projects/LORE/api/index.py)**
   - Added `VercelWSGIMiddleware` to restore `PATH_INFO` from Vercel's rewrite headers before Flask route matching.
2. **[`tests/test_vercel_entrypoint.py`](file:///e:/projects/LORE/tests/test_vercel_entrypoint.py)**
   - Added automated unit tests verifying:
     - Root route rewrite: `GET /api/index` with `X-Forwarded-Uri: /` -> HTTP 200 (renders homepage).
     - System info rewrite: `GET /api/index` with `X-Forwarded-Uri: /api/info` -> HTTP 200.
     - Presets rewrite: `GET /api/index` with `X-Forwarded-Uri: /api/categories` -> HTTP 200 (12 presets).
     - Direct fallback: `GET /api/index` without headers -> HTTP 200.

---

## 5. Deployment Configuration

- **[`vercel.json`](file:///e:/projects/LORE/vercel.json)**:
  ```json
  {
    "rewrites": [
      {
        "source": "/(.*)",
        "destination": "/api/index"
      }
    ]
  }
  ```
- **Dependencies (`requirements.txt`)**: Contains `flask` and `requests`.

---

## 6. Routes Tested & Verification Results

All 25 automated tests in the test suite passed cleanly (`py -m unittest discover -s tests`):

| Route / Capability | Request Method | Simulated Header | Status Code | Verification Result |
| :--- | :--- | :--- | :--- | :--- |
| `/` | `GET` | *(Direct)* | `200 OK` | LORE homepage rendered with dark luxury UI & brand emblem |
| `/api/index` | `GET` | `X-Forwarded-Uri: /` | `200 OK` | Successfully resolved to root homepage via WSGI middleware |
| `/api/categories` | `GET` | `X-Forwarded-Uri: /api/categories` | `200 OK` | Returned all 12 AI genre presets (`Mystery`, `Horror`, `Sci-Fi`, etc.) |
| `/api/info` | `GET` | `X-Forwarded-Uri: /api/info` | `200 OK` | Returned system status `success`, provider metadata, and features |
| `/static/style.css` | `GET` | *(Direct)* | `200 OK` | Served with `Content-Type: text/css` |
| `/static/script.js` | `GET` | *(Direct)* | `200 OK` | Served with `Content-Type: text/javascript` |
| `/static/speech.js` | `GET` | *(Direct)* | `200 OK` | Served with `Content-Type: text/javascript` |
| `/static/assets/lore-emblem.svg` | `GET` | *(Direct)* | `200 OK` | Served with `Content-Type: image/svg+xml` |
| `/api/generate-story` | `POST` | `Content-Type: application/json` | `200 OK` / `503` | Verified error envelope when key missing, validated full generation schema with mock provider |

---

## 7. Remaining Manual Vercel Steps

Per your instructions, changes have **NOT** been automatically pushed to GitHub.

To apply this routing fix to the live Vercel production deployment:

1. **Commit and push the changes**:
   ```bash
   git add api/index.py tests/test_vercel_entrypoint.py LORE_VERCEL_ROUTING_REVIEW.md
   git commit -m "fix(vercel): add WSGI middleware to handle Vercel URL rewrite headers"
   git push origin main
   ```
2. **Verify on Vercel**:
   - Vercel will trigger a new deployment for `main`.
   - Once deployed, visit [https://lore-lac.vercel.app/](https://lore-lac.vercel.app/) to confirm the homepage loads immediately.
   - Confirm in **Vercel Project Settings → Environment Variables** that `OPENAI_API_KEY` (or `STORY_AI_API_KEY`) is configured for the Production environment so live story generation can proceed.
