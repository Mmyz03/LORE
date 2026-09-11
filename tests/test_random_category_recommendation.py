"""
Specialized Test Suite: True Random Story within Same Category for LORE
Validates:
1. Category Determination from NLP queries
2. Session Category Preservation across consecutive "Find Another Story" requests
3. True Random Selection within the determined category (not just top TF-IDF score)
4. Duplicate Exclusion using Rolling ID History
5. Graceful handling of exhausted category cycles
"""

import sys
import os
import json
import urllib.request
import urllib.error

SERVER_URL = "http://127.0.0.1:5000"

def recommend_api(query, category=None, exclude_ids=None, is_find_another=False):
    payload = json.dumps({
        "query": query,
        "category": category,
        "exclude_ids": exclude_ids or [],
        "is_find_another": is_find_another
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{SERVER_URL}/api/recommend",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def test_query_flow(test_name, initial_query, expected_category, iterations=5):
    print(f"\n--- Testing Flow: '{initial_query}' (Expected: {expected_category}) ---")
    
    # 1. Initial Generate Story
    res1 = recommend_api(query=initial_query, is_find_another=False)
    assert res1["status"] == "success", f"Failed initial request: {res1}"
    story1 = res1["story"]
    session_category = res1.get("category") or story1["category"]
    
    print(f"  [1] Initial Story: [{story1['id']}] '{story1['title']}' | Category: {session_category}")
    assert session_category.lower() == expected_category.lower(), (
        f"Category mismatch on initial query: got '{session_category}', expected '{expected_category}'"
    )
    
    seen_ids = [story1["id"]]
    stories_seen = [story1]
    
    # 2. Consecutive "Find Another Story" calls
    for i in range(1, iterations + 1):
        res_next = recommend_api(
            query=initial_query,
            category=session_category,
            exclude_ids=seen_ids[-15:], # Rolling window
            is_find_another=True
        )
        assert res_next["status"] == "success", f"Failed Find Another iteration {i}: {res_next}"
        story_next = res_next["story"]
        story_cat = res_next.get("category") or story_next["category"]
        
        print(f"  [{i+1}] Find Another #{i}: [{story_next['id']}] '{story_next['title']}' | Category: {story_cat}")
        
        # CATEGORY MUST REMAIN EXACTLY THE SAME
        assert story_cat.lower() == expected_category.lower(), (
            f"Category changed on Find Another #{i}! Expected '{expected_category}', got '{story_cat}'"
        )
        
        # MUST NOT REPEAT IMMEDIATELY RECENT STORIES
        if len(seen_ids) < 35:  # Category has 40 stories
            assert story_next["id"] not in seen_ids[-15:], (
                f"Story ID {story_next['id']} was repeated within the recent exclusion window!"
            )
            
        seen_ids.append(story_next["id"])
        stories_seen.append(story_next)

    # Verify diversity across iterations
    unique_ids = set(s["id"] for s in stories_seen)
    print(f"  [PASS] {len(unique_ids)} unique {expected_category} stories retrieved across {len(stories_seen)} requests without category drift.")

def test_randomness_distribution():
    print("\n--- Testing True Random Distribution in Horror Category ---")
    first_stories = []
    for _ in range(10):
        res = recommend_api(
            query="",
            category="Horror",
            exclude_ids=[],
            is_find_another=True
        )
        first_stories.append(res["story"]["id"])
    
    unique_picks = len(set(first_stories))
    print(f"  Picks across 10 random requests: {first_stories} ({unique_picks} unique)")
    assert unique_picks > 4, "Randomness test failed: too many duplicate selections without exclusion"
    print("  [PASS] True random distribution verified.")

def test_exhaustion_resilience():
    print("\n--- Testing Cycle Resilience when Category Stories are Exhausted ---")
    seen_ids = []
    for i in range(45):  # Horror has 40 stories
        res = recommend_api(
            query="",
            category="Horror",
            exclude_ids=seen_ids[-15:],
            is_find_another=True
        )
        assert res["status"] == "success"
        current_id = res["story"]["id"]
        if seen_ids:
            assert current_id != seen_ids[-1], "Immediate back-to-back duplicate occurred!"
        seen_ids.append(current_id)
    print(f"  [PASS] Successfully retrieved 45 consecutive stories without error or immediate repeats.")

if __name__ == "__main__":
    print("==========================================================")
    print(" LORE Category Preservation & Random Story Verification   ")
    print("==========================================================")
    
    test_query_flow("Horror Query", "I want a scary haunted house story", "Horror", iterations=5)
    test_query_flow("Friendship Query", "funny friendship story", "Friendship", iterations=5)
    test_query_flow("Romance Query", "romantic love story", "Romance", iterations=5)
    test_query_flow("Mystery Query", "a mysterious detective story", "Mystery", iterations=5)
    
    test_randomness_distribution()
    test_exhaustion_resilience()
    
    print("\n==========================================================")
    print(" ALL RECOMMENDATION & CATEGORY TESTS PASSED (100%)       ")
    print("==========================================================")
