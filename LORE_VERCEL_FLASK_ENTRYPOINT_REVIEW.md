# LORE — Vercel Flask Entrypoint & Deployment Architecture Review

## 1. Executive Summary

This document details the root cause investigation, architectural resolution, and test verification for the **Flask 404 Not Found** error observed when accessing the deployed LORE web application on Vercel ([`https://lore-lac.vercel.app/`](https://lore-lac.vercel.app/)).

The issue was resolved by replacing an outdated and malfunctioning Serverless Function rewrite workaround (`api/index.py` + `vercel.json` rewrites) with Vercel's standard **Zero-Configuration Flask Entrypoint** (`index.py` at root), cleanly exposing the canonical Flask `app` from `app/app.py` directly to Vercel's native Python runtime.

---

## 2. Root Cause Analysis

### What Happened & Why `/` Returned Flask 404
1. **The Outdated Serverless Architecture**:
   - The repository previously contained an `api/index.py` file and a `vercel.json` rewrite configuration:
     ```json
     {
       "rewrites": [
         { "source": "/(.*)", "destination": "/api/index" }
       ]
     }
     ```
2. **The Erroneous WSGI Middleware**:
   - Inside `api/index.py`, custom WSGI middleware attempted to restore client request paths by checking:
     ```python
     forwarded_uri = (
         environ.get("HTTP_X_FORWARDED_URI") or
         environ.get("HTTP_X_MATCHED_PATH") or
         environ.get("HTTP_X_VERCEL_MATCHED_PATH") or
         ""
     )
     if forwarded_uri:
         path = forwarded_uri.split("?", 1)[0]
         if path:
             environ["PATH_INFO"] = path
     ```
3. **The Deployment Failure Mechanism**:
   - In production on Vercel, `HTTP_X_FORWARDED_URI` is not sent by Vercel edge routers.
   - Instead, Vercel sets `HTTP_X_MATCHED_PATH` to the rewrite destination (`/api/index`).
   - Because `environ.get("HTTP_X_MATCHED_PATH")` returned `"/api/index"`, the middleware evaluated `forwarded_uri` as truthy and forced `environ["PATH_INFO"] = "/api/index"` for **all** incoming requests (including `/`, `/api/categories`, `/api/generate-story`, and `/static/*`).
   - The canonical Flask application defines routes for `/`, `/api/categories`, `/api/generate-story`, and `/api/info`, but **no route** for `/api/index`.
   - Flask's router received `PATH_INFO = "/api/index"`, found no matching rule, and returned Werkzeug's default 404 response:
     > *"Not Found. The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."*

---

## 3. Architecture Comparison

### Entrypoint Before vs. After

| Attribute | Before (Broken Setup) | After (Clean Vercel Standard) |
| :--- | :--- | :--- |
| **Vercel Entrypoint** | `api/index.py` | [`index.py`](file:///e:/projects/LORE/index.py) (project root) |
| **Vercel Runtime Mode** | Serverless Function with rewrite layer | Zero-Configuration Framework Preset |
| **Flask Application Object** | `app/app.py:app` wrapped with `VercelWSGIMiddleware` | `app/app.py:app` (single canonical instance, untouched WSGI pipeline) |
| **`vercel.json`** | Present with catch-all rewrite to `/api/index` | Removed (zero-configuration detection) |
| **`api/` Directory** | Present (`api/index.py`) | Removed |
| **Route Path Resolution** | Overwritten by faulty header inspection | Standard WSGI `PATH_INFO` passed directly by Vercel |

### Flask Application Verification
- **Canonical Object**: `app` in [`app/app.py`](file:///e:/projects/LORE/app/app.py).
- **Secondary App Objects**: None. Exactly one Flask application instance exists across the codebase.
- **Root Route (`/`)**: Present (`@app.route("/")` rendering `index.html`).
- **Story Generation Route (`/api/generate-story`)**: Present (`@app.route("/api/generate-story", methods=["POST"])`).
- **Genre Presets Route (`/api/categories`)**: Present (`@app.route("/api/categories", methods=["GET"])`).
- **System Info Route (`/api/info`)**: Present (`@app.route("/api/info", methods=["GET"])`).

---

## 4. Flask Route Map Verification

Inspecting `app.url_map` on the canonical entrypoint yields:

```text
Map([
  <Rule '/static/<path:filename>' (OPTIONS, HEAD, GET) -> static>,
  <Rule '/' (OPTIONS, HEAD, GET) -> index>,
  <Rule '/api/generate-story' (OPTIONS, POST) -> generate_story>,
  <Rule '/api/categories' (OPTIONS, HEAD, GET) -> get_categories>,
  <Rule '/api/info' (OPTIONS, HEAD, GET) -> get_info>
])
```

All application routes and static assets are mapped directly on the same Flask object exported by [`index.py`](file:///e:/projects/LORE/index.py).

---

## 5. Files Changed

1. **[`index.py`](file:///e:/projects/LORE/index.py)** *(NEW)*:
   - Root-level entrypoint that exposes the canonical Flask `app` object from `app.app` for Vercel's zero-configuration Python runtime.
2. **[`api/index.py`](file:///e:/projects/LORE/api/index.py)** *(DELETED)*:
   - Removed legacy serverless function wrapper and buggy `VercelWSGIMiddleware`.
3. **[`vercel.json`](file:///e:/projects/LORE/vercel.json)** *(DELETED)*:
   - Removed rewrite rule that redirected all traffic to `/api/index`.
4. **[`tests/test_vercel_entrypoint.py`](file:///e:/projects/LORE/tests/test_vercel_entrypoint.py)** *(MODIFIED)*:
   - Updated automated test suite to verify root `index.py` export, route completeness, and Flask URL mapping.
5. **[`AGENTS.md`](file:///e:/projects/LORE/AGENTS.md)** *(MODIFIED)*:
   - Updated repository structure documentation to reflect `index.py`.

---

## 6. Verification & Test Results

### Local Test Suite
Executed: `py -m unittest discover -s tests`
- **Total Tests**: 23
- **Passed**: 23
- **Failures / Errors**: 0

### Direct Endpoint Verification

| Route | HTTP Method | Expected Status | Result | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `/` | `GET` | `200 OK` | `200 OK` | Renders LORE Dark Luxury UI homepage |
| `/api/categories` | `GET` | `200 OK` | `200 OK` | Returns all 12 AI genre presets |
| `/api/info` | `GET` | `200 OK` | `200 OK` | Returns AI provider readiness & system status |
| `/static/style.css` | `GET` | `200 OK` | `200 OK` | Served with `Content-Type: text/css; charset=utf-8` |
| `/api/generate-story` | `POST` | `400` / `200` | `400 Bad Request` | Validates input (`EMPTY_PROMPT` envelope) when empty |

---

## 7. Manual Deployment Steps (For Developer)

In accordance with project guidelines, changes have **not** been automatically deployed or pushed to GitHub.

To deploy this fix to Vercel production:

1. **Stage and commit the changes**:
   ```bash
   git add index.py tests/test_vercel_entrypoint.py AGENTS.md
   git rm api/index.py vercel.json
   git commit -m "fix(deployment): migrate to Vercel zero-configuration Flask entrypoint (index.py)"
   ```

2. **Push to GitHub**:
   ```bash
   git push origin main
   ```

3. **Verify Deployment on Vercel**:
   - Vercel will automatically detect `flask` in `requirements.txt` and use the root `index.py` entrypoint.
   - Visit [`https://lore-lac.vercel.app/`](https://lore-lac.vercel.app/) to confirm the homepage loads cleanly.
   - Verify in **Vercel Project Settings → Environment Variables** that `OPENAI_API_KEY` (or `STORY_AI_API_KEY`) is configured for the Production environment.
