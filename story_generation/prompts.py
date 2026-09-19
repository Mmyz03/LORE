"""
LORE — Master System Prompts & Story Generation Prompt Engine
"""

SYSTEM_STORY_PROMPT = """You are LORE, a world-class literary novelist and master storyteller crafted to write complete, compelling, publication-quality original short stories.

Your mission is to understand the reader's requested premise, genre preset, atmosphere, character dynamics, and length constraints, then compose a cohesive, immersive, and fully developed original short story.

NARRATIVE EXCELLENCE REQUIREMENTS:
1. COMPLETE NARRATIVE ARC: Every story MUST be a complete and fully realized tale with a distinct 6-stage arc:
   - Compelling Hook / Exposition: Establishes setting, atmospheric tone, and character presence.
   - Inciting Incident: The pivotal spark or disturbance that initiates the story's trajectory.
   - Character & Setting Development: Believable motivations, sensory details, and tangible world-building.
   - Conflict & Rising Tension: Deepening stakes, obstacles, friction, or mysteries.
   - Dramatic Climax: The high point of emotional or physical confrontation.
   - Meaningful Resolution & Ending: A deliberate, earned conclusion that brings closure (no abrupt cut-offs, no unfinished fragments, no filler).

2. PROSE & DIALOGUE QUALITY:
   - Evocative sensory descriptions (scents, textures, light, acoustics).
   - Natural, distinct dialogue that reveals character personality.
   - Varied sentence cadence and pacing.
   - Avoid clichés, generic summaries, and repetitive wording.

3. ZERO AI SELF-REFERENCE:
   - Never refer to AI, prompts, instructions, language models, or generation within the story or metadata.
   - Write purely with the authentic voice of a seasoned literary author.

OUTPUT FORMAT:
You MUST respond with ONLY a single valid JSON object formatted EXACTLY as follows (with NO markdown code fences, comments, or surrounding text):
{
  "title": "An evocative, original story title",
  "genre": "Identified primary genre (e.g., Mystery, Horror, Romance, Fantasy, Adventure, Science Fiction, Thriller, Comedy, Emotional, Friendship, Moral, Bedtime)",
  "summary": "A crisp, compelling 2-sentence synopsis capturing the core premise and emotional stakes.",
  "content": "The complete, unabridged narrative structured into rich paragraphs separated by double newlines (\\n\\n).",
  "tags": ["Primary Genre", "Atmosphere", "Theme", "Key Motif"]
}
"""

CATEGORY_GUIDES = {
    "mystery": "Establish an intriguing crime, puzzle, or enigma early; weave concrete clues and subtle red herrings; maintain logical suspect dynamics; and reveal a satisfying, well-earned deduction or twist.",
    "horror": "Build atmospheric dread and psychological tension gradually; utilize vivid sensory details of shadows, temperatures, and silence; escalate the encounter with the unknown; and deliver a haunting climax.",
    "romance": "Cultivate genuine emotional vulnerability, magnetic character chemistry, unspoken tension, interpersonal obstacles, and a deeply felt, heartfelt resolution.",
    "fantasy": "Immerse the reader in enchanting world-building with consistent internal logic, mythical lore, wonder, high stakes, and poignant personal sacrifice.",
    "adventure": "Drive the story forward with perilous environments, expeditions, daring decisions, physical trials, and perseverance against overwhelming odds.",
    "sci-fi": "Integrate speculative concepts, futuristic technology, deep space, or existential questions seamlessly with personal human stakes and survival.",
    "science fiction": "Integrate speculative concepts, futuristic technology, deep space, or existential questions seamlessly with personal human stakes and survival.",
    "thriller": "Maintain a relentless ticking clock, immediate physical/psychological peril, high-stakes suspense, and sudden turns of fortune.",
    "comedy": "Employ clever wit, situational irony, escalating comic misunderstandings, vibrant banter, and a delightfully satisfying payoff.",
    "emotional": "Explore poignant memories, human dignity, grief, healing, bittersweet nostalgia, and profound emotional empathy.",
    "friendship": "Highlight unyielding loyalty, shared trials, childhood promises, mutual trust, and the enduring bond between companions.",
    "moral": "Craft a timeless fable or ethical dilemma where character choices reveal wisdom, consequence, humility, or the true nature of integrity.",
    "bedtime": "Create a soothing, lyrical, and comforting narrative filled with tranquility, calm wonder, gentle imagery, and a restful, peaceful close."
}

LENGTH_SPECIFICATIONS = {
    "default": "STORY LENGTH: Normal story equivalent to approximately 2 pages of readable content (~900 to 1,400 words, formatted across 4 to 6 substantial paragraphs). Ensure the story is substantial and immersive—neither excessively short nor unnecessarily drawn out.",
    "short": "STORY LENGTH: A tight, concise single-page short story (~450 to 750 words, formatted across 3 to 4 paragraphs) with rapid pacing and a swift, punchy arc.",
    "1-page": "STORY LENGTH: A tight, concise single-page short story (~450 to 750 words, formatted across 3 to 4 paragraphs) with rapid pacing and a swift, punchy arc.",
    "long": "STORY LENGTH: An extended, multi-page narrative (~1,800 to 2,500 words, formatted across 6 to 10 comprehensive paragraphs) with rich world-building, in-depth character development, and intricate scene progression.",
    "3-5 pages": "STORY LENGTH: An extended, multi-page narrative (~1,800 to 2,500 words, formatted across 6 to 10 comprehensive paragraphs) with rich world-building, in-depth character development, and intricate scene progression."
}


def build_story_prompt(
    user_prompt: str = "",
    category: str = None,
    length: str = "default",
    is_another: bool = False,
    previous_titles: list = None
) -> tuple[str, str]:
    """
    Constructs the system prompt and structured user prompt payload for LLM generation.
    Supports genre presets, natural language ideas, custom length calibration, and
    anti-repetition safeguards.
    """
    prompt_clean = (user_prompt or "").strip()
    cat_clean = (category or "").strip()
    length_clean = (length or "default").strip().lower()

    # Determine prompt core
    if prompt_clean and cat_clean:
        core_request = f"CATEGORY PRESET: {cat_clean}\nREADER STORY REQUEST: \"{prompt_clean}\""
    elif prompt_clean:
        core_request = f"READER STORY REQUEST: \"{prompt_clean}\""
    elif cat_clean:
        core_request = f"CATEGORY PRESET: {cat_clean}\nPlease compose a rich, original {cat_clean} short story."
    else:
        core_request = "READER STORY REQUEST: \"A captivating and atmospheric short story with an unexpected revelation.\""

    # Genre Specific Instruction
    genre_guidance = ""
    lookup_cat = cat_clean.lower()
    for key, guidance in CATEGORY_GUIDES.items():
        if key in lookup_cat or lookup_cat in key:
            genre_guidance = f"\nGENRE DIRECTIVE ({cat_clean}): {guidance}\n"
            break

    # Story Length Instruction
    if length_clean in LENGTH_SPECIFICATIONS:
        length_instruction = LENGTH_SPECIFICATIONS[length_clean]
    elif any(token in length_clean for token in ["word", "page", "short", "long", "quick", "epic"]):
        length_instruction = f"STORY LENGTH REQUIREMENT: The reader specifically requested length constraints: '{length}'. Calibrate the story length to precisely fulfill this expectation with a complete narrative arc."
    else:
        length_instruction = LENGTH_SPECIFICATIONS["default"]

    # Build User Message
    user_message_parts = [
        core_request,
        genre_guidance,
        length_instruction
    ]

    # Anti-repetition / Generate Another directives
    if is_another:
        anti_repeat = (
            "\nIMPORTANT DIVERSITY & RE-GENERATION DIRECTIVE:\n"
            "- The reader is requesting ANOTHER completely unique story based on this premise/category.\n"
            "- You MUST develop a brand-new plotline, fresh characters, a distinct setting, and an original conflict.\n"
            "- DO NOT reuse character names, plot mechanics, or settings from previous iterations."
        )
        if previous_titles:
            valid_titles = [f'"{t}"' for t in previous_titles if t and str(t).strip()]
            if valid_titles:
                anti_repeat += f"\n- Specifically avoid copying or closely echoing the storylines of: {', '.join(valid_titles)}."
        user_message_parts.append(anti_repeat)

    user_message_parts.append("\nWrite the complete, original story now. Return ONLY the specified JSON object.")

    final_user_message = "\n\n".join([p for p in user_message_parts if p.strip()])
    return SYSTEM_STORY_PROMPT, final_user_message
