

"""
AI-Based Story Recommendation and Retrieval System
Master Pipeline Script: Ingestion -> Preprocessing -> Indexing -> Diagnostics

Run this script whenever you add or modify datasets in data/raw/:
    python pipeline.py
    or:
    py pipeline.py
"""

import os
import sys
import time
import argparse

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from preprocessing.preprocess import process_dataset
from recommendation.tfidf_model import run_indexing, load_story_index


def run_full_pipeline(raw_dir=None, processed_path=None, vectorizer_path=None, index_path=None):
    """
    Executes the unified end-to-end dataset pipeline:
    1. Ingests and validates all files in data/raw/
    2. Cleans text, applies NLP lemmatization, and engineers searchable content
    3. Saves processed dataset to data/processed/
    4. Builds and serializes the Scikit-Learn TF-IDF index & sparse matrix
    5. Verifies index loading & outputs diagnostics
    """
    start_total_time = time.time()

    if raw_dir is None:
        raw_dir = os.path.join(PROJECT_ROOT, "data", "raw")
    if processed_path is None:
        processed_path = os.path.join(PROJECT_ROOT, "data", "processed", "processed_stories.csv")
    if vectorizer_path is None:
        vectorizer_path = os.path.join(PROJECT_ROOT, "models", "tfidf_vectorizer.pkl")
    if index_path is None:
        index_path = os.path.join(PROJECT_ROOT, "models", "story_index.pkl")

    print("\n" + "=" * 70)
    print("      LORE - STORY RECOMMENDATION SYSTEM: DATASET PIPELINE")
    print("=" * 70)
    print(f"[*] Project Root      : {PROJECT_ROOT}")
    print(f"[*] Raw Data Path     : {raw_dir}")
    print(f"[*] Processed Output  : {processed_path}")
    print(f"[*] Model Index Path  : {index_path}\n")

    # Step 1: Preprocessing & Data Validation
    df_processed = process_dataset(raw_dir, processed_path)

    # Step 2: TF-IDF Vectorization & Model Serialization
    print()
    vectorizer, tfidf_matrix, df_indexed = run_indexing(
        processed_csv_path=processed_path,
        vectorizer_path=vectorizer_path,
        index_path=index_path
    )

    # Step 3: Diagnostic Verification & Health Check
    print("\n" + "=" * 70)
    print("STEP 3: SYSTEM INTEGRITY CHECK & DIAGNOSTICS")
    print("=" * 70)

    try:
        vec, matrix, df_loaded, cats = load_story_index(vectorizer_path, index_path)
        total_count = len(df_loaded)
        total_cats = len(cats)
        total_features = len(vec.get_feature_names_out())
        total_words = df_loaded['word_count'].sum() if 'word_count' in df_loaded.columns else 0

        total_elapsed = round(time.time() - start_total_time, 2)

        print(f"  [OK] Model Loading Verification : PASSED")
        print(f"  [OK] Successfully Indexed       : {total_count:,} stories")
        print(f"  [OK] Total Story Categories     : {total_cats}")
        print(f"  [OK] TF-IDF N-Gram Features     : {total_features:,}")
        print(f"  [OK] Total Story Word Corpus    : {total_words:,} words")
        print(f"  [OK] Pipeline Execution Time    : {total_elapsed} seconds")
        print("=" * 70)
        print(f"\n>> LORE story index is ready! ({total_count:,} Stories Indexed)\n")

    except Exception as e:
        print(f"[!] Error verifying story index: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LORE Story Dataset Ingestion and Indexing Pipeline")
    parser.add_argument("--raw", type=str, default=None, help="Path to raw dataset folder or file")
    parser.add_argument("--processed", type=str, default=None, help="Path to save processed CSV")
    args = parser.parse_args()

    run_full_pipeline(raw_dir=args.raw, processed_path=args.processed)
