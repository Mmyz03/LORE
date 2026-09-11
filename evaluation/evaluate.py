"""
AI-Based Story Recommendation and Retrieval System
Module: Recommendation Benchmark & Evaluation Suite
"""

import os
import json
import pandas as pd
from recommendation.story_recommender import StoryRecommender


BENCHMARK_TEST_SET = [
    {"query": "Tell me a scary horror story with ghosts", "expected_category": "Horror"},
    {"query": "A mysterious detective solving a locked room crime", "expected_category": "Mystery"},
    {"query": "A dangerous jungle expedition for lost ancient treasure", "expected_category": "Adventure"},
    {"query": "A romantic love story with serendipity and a waltz", "expected_category": "Romance"},
    {"query": "Something funny with chaotic cooking and laughter", "expected_category": "Comedy"},
    {"query": "A magical fantasy kingdom with dragons and an enchanted sword", "expected_category": "Fantasy"},
    {"query": "A science fiction story about deep space exploration and alien planets", "expected_category": "Sci-Fi"},
    {"query": "A high-stakes spy thriller with secret agents and an escape countdown", "expected_category": "Thriller"},
    {"query": "A heartwarming story about unlikely animal friendship and loyalty", "expected_category": "Friendship"},
    {"query": "An emotional and bittersweet memory of grandfather and family love", "expected_category": "Emotional"},
    {"query": "A moral lesson about honesty being rewarded over greed", "expected_category": "Moral"},
    {"query": "A playful and cute story for children about a bear looking for his roar", "expected_category": "Children's Stories"},
    {"query": "A calming and soothing bedtime lullaby to help me sleep peacefully", "expected_category": "Bedtime Stories"}
]


def run_evaluation(
    vectorizer_path: str = "models/tfidf_vectorizer.pkl",
    index_path: str = "models/story_index.pkl",
    results_save_path: str = "evaluation/evaluation_results.json"
):
    """
    Executes automated retrieval evaluation across the benchmark test suite.
    Calculates Top-1 Categorical Accuracy, Top-3 Retrieval Accuracy,
    and Mean Cosine Relevance Scores.
    """
    print("=" * 80)
    print("AI STORY RECOMMENDER - BENCHMARK EVALUATION SUITE")
    print("=" * 80)

    recommender = StoryRecommender(vectorizer_path=vectorizer_path, index_path=index_path)

    total_queries = len(BENCHMARK_TEST_SET)
    top1_correct = 0
    top3_correct = 0
    relevance_scores = []
    detailed_results = []

    print(f"\n{'Query':<45} | {'Expected':<16} | {'Retrieved':<16} | {'Top-1':<5} | {'Relevance':<8}")
    print("-" * 100)

    for item in BENCHMARK_TEST_SET:
        query = item["query"]
        expected_cat = item["expected_category"]

        # Run recommendation
        result = recommender.recommend(query=query, top_k=5)
        retrieved_story = result["story"]
        retrieved_cat = retrieved_story["category"]
        relevance_pct = result["relevance_percentage"]
        relevance_scores.append(relevance_pct)

        # Check Top-1 Category Match
        is_top1 = (retrieved_cat.lower() == expected_cat.lower())
        if is_top1:
            top1_correct += 1

        # Check Top-3 Candidate Categories
        parsed_cats = [c.lower() for c in result["parsed_intent"]["categories"]]
        is_top3 = is_top1 or (expected_cat.lower() in parsed_cats)
        if is_top3:
            top3_correct += 1

        mark = "[PASS]" if is_top1 else "[FAIL]"
        truncated_query = (query[:42] + '...') if len(query) > 42 else query
        print(f"{truncated_query:<45} | {expected_cat:<16} | {retrieved_cat:<16} | {mark:<5} | {relevance_pct}%")

        detailed_results.append({
            "query": query,
            "expected_category": expected_cat,
            "retrieved_title": retrieved_story["title"],
            "retrieved_category": retrieved_cat,
            "top1_match": is_top1,
            "relevance_percentage": relevance_pct,
            "why_this_story": result["why_this_story"]
        })

    top1_acc = round((top1_correct / total_queries) * 100, 2)
    top3_acc = round((top3_correct / total_queries) * 100, 2)
    mean_relevance = round(sum(relevance_scores) / total_queries, 2)

    summary_metrics = {
        "total_test_queries": total_queries,
        "top1_accuracy_percent": top1_acc,
        "top3_accuracy_percent": top3_acc,
        "mean_relevance_percent": mean_relevance,
        "detailed_results": detailed_results
    }

    print("-" * 100)
    print("EVALUATION SUMMARY METRICS:")
    print(f"  [+] Total Evaluated Queries : {total_queries}")
    print(f"  [+] Top-1 Accuracy          : {top1_acc}% ({top1_correct}/{total_queries})")
    print(f"  [+] Top-3 Accuracy          : {top3_acc}% ({top3_correct}/{total_queries})")
    print(f"  [+] Mean Relevance Score    : {mean_relevance}%")
    print("=" * 80)

    os.makedirs(os.path.dirname(results_save_path), exist_ok=True)
    with open(results_save_path, "w", encoding="utf-8") as f:
        json.dump(summary_metrics, f, indent=4)
    print(f"[+] Evaluation report exported to: {results_save_path}")

    return summary_metrics


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    VEC_PATH = os.path.join(BASE_DIR, "models", "tfidf_vectorizer.pkl")
    IDX_PATH = os.path.join(BASE_DIR, "models", "story_index.pkl")
    RES_PATH = os.path.join(BASE_DIR, "evaluation", "evaluation_results.json")

    run_evaluation(VEC_PATH, IDX_PATH, RES_PATH)
