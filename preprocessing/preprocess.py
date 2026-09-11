"""
AI-Based Story Recommendation and Retrieval System
Module: NLP Preprocessing, Robust Dataset Ingestion & Feature Engineering

Features:
- Robust multi-type support: handles strings, lists, arrays, dictionaries, None/NaN safely
- Flexible column aliasing (title, story/content, category/genre, tags/keywords)
- Multi-file format support (.csv, .json, .jsonl, .tsv)
- Robust dataset validation: skips empty content, detects duplicates, handles malformed records
- Stop-words removal & WordNet lemmatization
- Searchable feature weighting and metadata engineering
- Word count & reading time calculation
- Terminal logging of loaded, processed, skipped, and category distributions
"""

import os
import re
import json
import hashlib
import glob
import math
import pandas as pd
import nltk

# Gracefully initialize NLTK or fallback
STOP_WORDS = None
LEMMATIZER = None

try:
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    STOP_WORDS = set(stopwords.words('english'))
    LEMMATIZER = WordNetLemmatizer()
except Exception:
    pass

if STOP_WORDS is None:
    STOP_WORDS = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
        "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
        "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
        "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
        "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
        "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
        "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
        "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
        "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
        "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
        "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
        "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
        "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
        "they've", "this", "those", "through", "to", "too", "under", "until", "up",
        "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
        "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
        "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
        "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
        "yourself", "yourselves"
    }

# Conversational filler words in user requests
CONVERSATIONAL_FILLERS = {
    "tell", "give", "show", "find", "read", "recommend", "want", "like", "story", "stories",
    "please", "looking", "need", "something", "kind", "type", "around", "about"
}

# Column aliases mapping to standardized names
COLUMN_ALIASES = {
    "id": ["id", "story_id", "storyid", "uuid", "key"],
    "title": ["title", "name", "story_title", "heading", "story_name", "book_title"],
    "story": ["story", "story_text", "content", "body", "text", "narrative", "full_text", "article"],
    "category": ["category", "genre", "category_name", "topic", "type", "theme_category"],
    "theme": ["theme", "subgenre", "subject", "sub_category", "plot_theme"],
    "setting": ["setting", "location", "place", "environment", "world", "backdrop"],
    "mood": ["mood", "tone", "atmosphere", "sentiment", "feeling", "vibe"],
    "keywords": ["keywords", "tags", "labels", "descriptors", "keyword_list"]
}


def safe_to_string(val, delimiter=" ") -> str:
    """
    Safely converts any arbitrary data type (string, list, tuple, set, dict, float, None, NaN)
    into a clean, normalized string representation.
    - If list/tuple/set: joins elements with delimiter
    - If dict: joins values
    - If None or float NaN: returns ""
    - If string: returns stripped string
    """
    if val is None:
        return ""
    if isinstance(val, float):
        if math.isnan(val):
            return ""
        return str(val)
    if isinstance(val, (list, tuple, set)):
        items = []
        for x in val:
            s = safe_to_string(x, delimiter=delimiter).strip()
            if s:
                items.append(s)
        return delimiter.join(items)
    if isinstance(val, dict):
        items = []
        for v in val.values():
            s = safe_to_string(v, delimiter=delimiter).strip()
            if s:
                items.append(s)
        return delimiter.join(items)
    
    s = str(val).strip()
    if s.lower() in ("nan", "none", "null"):
        return ""
    return s


def clean_text(text) -> str:
    """
    Cleans and normalizes raw text input of any data type:
    - Safely converts lists/arrays/nulls to string
    - Lowercases text
    - Replaces contractions
    - Strips special punctuation/symbols
    - Normalizes extra whitespace
    """
    text_str = safe_to_string(text)
    if not text_str:
        return ""

    text_str = text_str.lower()

    # Contraction expansions
    contractions = {
        r"\bcan't\b": "cannot",
        r"\bwon't\b": "will not",
        r"\bn't\b": " not",
        r"\b're\b": " are",
        r"\b's\b": " is",
        r"\b'd\b": " would",
        r"\b'll\b": " will",
        r"\b've\b": " have",
        r"\b'm\b": " am",
    }
    for pattern, replacement in contractions.items():
        text_str = re.sub(pattern, replacement, text_str)

    # Remove non-alphanumeric characters (keep alphanumeric and space)
    text_str = re.sub(r"[^a-zA-Z0-9\s]", " ", text_str)

    # Collapse multiple whitespaces
    text_str = re.sub(r"\s+", " ", text_str).strip()
    return text_str


def tokenize_and_lemmatize(text, remove_conversational: bool = False) -> str:
    """
    Tokenizes text, removes stop words, and applies lemmatization.
    Accepts string, list, or any type safely.
    Returns cleaned space-separated token string.
    """
    cleaned = clean_text(text)
    tokens = cleaned.split()

    stoplist = STOP_WORDS
    if remove_conversational:
        stoplist = STOP_WORDS.union(CONVERSATIONAL_FILLERS)

    filtered_tokens = []
    for token in tokens:
        if token not in stoplist and len(token) > 1:
            if LEMMATIZER:
                try:
                    token = LEMMATIZER.lemmatize(token)
                except Exception:
                    pass
            filtered_tokens.append(token)

    return " ".join(filtered_tokens)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps varied column names into standardized schema:
    [id, title, story, category, theme, setting, mood, keywords]
    """
    col_mapping = {}
    lower_to_orig = {str(col).lower().strip().replace(" ", "_"): col for col in df.columns}

    for std_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_to_orig:
                col_mapping[lower_to_orig[alias]] = std_name
                break

    df = df.rename(columns=col_mapping)
    return df


def load_raw_dataset_files(raw_path: str) -> list:
    """
    Loads records from a specific file or all CSV/JSON/JSONL files in a directory.
    Returns list of dictionaries.
    """
    records = []
    files_to_load = []

    if os.path.isfile(raw_path):
        files_to_load.append(raw_path)
    elif os.path.isdir(raw_path):
        patterns = ["*.csv", "*.json", "*.jsonl", "*.tsv"]
        for p in patterns:
            files_to_load.extend(glob.glob(os.path.join(raw_path, p)))
    else:
        raise FileNotFoundError(f"Specified raw path does not exist: {raw_path}")

    print(f"[*] Found {len(files_to_load)} raw dataset file(s) to process:")
    for fpath in files_to_load:
        print(f"    - {os.path.basename(fpath)}")

    for fpath in files_to_load:
        fname = os.path.basename(fpath).lower()
        try:
            if fname.endswith(".csv") or fname.endswith(".tsv"):
                sep = "\t" if fname.endswith(".tsv") else ","
                try:
                    file_df = pd.read_csv(fpath, sep=sep, encoding="utf-8", on_bad_lines="skip")
                except UnicodeDecodeError:
                    file_df = pd.read_csv(fpath, sep=sep, encoding="latin1", on_bad_lines="skip")
                file_df = standardize_columns(file_df)
                records.extend(file_df.to_dict(orient="records"))

            elif fname.endswith(".jsonl"):
                with open(fpath, "r", encoding="utf-8", errors="ignore") as jf:
                    for line in jf:
                        line = line.strip()
                        if line:
                            try:
                                item = json.loads(line)
                                if isinstance(item, dict):
                                    records.append(item)
                            except Exception:
                                pass

            elif fname.endswith(".json"):
                with open(fpath, "r", encoding="utf-8", errors="ignore") as jf:
                    data = json.load(jf)
                    if isinstance(data, list):
                        records.extend(data)
                    elif isinstance(data, dict):
                        if "stories" in data and isinstance(data["stories"], list):
                            records.extend(data["stories"])
                        else:
                            records.append(data)
        except Exception as e:
            print(f"[!] Warning: Error reading file {fpath}: {e}. Skipping file.")

    return records


def validate_and_sanitize_records(records: list) -> tuple:
    """
    Validates dataset records:
    - Safely coerces all fields (strings, lists, arrays, dicts) to valid clean strings
    - Detects and skips empty or ultra-short stories (< 20 characters)
    - Detects and skips duplicates (by text hash / title)
    - Fills missing titles / metadata
    - Generates unique IDs if missing
    Returns: (valid_records, validation_report)
    """
    valid_records = []
    seen_content_hashes = set()
    seen_titles = set()

    skipped_empty = 0
    skipped_duplicates = 0
    skipped_malformed = 0
    missing_titles_fixed = 0

    total_loaded = len(records)

    for idx, item in enumerate(records):
        if not isinstance(item, dict):
            skipped_malformed += 1
            continue

        # Standardize keys in dictionary
        cleaned_item = {}
        for k, v in item.items():
            k_clean = str(k).lower().strip().replace(" ", "_")
            matched_std = None
            for std_name, aliases in COLUMN_ALIASES.items():
                if k_clean in aliases:
                    matched_std = std_name
                    break
            if matched_std:
                cleaned_item[matched_std] = v
            else:
                cleaned_item[k_clean] = v

        # Extract and safely stringify fields (handles lists, arrays, None, etc.)
        story_text = safe_to_string(cleaned_item.get("story", "")).strip()

        # 1. Validation: Empty or unusable content
        if not story_text or len(story_text) < 20:
            skipped_empty += 1
            continue

        # Normalize text to detect exact duplicates
        norm_content = re.sub(r"\s+", " ", story_text).strip().lower()
        content_hash = hashlib.md5(norm_content[:500].encode("utf-8")).hexdigest()

        title = safe_to_string(cleaned_item.get("title", "")).strip()
        norm_title = title.lower()

        # 2. Validation: Duplicate Detection
        if content_hash in seen_content_hashes:
            skipped_duplicates += 1
            continue

        seen_content_hashes.add(content_hash)
        if norm_title:
            seen_titles.add(norm_title)

        # 3. Handle missing title
        if not title:
            words = story_text.split()
            title = " ".join(words[:5]).capitalize() + "..."
            missing_titles_fixed += 1

        # 4. Handle metadata & ID with safe string conversion
        category = safe_to_string(cleaned_item.get("category", "")).strip()
        if not category:
            category = "General"

        theme = safe_to_string(cleaned_item.get("theme", "")).strip()
        if not theme:
            theme = category

        setting = safe_to_string(cleaned_item.get("setting", "")).strip()
        if not setting:
            setting = "Atmospheric Setting"

        mood = safe_to_string(cleaned_item.get("mood", "")).strip()
        if not mood:
            mood = "Engaging"

        keywords = safe_to_string(cleaned_item.get("keywords", ""), delimiter=", ").strip()
        if not keywords:
            keywords = f"{category.lower()}, {theme.lower()}, {mood.lower()}"

        story_id = safe_to_string(cleaned_item.get("id", "")).strip()
        if not story_id:
            story_id = f"ST-{len(valid_records) + 1:04d}"

        sanitized_record = {
            "id": story_id,
            "title": title,
            "story": story_text,
            "category": category,
            "theme": theme,
            "setting": setting,
            "mood": mood,
            "keywords": keywords
        }

        valid_records.append(sanitized_record)

    report = {
        "total_loaded": total_loaded,
        "valid_count": len(valid_records),
        "skipped_empty": skipped_empty,
        "skipped_duplicates": skipped_duplicates,
        "skipped_malformed": skipped_malformed,
        "missing_titles_fixed": missing_titles_fixed
    }

    return valid_records, report


def engineer_searchable_content(row) -> str:
    """
    Combines story fields into a weighted searchable document.
    Metadata fields (category, theme, mood, setting, keywords) are weighted
    to ensure high precision on natural-language and categorical queries.
    Safely stringifies all inputs regardless of whether row is Series or dict.
    """
    if isinstance(row, dict):
        title = safe_to_string(row.get('title', ''))
        category = safe_to_string(row.get('category', ''))
        theme = safe_to_string(row.get('theme', ''))
        setting = safe_to_string(row.get('setting', ''))
        mood = safe_to_string(row.get('mood', ''))
        keywords = safe_to_string(row.get('keywords', ''))
        story = safe_to_string(row.get('story', ''))
    else:
        title = safe_to_string(row.get('title', ''))
        category = safe_to_string(row.get('category', ''))
        theme = safe_to_string(row.get('theme', ''))
        setting = safe_to_string(row.get('setting', ''))
        mood = safe_to_string(row.get('mood', ''))
        keywords = safe_to_string(row.get('keywords', ''))
        story = safe_to_string(row.get('story', ''))

    # Weighting: emphasize metadata keywords + full narrative content
    weighted_parts = [
        title, title,
        category, category, category,
        theme, theme,
        setting, setting,
        mood, mood,
        keywords, keywords,
        story
    ]

    combined_text = " ".join([p for p in weighted_parts if p])
    processed_tokens = tokenize_and_lemmatize(combined_text, remove_conversational=False)
    return processed_tokens


def process_dataset(raw_input_path: str, processed_csv_path: str) -> pd.DataFrame:
    """
    Complete pipeline:
    1. Loads all raw files (.csv, .json, .jsonl, .tsv)
    2. Validates records, skips duplicates & empty stories
    3. Cleans and lemmatizes text
    4. Computes word count & reading time
    5. Saves standardized processed CSV
    """
    print("=" * 65)
    print("STEP 1: DATASET INGESTION & NLP PREPROCESSING PIPELINE")
    print("=" * 65)

    raw_records = load_raw_dataset_files(raw_input_path)
    if not raw_records:
        raise ValueError(f"No valid story records found in {raw_input_path}")

    valid_records, report = validate_and_sanitize_records(raw_records)

    print("\n--- [ Dataset Validation Report ] ---")
    print(f"  - Total raw records loaded  : {report['total_loaded']}")
    print(f"  - Skipped (Empty / Short)   : {report['skipped_empty']}")
    print(f"  - Skipped (Duplicates)      : {report['skipped_duplicates']}")
    print(f"  - Skipped (Malformed)       : {report['skipped_malformed']}")
    print(f"  - Missing Titles Fixed      : {report['missing_titles_fixed']}")
    print(f"  - Successfully Validated    : {report['valid_count']} stories")
    print("-------------------------------------\n")

    if not valid_records:
        raise ValueError("All records in the dataset were empty, duplicate, or invalid.")

    df = pd.DataFrame(valid_records)

    # Ensure all columns are clean Python strings
    for col in ['id', 'title', 'category', 'theme', 'setting', 'mood', 'keywords', 'story']:
        if col in df.columns:
            df[col] = df[col].apply(safe_to_string)

    print("[+] Engineering searchable NLP tokens (stop-words removal & lemmatization)...")
    df['searchable_text'] = df.apply(engineer_searchable_content, axis=1)

    # Word count and reading time metadata
    df['word_count'] = df['story'].apply(lambda s: len(str(s).split()))
    df['reading_time_min'] = df['word_count'].apply(lambda w: max(1, round(w / 200)))

    os.makedirs(os.path.dirname(processed_csv_path), exist_ok=True)
    df.to_csv(processed_csv_path, index=False, encoding="utf-8")

    print(f"[+] Processed dataset saved to: {processed_csv_path}")
    print(f"[+] Total indexed stories     : {len(df)}")
    print(f"[+] Categories detected ({len(df['category'].unique())}):")
    for cat, count in df['category'].value_counts().items():
        print(f"    - {cat:20s}: {count} stories")

    return df


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RAW_PATH = os.path.join(BASE_DIR, "data", "raw")
    PROCESSED_PATH = os.path.join(BASE_DIR, "data", "processed", "processed_stories.csv")

    process_dataset(RAW_PATH, PROCESSED_PATH)
