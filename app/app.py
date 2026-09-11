"""
AI-Based Story Recommendation and Retrieval System
Module: Flask Web Backend & REST API
"""

import os
import sys
import json
import time
from flask import Flask, render_template, request, jsonify

# Resolve robust absolute paths relative to this file
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
TEMPLATE_DIR = os.path.join(APP_DIR, "templates")
STATIC_DIR = os.path.join(APP_DIR, "static")

# Ensure project root is in sys.path for cross-module imports
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from recommendation.story_recommender import StoryRecommender

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR
)

# Model and dataset absolute paths
VEC_PATH = os.path.join(PROJECT_ROOT, "models", "tfidf_vectorizer.pkl")
IDX_PATH = os.path.join(PROJECT_ROOT, "models", "story_index.pkl")
EVAL_PATH = os.path.join(PROJECT_ROOT, "evaluation", "evaluation_results.json")

# Global Recommender Instance (Loaded once at startup)
RECOMMENDER = None
MODEL_LOADED = False
LOAD_ERROR = None


def init_recommender():
    """Loads the story index and TF-IDF models once at application startup."""
    global RECOMMENDER, MODEL_LOADED, LOAD_ERROR
    try:
        if os.path.exists(VEC_PATH) and os.path.exists(IDX_PATH):
            RECOMMENDER = StoryRecommender(vectorizer_path=VEC_PATH, index_path=IDX_PATH)
            MODEL_LOADED = True
            LOAD_ERROR = None
            print("[+] StoryRecommender successfully initialized in memory.")
        else:
            MODEL_LOADED = False
            LOAD_ERROR = "Model index files not found. Please run preprocessing and tfidf_model first."
            print(f"[!] Warning: {LOAD_ERROR}")
    except Exception as e:
        MODEL_LOADED = False
        LOAD_ERROR = str(e)
        print(f"[!] Error loading recommender: {e}")


# Initialize at server boot
init_recommender()


@app.route("/")
@app.route("/api/index")
@app.route("/api/index.py")
def index():
    """Renders the main story discovery web application."""
    return render_template("index.html")


@app.route("/api/info", methods=["GET"])
def get_info():
    """Returns application status, dataset metrics, and category list."""
    global RECOMMENDER, MODEL_LOADED, LOAD_ERROR
    if not MODEL_LOADED:
        init_recommender()

    if not MODEL_LOADED:
        return jsonify({
            "status": "error",
            "model_loaded": False,
            "message": LOAD_ERROR
        }), 503

    df = RECOMMENDER.stories_df
    categories_counts = df['category'].value_counts().to_dict()

    return jsonify({
        "status": "success",
        "model_loaded": True,
        "total_stories": len(df),
        "total_categories": len(RECOMMENDER.categories),
        "categories": RECOMMENDER.categories,
        "category_counts": categories_counts,
        "features": ["TF-IDF Vectorization", "Cosine Similarity", "NLP Query Understanding", "Feature Matching", "Explainable AI"]
    })


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Returns the list of supported story genres."""
    global RECOMMENDER, MODEL_LOADED
    if not MODEL_LOADED:
        init_recommender()
    if not MODEL_LOADED:
        return jsonify({"status": "error", "message": "Model not loaded"}), 503

    return jsonify({
        "status": "success",
        "categories": RECOMMENDER.categories
    })


@app.route("/api/recommend", methods=["POST"])
def recommend_story():
    """
    Primary story recommendation endpoint:
    Receives JSON: { "query": str, "category": str (optional), "exclude_ids": list (optional) }
    Returns JSON: { "status": "success", "story": {...}, "why_this_story": [...], "relevance_percentage": int }
    """
    global RECOMMENDER, MODEL_LOADED

    if not MODEL_LOADED:
        init_recommender()
        if not MODEL_LOADED:
            return jsonify({
                "status": "error",
                "message": "Recommendation system is initializing or missing model files."
            }), 503

    data = request.get_json() or {}
    query = data.get("query", "").strip()
    selected_category = data.get("category", None)
    exclude_ids = data.get("exclude_ids", [])
    is_find_another = bool(data.get("is_find_another", False))

    if not query and not selected_category:
        return jsonify({
            "status": "error",
            "message": "Please enter a story request or select a category to find a story."
        }), 400

    start_time = time.time()
    try:
        result = RECOMMENDER.recommend(
            query=query,
            selected_category=selected_category,
            exclude_ids=exclude_ids,
            is_find_another=is_find_another
        )
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        result["latency_ms"] = elapsed_ms
        return jsonify(result)

    except Exception as e:
        print(f"[!] Technical Recommendation Error: {e}", file=sys.stderr)
        return jsonify({
            "status": "error",
            "message": "Something went wrong while finding your story. Please try again."
        }), 500


@app.route("/api/random", methods=["GET"])
def get_random_story():
    """Retrieves a random story, optionally filtered by category."""
    global RECOMMENDER, MODEL_LOADED
    if not MODEL_LOADED:
        init_recommender()
    if not MODEL_LOADED:
        return jsonify({"status": "error", "message": "Model not loaded"}), 503

    category = request.args.get("category", None)
    df = RECOMMENDER.stories_df
    if category:
        cat_df = df[df['category'].str.lower() == category.lower()]
        if not cat_df.empty:
            df = cat_df

    selected = df.sample(n=1).iloc[0]
    return jsonify({
        "status": "success",
        "story": {
            "id": str(selected["id"]),
            "title": str(selected["title"]),
            "category": str(selected["category"]),
            "theme": str(selected["theme"]),
            "setting": str(selected["setting"]),
            "mood": str(selected["mood"]),
            "keywords": str(selected["keywords"]),
            "story_text": str(selected["story"]),
            "word_count": int(selected.get("word_count", len(str(selected["story"]).split()))),
            "reading_time_min": int(selected.get("reading_time_min", 1)),
        },
        "relevance_percentage": 100,
        "why_this_story": [
            {"type": "random", "label": "Random Pick", "detail": "Curated story from database"}
        ]
    })


@app.route("/api/evaluation", methods=["GET"])
def get_evaluation_metrics():
    """Returns benchmark evaluation metrics."""
    if os.path.exists(EVAL_PATH):
        with open(EVAL_PATH, "r", encoding="utf-8") as f:
            metrics = json.load(f)
        return jsonify({"status": "success", "metrics": metrics})
    else:
        return jsonify({"status": "error", "message": "Evaluation results not yet generated"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
