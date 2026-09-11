/**
 * LORE — Frontend Application Logic
 * Implements intelligent story recommendation, randomized relevance-pool sampling,
 * duplicate prevention across sessions, smooth Story Section scrolling, and explainability rendering.
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const storyQueryInput = document.getElementById("story-query-input");
    const btnClearQuery = document.getElementById("btn-clear-query");
    const btnSubmitSearch = document.getElementById("btn-submit-search");
    const btnFindAnother = document.getElementById("btn-find-another");
    const btnCopyStory = document.getElementById("btn-copy-story");
    const btnNewSearch = document.getElementById("btn-new-search");
    const btnErrorRetry = document.getElementById("btn-error-retry");

    // Category / Mood Elements
    const moodCards = document.querySelectorAll(".mood-card");
    const exampleChips = document.querySelectorAll(".example-chip");
    const activeCategoryIndicator = document.getElementById("active-category-indicator");
    const activeCatName = document.getElementById("active-cat-name");
    const btnRemoveCat = document.getElementById("btn-remove-cat");

    // Sections
    const storySection = document.getElementById("story-section") || document.getElementById("story-result-section");
    const emptyStateSection = document.getElementById("empty-state-section");
    const loadingStateSection = document.getElementById("loading-state-section");
    const errorStateSection = document.getElementById("error-state-section");
    const errorTitle = document.getElementById("error-title");
    const errorMessage = document.getElementById("error-message");

    // Story Reader Display Elements
    const storyGenreTag = document.getElementById("story-genre-tag");
    const storyReadingTime = document.getElementById("story-reading-time");
    const storyTitleDisplay = document.getElementById("story-title-display");
    const storyThemeTag = document.getElementById("story-theme-tag");
    const storySettingTag = document.getElementById("story-setting-tag");
    const storyMoodTag = document.getElementById("story-mood-tag");
    const storyTextDisplay = document.getElementById("story-text-display");
    const storyRelevanceScore = document.getElementById("story-relevance-score");
    const storyReasonsContainer = document.getElementById("story-reasons-container");
    const dbStatusPill = document.getElementById("db-status-pill");
    const toast = document.getElementById("toast");

    // Font Sizing Controls
    const btnDecreaseFont = document.getElementById("btn-decrease-font");
    const btnIncreaseFont = document.getElementById("btn-increase-font");
    let currentFontSizeRem = 1.18;

    // About Modal
    const btnAbout = document.getElementById("btn-about");
    const aboutModal = document.getElementById("about-modal");
    const btnCloseAbout = document.getElementById("btn-close-about");

    // State Variables for Recommendation & Duplicate Prevention
    let selectedCategory = "";
    let currentStory = null;
    let shownStoryIds = [];
    let lastQuery = "";
    let lastSelectedCategory = "";

    // Initialize System Status
    fetchDatabaseStatus();

    // -----------------------------------------------------------------
    // Event Listeners
    // -----------------------------------------------------------------

    // Query Textarea Input Handlers
    storyQueryInput.addEventListener("input", () => {
        btnClearQuery.style.display = storyQueryInput.value.trim() ? "block" : "none";
    });

    // Clear Query Button
    btnClearQuery.addEventListener("click", () => {
        storyQueryInput.value = "";
        btnClearQuery.style.display = "none";
        storyQueryInput.focus();
    });

    // Enter Key Search Trigger
    storyQueryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleFindStory(false);
        }
    });

    // Main "Generate Story" Button
    btnSubmitSearch.addEventListener("click", () => handleFindStory(false));

    // "Find Another Story" Button (Preserves original request, excludes already shown story IDs)
    btnFindAnother.addEventListener("click", () => handleFindStory(true));

    // Example Prompt Chips
    exampleChips.forEach((chip) => {
        chip.addEventListener("click", () => {
            const promptText = chip.getAttribute("data-prompt") || "";
            storyQueryInput.value = promptText;
            btnClearQuery.style.display = "block";
            // New prompt implies fresh recommendation
            shownStoryIds = [];
            handleFindStory(false);
        });
    });

    // Mood / Category Card Selection
    moodCards.forEach((card) => {
        card.addEventListener("click", () => {
            const category = card.getAttribute("data-category");

            if (selectedCategory === category) {
                // Deselect if already selected
                clearCategorySelection();
            } else {
                // Select category
                selectedCategory = category;
                moodCards.forEach((c) => c.classList.remove("active"));
                card.classList.add("active");

                // Update search card indicator
                activeCatName.textContent = category;
                activeCategoryIndicator.style.display = "inline-flex";

                // New category selection resets shown history
                shownStoryIds = [];
                handleFindStory(false);
            }
        });
    });

    // Remove Category Badge
    btnRemoveCat.addEventListener("click", (e) => {
        e.stopPropagation();
        clearCategorySelection();
    });

    // "Copy Story" Action
    btnCopyStory.addEventListener("click", async () => {
        if (!currentStory) return;
        const textToCopy = `${currentStory.title}\nCategory: ${currentStory.category}\nTheme: ${currentStory.theme}\nSetting: ${currentStory.setting}\nMood: ${currentStory.mood}\n\n${currentStory.story_text}`;
        try {
            await navigator.clipboard.writeText(textToCopy);
            showToast("Story copied to clipboard!", "success");
        } catch (err) {
            showToast("Failed to copy text", "error");
        }
    });

    // "New Search" Action
    btnNewSearch.addEventListener("click", () => {
        const searchSection = document.getElementById("search-section");
        if (searchSection) {
            searchSection.scrollIntoView({ behavior: "smooth", block: "start" });
        } else {
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
        storyQueryInput.focus();
    });

    // Retry Button on Error
    btnErrorRetry.addEventListener("click", () => {
        errorStateSection.style.display = "none";
        emptyStateSection.style.display = "block";
        const searchSection = document.getElementById("search-section");
        if (searchSection) {
            searchSection.scrollIntoView({ behavior: "smooth", block: "start" });
        }
        storyQueryInput.focus();
    });

    // Font Sizing Adjustments
    btnIncreaseFont.addEventListener("click", () => {
        if (currentFontSizeRem < 1.45) {
            currentFontSizeRem += 0.08;
            storyTextDisplay.style.fontSize = `${currentFontSizeRem}rem`;
        }
    });

    btnDecreaseFont.addEventListener("click", () => {
        if (currentFontSizeRem > 0.95) {
            currentFontSizeRem -= 0.08;
            storyTextDisplay.style.fontSize = `${currentFontSizeRem}rem`;
        }
    });

    // About Modal Controls
    btnAbout.addEventListener("click", () => {
        aboutModal.style.display = "flex";
    });

    btnCloseAbout.addEventListener("click", () => {
        aboutModal.style.display = "none";
    });

    window.addEventListener("click", (e) => {
        if (e.target === aboutModal) {
            aboutModal.style.display = "none";
        }
    });

    // -----------------------------------------------------------------
    // Core Recommendation & Navigation Logic
    // -----------------------------------------------------------------

    async function fetchDatabaseStatus() {
        try {
            const res = await fetch("/api/info");
            const data = await res.json();
            if (data.status === "success" && data.model_loaded && data.total_stories) {
                dbStatusPill.textContent = `${Number(data.total_stories).toLocaleString()} Stories Indexed`;
            } else {
                dbStatusPill.textContent = "Ready to Explore";
            }
        } catch (err) {
            dbStatusPill.textContent = "Ready";
        }
    }

    async function handleFindStory(isFindingAnother = false) {
        let query = storyQueryInput.value.trim();

        // If clicking 'Find Another Story', ensure we preserve the original query even if input was touched
        if (isFindingAnother && !query && lastQuery) {
            query = lastQuery;
            storyQueryInput.value = lastQuery;
        }

        if (!query && !selectedCategory) {
            showToast("Please enter what you'd like to read or select a mood.", "error");
            storyQueryInput.focus();
            return;
        }

        // Check if this is a brand new query/intent or a continuation
        const isSameQuery = (query === lastQuery && selectedCategory === lastSelectedCategory);

        if (!isFindingAnother) {
            if (!isSameQuery) {
                // User changed their query or category -> Reset duplicate exclusion history
                shownStoryIds = [];
            }
        }

        // Save current query state
        lastQuery = query;
        lastSelectedCategory = selectedCategory;

        // Stop any active narration when requesting another story or generating new query
        if (window.LoreSpeech) {
            window.LoreSpeech.stop();
        }

        // Show Loading State
        showLoadingState(true);

        try {
            const res = await fetch("/api/recommend", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: query,
                    category: selectedCategory || null,
                    exclude_ids: shownStoryIds
                })
            });

            const data = await res.json();

            if (!res.ok || data.status !== "success" || !data.story) {
                throw new Error(data.message || "We couldn't find a close match for your request.");
            }

            currentStory = data.story;

            // Track shown story ID to avoid immediate repetition
            if (currentStory.id && !shownStoryIds.includes(currentStory.id)) {
                shownStoryIds.push(currentStory.id);
            }

            // Render the story into the DOM
            renderStoryResult(data);

            // Hide loader and activate Story Section
            showLoadingState(false);

            // AUTOMATIC SMOOTH SCROLL DIRECTLY TO STORY SECTION
            // Must happen strictly AFTER story content is rendered in DOM
            requestAnimationFrame(() => {
                const targetSection = document.getElementById("story-section") || document.getElementById("story-result-section");
                if (targetSection) {
                    targetSection.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });
                }
            });

            showToast(isFindingAnother ? "Here is another story for you!" : "Story retrieved successfully!", "success");
        } catch (error) {
            console.error(error);
            showLoadingState(false);
            showErrorState(error.message);
        }
    }

    function renderStoryResult(data) {
        const story = data.story;
        const reasons = data.why_this_story || [];

        // Hide empty & error states, display reader
        emptyStateSection.style.display = "none";
        errorStateSection.style.display = "none";
        
        const targetSection = document.getElementById("story-section") || document.getElementById("story-result-section");
        if (targetSection) {
            targetSection.style.display = "block";
        }

        // Update Metadata
        storyGenreTag.textContent = (story.category || "STORY").toUpperCase();
        storyReadingTime.textContent = `${story.reading_time_min || 2} min read (${story.word_count || 200} words)`;
        storyTitleDisplay.textContent = story.title;

        storyThemeTag.textContent = story.theme || "General";
        storySettingTag.textContent = story.setting || "Unspecified";
        storyMoodTag.textContent = story.mood || "Atmospheric";

        // Story Body Text (Rendered as structured paragraphs for reading & narration chunking)
        renderStoryParagraphs(story.story_text);

        // Initialize voice narration engine with the retrieved story
        if (window.LoreSpeech) {
            window.LoreSpeech.loadStory(story.title, story.story_text);
        }

        // Match Score & Explainability Tags
        storyRelevanceScore.textContent = `${data.relevance_percentage || 92}% Match`;
        storyReasonsContainer.innerHTML = "";

        reasons.forEach((r) => {
            const tag = document.createElement("div");
            tag.className = "reason-tag";
            tag.innerHTML = `
                <span class="reason-title">&#10003; ${escapeHtml(r.label)}</span>
                <span class="reason-note">${escapeHtml(r.detail)}</span>
            `;
            storyReasonsContainer.appendChild(tag);
        });
    }

    function renderStoryParagraphs(text) {
        storyTextDisplay.innerHTML = "";
        const rawParagraphs = (text || "").split(/\n+/).filter(p => p.trim().length > 0);

        if (rawParagraphs.length <= 1 && (text || "").length > 250) {
            // Split into cohesive readable sentence groups
            const sentences = text.match(/[^.!?]+[.!?]+(\s+|$)/g) || [text];
            const chunks = [];
            let currentChunk = "";
            sentences.forEach(s => {
                if ((currentChunk + s).length > 220 && currentChunk.length > 0) {
                    chunks.push(currentChunk.trim());
                    currentChunk = s;
                } else {
                    currentChunk += s;
                }
            });
            if (currentChunk.trim().length > 0) {
                chunks.push(currentChunk.trim());
            }

            chunks.forEach((chunkText, idx) => {
                const p = document.createElement("p");
                p.className = "story-paragraph";
                p.id = `story-p-${idx}`;
                p.textContent = chunkText;
                storyTextDisplay.appendChild(p);
            });
        } else {
            rawParagraphs.forEach((paraText, idx) => {
                const p = document.createElement("p");
                p.className = "story-paragraph";
                p.id = `story-p-${idx}`;
                p.textContent = paraText;
                storyTextDisplay.appendChild(p);
            });
        }
    }

    function showLoadingState(isLoading) {
        const targetSection = document.getElementById("story-section") || document.getElementById("story-result-section");

        if (isLoading) {
            btnSubmitSearch.classList.add("loading");
            btnSubmitSearch.disabled = true;
            btnFindAnother.disabled = true;

            emptyStateSection.style.display = "none";
            errorStateSection.style.display = "none";
            if (targetSection) {
                targetSection.style.display = "none";
            }
            loadingStateSection.style.display = "block";

            // Scroll gently to loading placeholder if off-screen
            loadingStateSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
        } else {
            btnSubmitSearch.classList.remove("loading");
            btnSubmitSearch.disabled = false;
            btnFindAnother.disabled = false;
            loadingStateSection.style.display = "none";
        }
    }

    function showErrorState(msg) {
        emptyStateSection.style.display = "none";
        const targetSection = document.getElementById("story-section") || document.getElementById("story-result-section");
        if (targetSection) {
            targetSection.style.display = "none";
        }
        loadingStateSection.style.display = "none";
        errorStateSection.style.display = "block";

        errorTitle.textContent = "We couldn't find a close match.";
        errorMessage.textContent = msg || "Try describing your story in a different way or explore one of the mood categories.";
        errorStateSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function clearCategorySelection() {
        selectedCategory = "";
        lastSelectedCategory = "";
        shownStoryIds = [];
        moodCards.forEach((c) => c.classList.remove("active"));
        activeCategoryIndicator.style.display = "none";
    }

    function showToast(message, type = "info") {
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.style.display = "block";

        setTimeout(() => {
            toast.style.display = "none";
        }, 3400);
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }
});
