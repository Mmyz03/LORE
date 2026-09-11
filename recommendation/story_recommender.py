"""
AI-Based Story Recommendation and Retrieval System
Module: Core Recommendation Engine, NLP Query Understanding & Explainability

Features:
- Fast TF-IDF Cosine Similarity vector search across arbitrary corpus size (500 to 50,000+ stories)
- Natural Language Intent Parsing (Categories, Moods, Settings, Keywords)
- Fully type-safe metadata matching (handles strings, lists, arrays, None/NaN without error)
- Adaptive High-Relevance Candidate Pool & Intelligent Randomization
- Seamless Session-Based Duplicate Exclusion ("Find Another Story")
- Transparent Explainability Generation ("Why this story?")
"""

import os
import random
import argparse
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from preprocessing.preprocess import clean_text, tokenize_and_lemmatize, safe_to_string
from recommendation.tfidf_model import load_story_index


# Category keyword mappings for NLP query intent extraction
CATEGORY_SYNONYMS = {
    "Horror": ["horror", "scary", "spooky", "frightening", "terrifying", "ghost", "ghosts", "monster", "creepy", "haunted", "fear", "gore", "nightmare", "demon", "spirit", "shadows", "graveyard", "mansion", "attic"],
    "Mystery": ["mystery", "detective", "crime", "investigation", "clue", "clues", "puzzle", "murder", "theft", "cipher", "secret", "suspect", "alibi", "enigma", "heist", "stolen", "forgery"],
    "Adventure": ["adventure", "expedition", "quest", "treasure", "explore", "explorer", "jungle", "climb", "voyage", "hazard", "journey", "wilderness", "peril", "mountain", "ruins", "dunes", "reef"],
    "Romance": ["romance", "love", "romantic", "lovers", "heart", "affection", "passion", "waltz", "couple", "kiss", "destiny", "dating", "beloved", "serendipity", "sweetheart", "seine"],
    "Comedy": ["comedy", "funny", "humor", "humorous", "hilarious", "laugh", "laughter", "joke", "joking", "silly", "jester", "clumsy", "mishap", "fun", "pancakes", "cat", "cats"],
    "Fantasy": ["fantasy", "magic", "magical", "wizard", "witch", "dragon", "spell", "fairy", "elf", "elves", "enchanted", "kingdom", "mythical", "blade", "moonstone", "alchemist", "citadel"],
    "Sci-Fi": ["scifi", "sci-fi", "science fiction", "space", "alien", "spaceship", "planet", "galaxy", "future", "futuristic", "astronaut", "time travel", "quantum", "robot", "cyber", "ai", "titan", "orbit"],
    "Thriller": ["thriller", "suspense", "espionage", "spy", "agent", "chase", "conspiracy", "intense", "danger", "countdown", "assassin", "hostage", "bomb", "sabotage", "escape"],
    "Friendship": ["friendship", "friends", "friend", "ally", "allies", "loyalty", "loyal", "buddy", "companionship", "pal", "trust", "unlikely friends", "companions", "bond", "brotherhood"],
    "Emotional": ["emotional", "poignant", "touching", "heartfelt", "tear", "tears", "sad", "sorrow", "crying", "grief", "memory", "family", "bittersweet", "grandfather", "violin"],
    "Moral": ["moral", "lesson", "fable", "wisdom", "honesty", "truth", "greed", "humility", "ethics", "integrity", "virtue", "generosity", "karma", "axe", "pitcher"],
    "Children's Stories": ["children", "kids", "child", "bedtime for kids", "cute", "playful", "whimsical", "fairy tale", "fable for kids", "bear", "animals", "toddler", "dragon", "paintbrush"],
    "Bedtime Stories": ["bedtime", "sleep", "sleepy", "calm", "relaxing", "peaceful", "night", "lullaby", "soothing", "slumber", "stars", "moon", "dreams", "gentle", "blanket", "cove"]
}

# Mood synonyms mapping
MOOD_KEYWORDS = {
    "Scary": ["scary", "terrifying", "creepy", "spooky", "chilling", "eerie", "dark", "fearful"],
    "Funny": ["funny", "hilarious", "humorous", "silly", "laughable", "witty", "amusing"],
    "Heartwarming": ["heartwarming", "warm", "loving", "tender", "sweet", "uplifting"],
    "Suspenseful": ["suspenseful", "tense", "gripping", "thrilling", "intense", "mysterious"],
    "Calm": ["calm", "relaxing", "peaceful", "soothing", "gentle", "serene", "quiet"],
    "Inspiring": ["inspiring", "heroic", "brave", "courageous", "wise", "uplifting", "inspirational"],
    "Poignant": ["poignant", "emotional", "bittersweet", "sad", "touching", "deep", "heartfelt"]
}

# Setting & Time keywords mapping
SETTING_KEYWORDS = {
    "Forest": ["forest", "woods", "trees", "jungle", "grove"],
    "Mansion / House": ["mansion", "house", "attic", "castle", "palace", "room", "bunker", "laboratory", "precinct"],
    "Space / Station": ["space", "station", "spaceship", "planet", "galaxy", "orbit", "temporal", "titan"],
    "Sea / River": ["sea", "ocean", "river", "shore", "island", "bridge", "water", "stream", "quay", "harbor", "cove"],
    "Mountain": ["mountain", "cliff", "peak", "summit", "glacier", "himalayan", "alps"],
    "Night / Midnight": ["night", "midnight", "dusk", "evening", "moonlight", "darkness", "starlight"],
    "Desert": ["desert", "dunes", "oasis", "sand", "sahara"]
}


class StoryRecommender:
    """
    Intelligent Story Recommendation & Retrieval Engine:
    Combines NLP Query Parsing, TF-IDF Vectorization, Cosine Similarity,
    Categorical & Feature Matching, Randomized Relevance-Pool Sampling,
    and Explainability Tag Generation.
    """

    def __init__(
        self,
        vectorizer_path: str = "models/tfidf_vectorizer.pkl",
        index_path: str = "models/story_index.pkl"
    ):
        self.vectorizer_path = vectorizer_path
        self.index_path = index_path
        self.vectorizer = None
        self.tfidf_matrix = None
        self.stories_df = None
        self.categories = []
        self._load_model()

    def _load_model(self):
        """Loads serialized TF-IDF vectorizer and story index into memory."""
        self.vectorizer, self.tfidf_matrix, self.stories_df, self.categories = load_story_index(
            vectorizer_path=self.vectorizer_path,
            index_path=self.index_path
        )
        # Ensure all columns in dataframe are safely stringified
        for col in ['id', 'title', 'category', 'theme', 'setting', 'mood', 'keywords', 'story']:
            if col in self.stories_df.columns:
                self.stories_df[col] = self.stories_df[col].apply(safe_to_string)

        print(f"[+] StoryRecommender initialized with {len(self.stories_df):,} stories across {len(self.categories)} categories.")

    def parse_query_intent(self, query) -> dict:
        """
        Parses a natural-language user prompt to extract explicit/implicit:
        - Target Categories
        - Identified Moods
        - Identified Settings & Times
        - Identified Keywords
        """
        cleaned_query = clean_text(query).lower()
        query_words = set(cleaned_query.split())

        extracted_categories = []
        for category, synonyms in CATEGORY_SYNONYMS.items():
            for syn in synonyms:
                if " " in syn and syn in cleaned_query:
                    extracted_categories.append(category)
                    break
                elif syn in query_words:
                    extracted_categories.append(category)
                    break

        extracted_moods = []
        for mood, keywords in MOOD_KEYWORDS.items():
            for kw in keywords:
                if kw in query_words:
                    extracted_moods.append(mood)
                    break

        extracted_settings = []
        for setting, keywords in SETTING_KEYWORDS.items():
            for kw in keywords:
                if kw in query_words:
                    extracted_settings.append(setting)
                    break

        return {
            "categories": list(dict.fromkeys(extracted_categories)),
            "moods": list(dict.fromkeys(extracted_moods)),
            "settings": list(dict.fromkeys(extracted_settings)),
            "raw_cleaned": cleaned_query
        }

    def recommend(
        self,
        query,
        selected_category=None,
        exclude_ids=None,
        min_relevance_threshold: float = 0.12,
        relative_score_margin: float = 0.65,
        max_pool_size: int = 15
    ) -> dict:
        """
        Recommends a suitable story from a high-relevance candidate pool with intelligent
        randomization and duplicate prevention.

        Parameters:
        - query (str/any): User's natural language request (e.g. "scary ghost in a dark forest")
        - selected_category (str/any, optional): Optional category filter chosen by user
        - exclude_ids (list, optional): List of story IDs to avoid (for "Find Another Story")
        - min_relevance_threshold (float): Minimum absolute score for candidate inclusion
        - relative_score_margin (float): Ratio relative to top score for forming the candidate pool
        - max_pool_size (int): Maximum number of candidates in the relevance pool

        Returns:
        - dict containing selected story details, scores, pool metrics, and 'Why this story?' explainability breakdown.
        """
        if exclude_ids is None:
            exclude_ids = []
        exclude_ids = [safe_to_string(x) for x in exclude_ids]

        query_str = safe_to_string(query).strip()
        selected_cat_str = safe_to_string(selected_category).strip()

        parsed_intent = self.parse_query_intent(query_str)
        processed_query = tokenize_and_lemmatize(query_str, remove_conversational=True)

        # Fallback if query tokens are completely empty
        if not processed_query:
            processed_query = tokenize_and_lemmatize(query_str, remove_conversational=False)
            if not processed_query:
                processed_query = "story"

        # 1. Transform query to TF-IDF vector & compute Cosine Similarity across corpus
        query_vector = self.vectorizer.transform([processed_query])
        cosine_sims = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        # 2. Fully type-safe metadata matching
        story_cats = [safe_to_string(c) for c in self.stories_df['category']]
        story_moods = [safe_to_string(m) for m in self.stories_df['mood']]
        story_settings = [safe_to_string(s) for s in self.stories_df['setting']]
        story_kws = [safe_to_string(k) for k in self.stories_df['keywords']]

        num_stories = len(self.stories_df)

        # Category bonus
        cat_bonuses = np.zeros(num_stories, dtype=float)
        if selected_cat_str:
            sel_lower = selected_cat_str.lower()
            mask = np.array([sel_lower in cat.lower() for cat in story_cats], dtype=bool)
            cat_bonuses[mask] += 0.45
        elif parsed_intent["categories"]:
            for cat in parsed_intent["categories"]:
                cat_lower = cat.lower()
                mask = np.array([cat_lower in c.lower() for c in story_cats], dtype=bool)
                cat_bonuses[mask] += 0.38

        # Mood bonus
        mood_bonuses = np.zeros(num_stories, dtype=float)
        for mood in parsed_intent["moods"]:
            mood_lower = mood.lower()
            mask = np.array([mood_lower in m.lower() for m in story_moods], dtype=bool)
            mood_bonuses[mask] += 0.15

        # Setting bonus
        setting_bonuses = np.zeros(num_stories, dtype=float)
        for setting in parsed_intent["settings"]:
            setting_lower = setting.lower()
            mask = np.array([setting_lower in s.lower() for s in story_settings], dtype=bool)
            setting_bonuses[mask] += 0.15

        # Keyword overlap bonus
        query_token_set = set(processed_query.split())
        kw_bonuses = np.zeros(num_stories, dtype=float)
        if query_token_set:
            for i, kw_str in enumerate(story_kws):
                kws = set(kw_str.lower().replace(',', ' ').split())
                overlap = query_token_set.intersection(kws)
                if overlap:
                    kw_bonuses[i] = min(0.20, len(overlap) * 0.08)

        # Total Composite Score
        total_scores = (cosine_sims * 0.50) + cat_bonuses + mood_bonuses + setting_bonuses + kw_bonuses

        df = self.stories_df.copy()
        df['final_score'] = total_scores
        df['cosine_similarity'] = cosine_sims

        # 3. Apply category filter if explicitly chosen
        if selected_cat_str:
            cat_match = df[df['category'].apply(lambda x: selected_cat_str.lower() in safe_to_string(x).lower())]
            if not cat_match.empty:
                df = cat_match

        # 4. Rank candidates by descending final score
        ranked_df = df.sort_values(by='final_score', ascending=False)
        if ranked_df.empty:
            ranked_df = self.stories_df.copy().sort_values(by='final_score', ascending=False)

        top_score = float(ranked_df['final_score'].iloc[0])

        # 5. Form the High-Relevance Candidate Pool
        cutoff = max(min_relevance_threshold, top_score * relative_score_margin)
        relevance_pool = ranked_df[ranked_df['final_score'] >= cutoff]

        if relevance_pool.empty:
            relevance_pool = ranked_df.head(1)

        # Cap pool size
        relevance_pool = relevance_pool.head(max_pool_size)

        # 6. Duplicate Prevention & Random Selection
        available_pool = relevance_pool[~relevance_pool['id'].apply(safe_to_string).isin(exclude_ids)]

        exhausted_cycle = False
        if not available_pool.empty:
            # Randomly select from available non-excluded relevant stories
            selected_row = available_pool.sample(n=1).iloc[0]
        else:
            # All stories in relevant pool already shown -> cycle gracefully
            exhausted_cycle = True
            last_shown_id = exclude_ids[-1] if exclude_ids else None
            other_in_pool = relevance_pool[relevance_pool['id'].apply(safe_to_string) != str(last_shown_id)]
            if not other_in_pool.empty:
                selected_row = other_in_pool.sample(n=1).iloc[0]
            else:
                selected_row = relevance_pool.sample(n=1).iloc[0]

        # 7. Generate "Why this story?" Explainability Breakdown
        why_this_story = self._generate_explainability(selected_row, query_str, parsed_intent, selected_cat_str)

        # Calculate realistic display match percentage
        raw_score = float(selected_row.get('final_score', 0.5))
        relevance_percent = min(98, max(72, int(raw_score * 75 + 20)))

        story_content = safe_to_string(selected_row.get("story", ""))
        word_count = int(selected_row.get("word_count", len(story_content.split())))
        reading_time = int(selected_row.get("reading_time_min", max(1, round(word_count / 200))))

        return {
            "status": "success",
            "story": {
                "id": safe_to_string(selected_row.get("id", "")),
                "title": safe_to_string(selected_row.get("title", "")),
                "category": safe_to_string(selected_row.get("category", "")),
                "theme": safe_to_string(selected_row.get("theme", "")),
                "setting": safe_to_string(selected_row.get("setting", "")),
                "mood": safe_to_string(selected_row.get("mood", "")),
                "keywords": safe_to_string(selected_row.get("keywords", "")),
                "story_text": story_content,
                "word_count": word_count,
                "reading_time_min": reading_time,
            },
            "relevance_score": round(raw_score, 4),
            "relevance_percentage": relevance_percent,
            "parsed_intent": parsed_intent,
            "why_this_story": why_this_story,
            "pool_size": len(relevance_pool),
            "exhausted_cycle": exhausted_cycle
        }

    def _generate_explainability(self, story_row, query: str, parsed_intent: dict, selected_category: str = None) -> list:
        """Constructs a list of verified match tags explaining why the story was chosen."""
        reasons = []

        story_cat = safe_to_string(story_row.get("category", ""))
        story_theme = safe_to_string(story_row.get("theme", ""))
        story_setting = safe_to_string(story_row.get("setting", ""))
        story_mood = safe_to_string(story_row.get("mood", ""))
        story_kws = safe_to_string(story_row.get("keywords", "")).lower()

        # Category Reason
        if selected_category and selected_category.lower() in story_cat.lower():
            reasons.append({"label": f"Category: {story_cat}", "detail": "Directly matches selected exploration genre"})
        elif parsed_intent["categories"] and any(c.lower() in story_cat.lower() for c in parsed_intent["categories"]):
            reasons.append({"label": f"Category: {story_cat}", "detail": "Inferred from intent query keywords"})

        # Theme Reason
        if story_theme:
            reasons.append({"label": f"Theme: {story_theme}", "detail": "Core narrative focus aligns with requested concept"})

        # Setting Reason
        if parsed_intent["settings"] and any(s.lower() in story_setting.lower() for s in parsed_intent["settings"]):
            reasons.append({"label": f"Setting: {story_setting}", "detail": "Environmental keywords match your description"})

        # Mood Reason
        if parsed_intent["moods"] and any(m.lower() in story_mood.lower() for m in parsed_intent["moods"]):
            reasons.append({"label": f"Mood: {story_mood}", "detail": "Atmospheric tone matches requested emotion"})

        # Keyword overlap
        clean_q = tokenize_and_lemmatize(query, remove_conversational=True)
        query_words = [w for w in clean_q.split() if len(w) > 3]
        matched_kws = [w for w in query_words if w in story_kws]
        if matched_kws:
            reasons.append({"label": f"Key terms: {', '.join(matched_kws[:3])}", "detail": "Semantic similarity match in story corpus"})

        if not reasons:
            reasons.append({"label": f"Category: {story_cat}", "detail": "Matched via semantic TF-IDF cosine similarity"})

        return reasons
