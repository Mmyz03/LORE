"""
AI-Based Story Recommendation and Retrieval System
Module: Dynamic TF-IDF Vectorization & Model Index Serialization

Features:
- Fits high-capacity Scikit-Learn TfidfVectorizer on arbitrary corpus sizes (100 to 50,000+ stories)
- Sublinear term frequency scaling and unigram + bigram n-gram extraction
- Efficient sparse matrix serialization and index bundling
- Detailed diagnostic logging (features, matrix dimensions, categories)
"""

import os
import sys
import time
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


def build_and_fit_tfidf(
    df: pd.DataFrame,
    max_features: int = 35000,
    ngram_range: tuple = (1, 2),
    min_df: int = 1
):
    """
    Fits a Scikit-Learn TfidfVectorizer on the preprocessed searchable_text column.
    Returns the vectorizer and the sparse TF-IDF matrix.
    """
    if 'searchable_text' not in df.columns:
        raise ValueError("DataFrame must contain 'searchable_text' column.")

    corpus = df['searchable_text'].fillna('').tolist()

    print(f"[+] Fitting TF-IDF Vectorizer across {len(corpus)} documents...")
    start_time = time.time()

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        min_df=min_df,
        sublinear_tf=True,
        norm='l2'
    )

    tfidf_matrix = vectorizer.fit_transform(corpus)
    fit_duration = round(time.time() - start_time, 3)

    num_features = len(vectorizer.get_feature_names_out())
    print(f"[+] TF-IDF Vectorizer fitted in {fit_duration}s with {num_features:,} features.")
    print(f"[+] TF-IDF Matrix shape: {tfidf_matrix.shape} (Stories: {tfidf_matrix.shape[0]:,}, Features: {tfidf_matrix.shape[1]:,})")

    return vectorizer, tfidf_matrix


def save_story_index(
    vectorizer: TfidfVectorizer,
    tfidf_matrix,
    df: pd.DataFrame,
    vectorizer_path: str = "models/tfidf_vectorizer.pkl",
    index_path: str = "models/story_index.pkl"
):
    """
    Serializes the TF-IDF vectorizer and complete story index (sparse matrix + DataFrame).
    """
    os.makedirs(os.path.dirname(vectorizer_path), exist_ok=True)
    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    # Save vectorizer
    with open(vectorizer_path, "wb") as f:
        pickle.dump(vectorizer, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"[+] Serialized TF-IDF vectorizer to: {vectorizer_path}")

    # Package index bundle
    categories = sorted(df['category'].dropna().unique().tolist())
    index_data = {
        "tfidf_matrix": tfidf_matrix,
        "stories_df": df.copy(),
        "total_stories": len(df),
        "categories": categories,
        "built_timestamp": time.time()
    }

    with open(index_path, "wb") as f:
        pickle.dump(index_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"[+] Serialized story index bundle to: {index_path} ({len(df):,} stories)")


# Resolve robust absolute default paths relative to this file
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(MODULE_DIR)
DEFAULT_VEC_PATH = os.path.join(PROJECT_ROOT, "models", "tfidf_vectorizer.pkl")
DEFAULT_IDX_PATH = os.path.join(PROJECT_ROOT, "models", "story_index.pkl")


def load_story_index(
    vectorizer_path: str = None,
    index_path: str = None
):
    """
    Loads pre-trained vectorizer and story index into memory.
    """
    vectorizer_path = vectorizer_path or DEFAULT_VEC_PATH
    index_path = index_path or DEFAULT_IDX_PATH

    if not os.path.exists(vectorizer_path):
        raise FileNotFoundError(f"Vectorizer file not found at: {vectorizer_path}")
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Story index file not found at: {index_path}")

    with open(vectorizer_path, "rb") as f:
        vectorizer = pickle.load(f)

    with open(index_path, "rb") as f:
        index_data = pickle.load(f)

    return vectorizer, index_data["tfidf_matrix"], index_data["stories_df"], index_data["categories"]


def run_indexing(
    processed_csv_path: str = "data/processed/processed_stories.csv",
    vectorizer_path: str = "models/tfidf_vectorizer.pkl",
    index_path: str = "models/story_index.pkl"
):
    """Executes the complete TF-IDF modeling and indexing pipeline."""
    print("=" * 65)
    print("STEP 2: TF-IDF VECTORIZATION & STORY INDEX CREATION")
    print("=" * 65)

    if not os.path.exists(processed_csv_path):
        raise FileNotFoundError(f"Processed dataset not found at: {processed_csv_path}. Run preprocessing first.")

    df = pd.read_csv(processed_csv_path, encoding="utf-8")
    vectorizer, tfidf_matrix = build_and_fit_tfidf(df)
    save_story_index(vectorizer, tfidf_matrix, df, vectorizer_path, index_path)

    print("\n[+] TF-IDF Story Indexing Completed Successfully!")
    return vectorizer, tfidf_matrix, df


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PROCESSED_PATH = os.path.join(BASE_DIR, "data", "processed", "processed_stories.csv")
    VEC_PATH = os.path.join(BASE_DIR, "models", "tfidf_vectorizer.pkl")
    IDX_PATH = os.path.join(BASE_DIR, "models", "story_index.pkl")

    run_indexing(PROCESSED_PATH, VEC_PATH, IDX_PATH)
