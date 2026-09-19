/**
 * LORE — Frontend Application Logic
 * AI-First Story Generation Platform
 */

document.addEventListener("DOMContentLoaded", () => {
    // -----------------------------------------------------------------
    // DOM Elements: AI Story Generation
    // -----------------------------------------------------------------
    const storyQueryInput = document.getElementById("story-query-input");
    const btnClearQuery = document.getElementById("btn-clear-query");
    const btnSubmitSearch = document.getElementById("btn-submit-search");
    const btnFindAnother = document.getElementById("btn-find-another");
    const btnCopyStory = document.getElementById("btn-copy-story");
    const btnNewSearch = document.getElementById("btn-new-search");
    const btnErrorRetry = document.getElementById("btn-error-retry");
    const exampleChips = document.querySelectorAll(".example-chip");
    const moodCards = document.querySelectorAll(".mood-card");
    const lengthPills = document.querySelectorAll(".btn-length-pill");

    // Active Category Indicator
    const activeCatIndicator = document.getElementById("active-category-indicator");
    const activeCatName = document.getElementById("active-cat-name");
    const btnRemoveCat = document.getElementById("btn-remove-cat");

    // Sections
    const heroSection = document.getElementById("hero-section");
    const storySection = document.getElementById("story-section");
    const loadingStateSection = document.getElementById("loading-state-section");
    const errorStateSection = document.getElementById("error-state-section");
    const errorTitle = document.getElementById("error-title");
    const errorMessage = document.getElementById("error-message");
    const loadingStatusText = document.getElementById("loading-status-text");

    // Story Reader Elements
    const storyGenreTag = document.getElementById("story-genre-tag");
    const storyReadingTime = document.getElementById("story-reading-time");
    const storyTitleDisplay = document.getElementById("story-title-display");
    const storyTagsRow = document.getElementById("story-tags-row");
    const storySummaryBox = document.getElementById("story-summary-box");
    const storySummaryText = document.getElementById("story-summary-text");
    const storyTextDisplay = document.getElementById("story-text-display");
    const storyOriginTag = document.getElementById("story-origin-tag");
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

    // Application State
    let currentStory = null;
    let lastUserPrompt = "";
    let lastCategory = "";
    let selectedCategory = "";
    let selectedLength = "default";
    let generatedTitles = [];

    // Initialize System Status
    fetchEngineStatus();

    // -----------------------------------------------------------------
    // Category Preset Selection
    // -----------------------------------------------------------------
    moodCards.forEach((card) => {
        card.addEventListener("click", () => {
            const category = card.getAttribute("data-category");
            if (selectedCategory === category) {
                // Deselect
                clearSelectedCategory();
            } else {
                setSelectedCategory(category);
            }
        });
    });

    if (btnRemoveCat) {
        btnRemoveCat.addEventListener("click", () => {
            clearSelectedCategory();
        });
    }

    function setSelectedCategory(category) {
        selectedCategory = category;
        moodCards.forEach((c) => {
            if (c.getAttribute("data-category") === category) {
                c.classList.add("active");
            } else {
                c.classList.remove("active");
            }
        });

        if (activeCatIndicator && activeCatName) {
            activeCatName.textContent = category;
            activeCatIndicator.style.display = "inline-flex";
        }
    }

    function clearSelectedCategory() {
        selectedCategory = "";
        moodCards.forEach((c) => c.classList.remove("active"));
        if (activeCatIndicator) {
            activeCatIndicator.style.display = "none";
        }
    }

    // -----------------------------------------------------------------
    // Story Length Selection
    // -----------------------------------------------------------------
    lengthPills.forEach((pill) => {
        pill.addEventListener("click", () => {
            lengthPills.forEach((p) => {
                p.classList.remove("active");
                p.setAttribute("aria-checked", "false");
            });
            pill.classList.add("active");
            pill.setAttribute("aria-checked", "true");
            selectedLength = pill.getAttribute("data-length") || "default";
        });
    });

    // -----------------------------------------------------------------
    // Textarea & Shortcuts
    // -----------------------------------------------------------------
    storyQueryInput.addEventListener("input", () => {
        btnClearQuery.style.display = storyQueryInput.value.trim() ? "block" : "none";
    });

    btnClearQuery.addEventListener("click", () => {
        storyQueryInput.value = "";
        btnClearQuery.style.display = "none";
        storyQueryInput.focus();
    });

    storyQueryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            handleGenerateStory(false);
        }
    });

    btnSubmitSearch.addEventListener("click", () => handleGenerateStory(false));

    // "Generate Another Story" (preserves active prompt, category, and length)
    btnFindAnother.addEventListener("click", () => handleGenerateStory(true));

    // Example Prompt Chips
    exampleChips.forEach((chip) => {
        chip.addEventListener("click", () => {
            const promptText = chip.getAttribute("data-prompt") || "";
            const cat = chip.getAttribute("data-category") || "";
            storyQueryInput.value = promptText;
            btnClearQuery.style.display = "block";
            if (cat) {
                setSelectedCategory(cat);
            }
            handleGenerateStory(false);
        });
    });

    // -----------------------------------------------------------------
    // Core Story Generation Dispatcher
    // -----------------------------------------------------------------
    async function handleGenerateStory(isAnother = false) {
        let prompt = storyQueryInput.value.trim();
        let category = selectedCategory;

        if (isAnother) {
            if (!prompt && lastUserPrompt) {
                prompt = lastUserPrompt;
                storyQueryInput.value = lastUserPrompt;
            }
            if (!category && lastCategory) {
                category = lastCategory;
                setSelectedCategory(lastCategory);
            }
        }

        if (!prompt && !category) {
            showToast("Please describe the story or choose a genre preset.", "error");
            storyQueryInput.focus();
            return;
        }

        lastUserPrompt = prompt;
        lastCategory = category;

        // Stop any active narration
        if (window.LoreSpeech) {
            window.LoreSpeech.stop();
        }

        showLoadingState(true, isAnother);

        try {
            const response = await fetch("/api/generate-story", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt: prompt,
                    category: category,
                    length: selectedLength,
                    is_another: isAnother,
                    previous_titles: generatedTitles.slice(-5)
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success || !data.story) {
                const errorMsg = (data && data.error) ? data.error : "LORE couldn't create the story right now. Please try again.";
                const err = new Error(errorMsg);
                err.code = (data && data.code) ? data.code : "GENERATION_ERROR";
                throw err;
            }

            currentStory = data.story;
            if (currentStory.title) {
                generatedTitles.push(currentStory.title);
            }

            renderGeneratedStory(currentStory);
            showLoadingState(false);

            // Smooth scroll to story reader card
            requestAnimationFrame(() => {
                if (storySection) {
                    storySection.scrollIntoView({ behavior: "smooth", block: "start" });
                }
            });

            showToast(isAnother ? "Here is another original story!" : "Original story written successfully!", "success");

        } catch (err) {
            console.error("[LORE Generation Error]", err);
            showLoadingState(false);
            showErrorState(err.message || "LORE couldn't create the story right now. Please try again.", err.code);
        }
    }

    function renderGeneratedStory(story) {
        if (!storySection) return;

        errorStateSection.style.display = "none";
        storySection.style.display = "block";

        storyOriginTag.textContent = "Original Story • Generated for you";
        storyGenreTag.textContent = (story.genre || selectedCategory || "STORY").toUpperCase();

        const words = story.word_count || (story.content ? story.content.split(/\s+/).length : 500);
        const readTime = story.reading_time_min || Math.max(1, Math.round(words / 200));
        storyReadingTime.textContent = `${readTime} min read (${words.toLocaleString()} words)`;
        storyTitleDisplay.textContent = story.title || "An Untitled Tale";

        // Summary
        if (story.summary && story.summary.trim()) {
            storySummaryText.textContent = story.summary.trim();
            storySummaryBox.style.display = "block";
        } else {
            storySummaryBox.style.display = "none";
        }

        // Tags
        if (story.tags && Array.isArray(story.tags) && story.tags.length > 0) {
            storyTagsRow.innerHTML = "";
            story.tags.slice(0, 5).forEach((tag, idx) => {
                const chip = document.createElement("span");
                chip.className = `story-chip ${idx === 0 ? "tag-theme" : idx === 1 ? "tag-setting" : "tag-mood"}`;
                chip.textContent = tag;
                storyTagsRow.appendChild(chip);
            });
            storyTagsRow.style.display = "flex";
        } else {
            storyTagsRow.style.display = "none";
        }

        // Render Paragraphs
        renderStoryParagraphs(story.content || story.story_text || "");

        // Initialize voice narration engine with the newly generated story
        if (window.LoreSpeech) {
            window.LoreSpeech.loadStory(story.title, story.content || story.story_text || "");
        }
    }

    function renderStoryParagraphs(text) {
        storyTextDisplay.innerHTML = "";
        const fragment = document.createDocumentFragment();
        const rawParagraphs = (text || "").split(/\n\s*\n/).filter(p => p.trim().length > 0);

        if (rawParagraphs.length === 0) {
            const p = document.createElement("p");
            p.className = "story-paragraph";
            p.textContent = text || "";
            fragment.appendChild(p);
        } else {
            rawParagraphs.forEach((paraText, idx) => {
                const p = document.createElement("p");
                p.className = "story-paragraph";
                p.id = `story-p-${idx}`;
                p.textContent = paraText.trim();
                fragment.appendChild(p);
            });
        }
        storyTextDisplay.appendChild(fragment);
    }

    function showLoadingState(isLoading, isAnother = false) {
        if (isLoading) {
            btnSubmitSearch.classList.add("loading");
            btnSubmitSearch.disabled = true;
            btnFindAnother.disabled = true;

            if (storySection) storySection.style.display = "none";
            if (errorStateSection) errorStateSection.style.display = "none";

            if (loadingStatusText) {
                loadingStatusText.textContent = isAnother ? "LORE is crafting another original story..." : "LORE is writing your story...";
            }
            loadingStateSection.style.display = "block";
            loadingStateSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
        } else {
            btnSubmitSearch.classList.remove("loading");
            btnSubmitSearch.disabled = false;
            btnFindAnother.disabled = false;
            loadingStateSection.style.display = "none";
        }
    }

    function showErrorState(msg, code) {
        if (storySection) storySection.style.display = "none";
        loadingStateSection.style.display = "none";
        errorStateSection.style.display = "block";

        if (code === "NO_API_KEY") {
            errorTitle.textContent = "AI API Key Required";
            errorMessage.textContent = "Story generation requires an active AI provider key. Please configure OPENAI_API_KEY (or STORY_AI_API_KEY) in your environment or .env file.";
        } else if (code === "INVALID_API_KEY") {
            errorTitle.textContent = "Invalid AI API Key";
            errorMessage.textContent = "The configured OPENAI_API_KEY was rejected by OpenAI. Please check your key in your .env file or environment.";
        } else {
            errorTitle.textContent = "Story generation is temporarily unavailable.";
            errorMessage.textContent = msg || "Please verify your AI credentials or try another request.";
        }
        errorStateSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    // -----------------------------------------------------------------
    // Copy Functionality
    // -----------------------------------------------------------------
    async function copyToClipboard(textToCopy) {
        let success = false;
        if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
            try {
                await navigator.clipboard.writeText(textToCopy);
                success = true;
            } catch (err) {
                console.warn("[LORE Copy] clipboard API failed, using fallback:", err);
            }
        }

        if (!success) {
            try {
                const tempTextarea = document.createElement("textarea");
                tempTextarea.value = textToCopy;
                tempTextarea.setAttribute("readonly", "");
                tempTextarea.style.position = "fixed";
                tempTextarea.style.top = "0";
                tempTextarea.style.left = "-9999px";
                tempTextarea.style.fontSize = "16px";
                document.body.appendChild(tempTextarea);
                tempTextarea.focus();
                tempTextarea.select();
                tempTextarea.setSelectionRange(0, textToCopy.length);
                success = document.execCommand("copy");
                document.body.removeChild(tempTextarea);
            } catch (err) {
                console.error("[LORE Copy Fallback Error]", err);
                success = false;
            }
        }
        return success;
    }

    btnCopyStory.addEventListener("click", async () => {
        if (!currentStory) return;
        const textToCopy = `${currentStory.title}\nGenre: ${currentStory.genre || ''}\n\n${currentStory.content || currentStory.story_text}`.trim();
        const originalHtml = btnCopyStory.innerHTML;
        const copied = await copyToClipboard(textToCopy);

        if (copied) {
            btnCopyStory.classList.add("copied");
            btnCopyStory.innerHTML = `
                <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span>✓ Copied</span>
            `;
            showToast("Story copied to clipboard!", "success");

            setTimeout(() => {
                btnCopyStory.classList.remove("copied");
                btnCopyStory.innerHTML = originalHtml;
            }, 2200);
        } else {
            showToast("Unable to copy automatically. Please select text.", "error");
        }
    });

    // "New Request" Action
    btnNewSearch.addEventListener("click", () => {
        if (heroSection) {
            heroSection.scrollIntoView({ behavior: "smooth", block: "start" });
        } else {
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
        storyQueryInput.focus();
    });

    btnErrorRetry.addEventListener("click", () => {
        errorStateSection.style.display = "none";
        if (heroSection) {
            heroSection.scrollIntoView({ behavior: "smooth", block: "start" });
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

    async function fetchEngineStatus() {
        try {
            const res = await fetch("/api/info");
            const data = await res.json();
            if (data.status === "success") {
                const prov = data.ai_provider || "AI Engine";
                dbStatusPill.textContent = `${prov} Ready`;
            } else {
                dbStatusPill.textContent = "AI Story Engine Ready";
            }
        } catch (err) {
            dbStatusPill.textContent = "LORE Engine Ready";
        }
    }

    function showToast(message, type = "info") {
        if (!toast) return;
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.style.display = "block";

        setTimeout(() => {
            toast.style.display = "none";
        }, 3400);
    }
});
