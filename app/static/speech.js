/**
 * LORE — Natural Audiobook-Style Voice Narration Controller
 * 
 * Features:
 * - Intelligent voice ranking & prioritization (Neural, Natural, Premium, Siri, Google, Microsoft)
 * - Clean human-friendly voice labels (e.g. "Jenny (Natural) — English (US) ✦")
 * - 8-Level precise playback speed control (0.25× to 2.0×) with 1:1 rate mapping
 * - Dynamic mid-playback voice & speed switching (resumes current position without restarting)
 * - Intelligent sentence & clause-level chunking with abbreviation protection & prosodic pauses
 * - 10s Backward (↶ 10s) and Forward (10s ↷) chunk seeking
 * - Interactive timeline scrub bar with live progress tracking
 * - Paragraph synchronization & visual reading indicator (.story-paragraph.active-reading)
 * - Floating sticky bottom mini audiobook player
 * - Accessible keyboard shortcuts (←, →, Space)
 * - Clean isolation when loading new stories or using "Find Another Story"
 */

class LoreSpeechController {
    constructor() {
        this.synth = window.speechSynthesis || null;
        this.isSupported = !!this.synth && 'SpeechSynthesisUtterance' in window;

        // Playback States
        this.STATE_IDLE = 'IDLE';
        this.STATE_PLAYING = 'PLAYING';
        this.STATE_PAUSED = 'PAUSED';
        this.STATE_FINISHED = 'FINISHED';
        this.state = this.STATE_IDLE;

        // Story Data & Chunks
        this.currentTitle = '';
        this.currentText = '';
        this.chunks = []; // Array of { text, paragraphIndex, chunkIndex, isParagraphEnd }
        this.currentChunkIndex = 0;

        // Voice & Playback Configuration
        this.voices = [];
        this.selectedVoice = null;
        this.playbackRate = 1.0;
        this.playbackPitch = 1.0;
        this.currentUtterance = null;
        this.isHandlingChunkEnd = false;

        // DOM Elements Cache
        this.dom = {};
    }

    init() {
        this.cacheDom();

        if (!this.isSupported) {
            console.warn('[LORE TTS] Web Speech API is not supported in this browser.');
            if (this.dom.toolbar) {
                this.dom.toolbar.innerHTML = `
                    <div class="speech-unsupported-notice">
                        <span>ℹ Voice narration is not supported in this browser.</span>
                    </div>
                `;
            }
            return;
        }

        this.bindEvents();
        this.loadVoices();

        // Listen for async voice loading in browsers (Chrome, Edge, Safari, Firefox)
        if (this.synth.onvoiceschanged !== undefined) {
            this.synth.onvoiceschanged = () => this.loadVoices();
        }

        // Additional fallback retry for browsers with delayed voice population
        setTimeout(() => this.loadVoices(), 250);
        setTimeout(() => this.loadVoices(), 1000);
    }

    cacheDom() {
        this.dom = {
            toolbar: document.getElementById('narration-toolbar'),
            btnListen: document.getElementById('btn-listen-story'),
            btnListenIcon: document.getElementById('btn-listen-icon'),
            btnListenText: document.getElementById('btn-listen-text'),
            waveAnim: document.getElementById('audio-wave-anim'),
            btnStop: document.getElementById('btn-audio-stop'),
            btnBack: document.getElementById('btn-audio-back'),
            btnForward: document.getElementById('btn-audio-forward'),

            // Toolbar Progress
            progressWrapper: document.getElementById('narration-progress-wrapper'),
            progressBar: document.getElementById('narration-progress-bar'),
            progressFill: document.getElementById('narration-progress-fill'),
            progressDot: document.getElementById('narration-progress-dot'),
            progressCurPos: document.getElementById('progress-current-pos'),
            progressTotalParts: document.getElementById('progress-total-parts'),

            // Settings
            voiceSelect: document.getElementById('voice-select'),
            speedButtons: document.querySelectorAll('.btn-speed-opt'),
            storyBody: document.getElementById('story-text-display'),

            // Mini Audiobook Player
            miniPlayer: document.getElementById('mini-audio-player'),
            miniTitle: document.getElementById('mini-audio-title'),
            miniSpeed: document.getElementById('mini-audio-speed'),
            miniPlayPauseBtn: document.getElementById('btn-mini-play-pause'),
            miniPlayIcon: document.getElementById('mini-play-icon'),
            miniBackBtn: document.getElementById('btn-mini-back'),
            miniForwardBtn: document.getElementById('btn-mini-forward'),
            miniStopBtn: document.getElementById('btn-mini-stop'),
            miniTrack: document.getElementById('mini-progress-track'),
            miniFill: document.getElementById('mini-progress-fill'),
            miniThumb: document.getElementById('mini-progress-thumb')
        };
    }

    bindEvents() {
        // Main Listen / Pause / Resume Button
        if (this.dom.btnListen) {
            this.dom.btnListen.addEventListener('click', () => {
                if (this.state === this.STATE_PLAYING) {
                    this.pause();
                } else if (this.state === this.STATE_PAUSED) {
                    this.resume();
                } else {
                    this.play();
                }
            });
        }

        // Backward 10s (Toolbar)
        if (this.dom.btnBack) {
            this.dom.btnBack.addEventListener('click', () => this.stepBackward());
        }

        // Forward 10s (Toolbar)
        if (this.dom.btnForward) {
            this.dom.btnForward.addEventListener('click', () => this.stepForward());
        }

        // Stop Button (Toolbar)
        if (this.dom.btnStop) {
            this.dom.btnStop.addEventListener('click', () => this.stop());
        }

        // Voice Selector Dropdown
        if (this.dom.voiceSelect) {
            this.dom.voiceSelect.addEventListener('change', (e) => {
                this.setVoice(e.target.value);
            });
        }

        // 8-Level Speed Option Buttons (0.25x to 2.0x)
        if (this.dom.speedButtons) {
            this.dom.speedButtons.forEach((btn) => {
                btn.addEventListener('click', () => {
                    const speed = parseFloat(btn.getAttribute('data-speed') || '1.0');
                    this.setSpeed(speed);
                });
            });
        }

        // Mini Player Controls
        if (this.dom.miniPlayPauseBtn) {
            this.dom.miniPlayPauseBtn.addEventListener('click', () => {
                if (this.state === this.STATE_PLAYING) {
                    this.pause();
                } else if (this.state === this.STATE_PAUSED) {
                    this.resume();
                } else {
                    this.play();
                }
            });
        }

        if (this.dom.miniBackBtn) {
            this.dom.miniBackBtn.addEventListener('click', () => this.stepBackward());
        }

        if (this.dom.miniForwardBtn) {
            this.dom.miniForwardBtn.addEventListener('click', () => this.stepForward());
        }

        if (this.dom.miniStopBtn) {
            this.dom.miniStopBtn.addEventListener('click', () => this.stop());
        }

        // Interactive Progress Scrubbing (Click to seek chunk)
        if (this.dom.progressBar) {
            this.dom.progressBar.addEventListener('click', (e) => this.handleTrackClick(e, this.dom.progressBar));
        }

        if (this.dom.miniTrack) {
            this.dom.miniTrack.addEventListener('click', (e) => this.handleTrackClick(e, this.dom.miniTrack));
        }

        // Keyboard Navigation Shortcuts (Left, Right, Space)
        window.addEventListener('keydown', (e) => this.handleKeyboardNav(e));
    }

    handleKeyboardNav(e) {
        // Do not intercept if user is typing in textarea, input, or select
        const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
        if (activeTag === 'input' || activeTag === 'textarea' || activeTag === 'select') {
            return;
        }

        // Left Arrow: Backward 10s
        if (e.key === 'ArrowLeft' && (this.state === this.STATE_PLAYING || this.state === this.STATE_PAUSED)) {
            e.preventDefault();
            this.stepBackward();
        }
        // Right Arrow: Forward 10s
        else if (e.key === 'ArrowRight' && (this.state === this.STATE_PLAYING || this.state === this.STATE_PAUSED)) {
            e.preventDefault();
            this.stepForward();
        }
        // Spacebar: Play / Pause toggle
        else if (e.key === ' ' && (this.state === this.STATE_PLAYING || this.state === this.STATE_PAUSED)) {
            e.preventDefault();
            if (this.state === this.STATE_PLAYING) {
                this.pause();
            } else {
                this.resume();
            }
        }
    }

    handleTrackClick(e, element) {
        if (this.chunks.length === 0) return;
        const rect = element.getBoundingClientRect();
        const clickRatio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        const targetChunkIndex = Math.min(this.chunks.length - 1, Math.floor(clickRatio * this.chunks.length));

        this.jumpToChunk(targetChunkIndex);
    }

    /**
     * Scores and ranks browser voices to prioritize natural, human-like neural storytellers.
     */
    scoreVoice(voice) {
        let score = 0;
        const name = (voice.name || '').toLowerCase();
        const lang = (voice.lang || '').toLowerCase();
        const uri = (voice.voiceURI || '').toLowerCase();
        const combined = `${name} ${lang} ${uri}`;

        // 1. Language Priority (English first)
        if (lang.startsWith('en')) {
            score += 120;
            if (lang.includes('us')) score += 25;
            else if (lang.includes('gb') || lang.includes('uk')) score += 20;
            else if (lang.includes('au') || lang.includes('ca')) score += 15;
            else if (lang.includes('ie') || lang.includes('in')) score += 10;
        } else {
            return -200; // Deprioritize non-English
        }

        // 2. High-Fidelity Neural / Natural Terminology
        if (combined.includes('natural')) score += 120;
        if (combined.includes('neural')) score += 120;
        if (combined.includes('online') && (combined.includes('microsoft') || combined.includes('edge'))) score += 90;
        if (combined.includes('premium')) score += 80;
        if (combined.includes('enhanced')) score += 70;
        if (combined.includes('siri')) score += 70;
        if (combined.includes('google')) score += 50;

        // 3. Known Premium Storyteller Voice Personas
        // Microsoft Natural / Neural Personas
        if (combined.includes('jenny')) score += 55;
        if (combined.includes('aria')) score += 55;
        if (combined.includes('ava')) score += 55;
        if (combined.includes('guy')) score += 50;
        if (combined.includes('steffan')) score += 50;
        if (combined.includes('ryan')) score += 50;
        if (combined.includes('sonia')) score += 45;
        if (combined.includes('andrew')) score += 45;
        if (combined.includes('brian')) score += 45;
        if (combined.includes('emma')) score += 45;

        // Apple / Siri Natural Personas
        if (combined.includes('samantha')) score += 50;
        if (combined.includes('daniel')) score += 50;
        if (combined.includes('karen')) score += 45;
        if (combined.includes('oliver')) score += 45;
        if (combined.includes('serena')) score += 45;

        // Standard Desktop Fallbacks
        if (combined.includes('zira')) score += 25;
        if (combined.includes('david')) score += 25;
        if (combined.includes('mark')) score += 25;
        if (combined.includes('hazel')) score += 25;
        if (combined.includes('catherine')) score += 25;
        if (combined.includes('george')) score += 25;
        if (combined.includes('susan')) score += 25;

        if (voice.default) score += 10;
        if (!voice.localService) score += 15; // Remote neural voices are typically higher quality

        return score;
    }

    /**
     * Formats technical voice strings into elegant human-readable labels.
     */
    formatVoiceLabel(voice) {
        const rawName = voice.name || 'Voice';
        const lang = (voice.lang || 'en-US').toLowerCase();
        const combined = `${rawName} ${voice.voiceURI || ''}`.toLowerCase();

        // Clean out technical clutter
        let cleanName = rawName
            .replace(/Microsoft\s+/gi, '')
            .replace(/Google\s+/gi, 'Google ')
            .replace(/Apple\s+/gi, '')
            .replace(/Desktop/gi, '')
            .replace(/\(Natural\)/gi, '')
            .replace(/\(Neural\)/gi, '')
            .replace(/Online/gi, '')
            .replace(/-\s*English.*$/gi, '')
            .replace(/\s+/g, ' ')
            .trim();

        // Format region
        let region = 'English';
        if (lang.includes('us')) region = 'English (US)';
        else if (lang.includes('gb') || lang.includes('uk')) region = 'English (UK)';
        else if (lang.includes('au')) region = 'English (AU)';
        else if (lang.includes('ca')) region = 'English (CA)';
        else if (lang.includes('in')) region = 'English (IN)';
        else if (lang.includes('ie')) region = 'English (IE)';

        const isNatural = /natural|neural|online|premium|enhanced/i.test(combined);
        const badge = isNatural ? ' ✦ Natural' : '';

        return `${cleanName} — ${region}${badge}`;
    }

    loadVoices() {
        if (!this.synth) return;
        const rawVoices = this.synth.getVoices();
        if (!rawVoices || rawVoices.length === 0) return;

        // Score and sort voices in descending order of naturalness
        const scoredVoices = rawVoices.map(v => ({ voice: v, score: this.scoreVoice(v) }));
        scoredVoices.sort((a, b) => b.score - a.score);

        // Filter English voices first, fallback to all if none
        const englishList = scoredVoices.filter(item => item.score > 0).map(item => item.voice);
        this.voices = englishList.length > 0 ? englishList : rawVoices;

        if (!this.dom.voiceSelect) return;

        // Remember current selection if any
        const currentSelectedURI = this.selectedVoice ? (this.selectedVoice.voiceURI || this.selectedVoice.name) : null;
        const savedVoiceURI = sessionStorage.getItem('lore_preferred_voice') || localStorage.getItem('lore_preferred_voice');

        this.dom.voiceSelect.innerHTML = '';

        this.voices.forEach((voice, index) => {
            const opt = document.createElement('option');
            opt.value = voice.voiceURI || voice.name;
            opt.textContent = this.formatVoiceLabel(voice);

            this.dom.voiceSelect.appendChild(opt);
        });

        // Determine best default voice
        let voiceToSelect = null;

        // 1. Try saved user preference
        if (savedVoiceURI) {
            voiceToSelect = this.voices.find(v => (v.voiceURI || v.name) === savedVoiceURI);
        }

        // 2. Try previously selected
        if (!voiceToSelect && currentSelectedURI) {
            voiceToSelect = this.voices.find(v => (v.voiceURI || v.name) === currentSelectedURI);
        }

        // 3. Select top ranked natural voice
        if (!voiceToSelect && this.voices.length > 0) {
            voiceToSelect = this.voices[0];
        }

        if (voiceToSelect) {
            this.selectedVoice = voiceToSelect;
            this.dom.voiceSelect.value = voiceToSelect.voiceURI || voiceToSelect.name;
        }

        console.log(`[LORE Voice Engine] Loaded ${this.voices.length} voices. Default Selected: "${this.selectedVoice ? this.selectedVoice.name : 'Default'}"`);
    }

    /**
     * Switch voice dynamically (works seamlessly mid-playback without restarting story).
     */
    setVoice(voiceURI) {
        if (!voiceURI) return;
        const matched = this.voices.find(v => (v.voiceURI || v.name) === voiceURI);
        if (matched) {
            this.selectedVoice = matched;
            sessionStorage.setItem('lore_preferred_voice', voiceURI);
            localStorage.setItem('lore_preferred_voice', voiceURI);

            if (this.state === this.STATE_PLAYING) {
                // Re-speak current chunk with newly selected voice immediately
                this.speakCurrentChunk();
            }
        }
    }

    /**
     * Set playback speed (0.25x to 2.0x) with direct 1:1 SpeechSynthesisUtterance.rate mapping.
     */
    setSpeed(speed) {
        // Enforce valid float
        const parsedSpeed = Math.max(0.25, Math.min(2.0, parseFloat(speed) || 1.0));
        this.playbackRate = parsedSpeed;

        // Update Speed Buttons UI
        if (this.dom.speedButtons) {
            this.dom.speedButtons.forEach(btn => {
                const btnSpeed = parseFloat(btn.getAttribute('data-speed'));
                if (Math.abs(btnSpeed - parsedSpeed) < 0.01) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
        }

        // Update Mini Player Speed Badge
        if (this.dom.miniSpeed) {
            this.dom.miniSpeed.textContent = `${parsedSpeed}×`;
        }

        if (this.state === this.STATE_PLAYING) {
            // Re-speak current chunk with newly selected speed immediately
            this.speakCurrentChunk();
        }
    }

    /**
     * Splits raw story paragraphs into natural, human-like sentence and clause chunks.
     * Protects abbreviations and respects natural prosodic pauses.
     */
    loadStory(title, storyText) {
        this.stop();

        this.currentTitle = title || 'Story';
        this.currentText = storyText || '';
        this.chunks = [];
        this.currentChunkIndex = 0;

        const paragraphElements = document.querySelectorAll('.story-paragraph');
        const paragraphs = [];

        if (paragraphElements && paragraphElements.length > 0) {
            paragraphElements.forEach(el => {
                const pText = el.textContent.trim();
                if (pText) paragraphs.push(pText);
            });
        } else if (this.currentText) {
            this.currentText.split(/\n+/).forEach(p => {
                const pText = p.trim();
                if (pText) paragraphs.push(pText);
            });
        }

        this.chunks = this.createStoryChunks(paragraphs);

        if (this.dom.miniTitle) {
            this.dom.miniTitle.textContent = this.currentTitle;
        }

        if (this.dom.progressTotalParts) {
            this.dom.progressTotalParts.textContent = `of ${Math.max(1, this.chunks.length)}`;
        }

        this.updateProgress(0);
        this.updateUiState(this.STATE_IDLE);
    }

    /**
     * Splits story text into natural sentence/clause chunks (~12-25 words each)
     * with abbreviation protection so Web Speech API intonation sounds smooth and calm.
     */
    createStoryChunks(paragraphs) {
        const chunks = [];

        paragraphs.forEach((pText, pIdx) => {
            if (!pText || !pText.trim()) return;

            // Protect common abbreviations to prevent unnatural sentence splits
            const protectedText = pText
                .replace(/\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc|i\.e|e\.g)\./gi, '$1__DOT__')
                .trim();

            // Split on sentence boundaries (. ! ?)
            const rawSentences = protectedText.match(/[^.!?]+[.!?]+(\s+|$)|[^.!?]+$/g) || [protectedText];

            rawSentences.forEach(s => {
                const sentence = s.replace(/__DOT__/g, '.').trim();
                if (!sentence) return;

                // If sentence is unusually long (> 140 chars or > 24 words), split at natural clause markers
                if (sentence.length > 140 && (sentence.includes(',') || sentence.includes(';') || sentence.includes('—'))) {
                    const clauses = sentence.match(/[^,;—]+[,;—]?(\s+|$)/g) || [sentence];
                    let buffer = '';

                    clauses.forEach(clause => {
                        if ((buffer + clause).length > 100 && buffer.trim().length > 0) {
                            chunks.push({
                                text: buffer.trim(),
                                paragraphIndex: pIdx,
                                chunkIndex: chunks.length,
                                isParagraphEnd: false
                            });
                            buffer = clause;
                        } else {
                            buffer += clause;
                        }
                    });

                    if (buffer.trim().length > 0) {
                        chunks.push({
                            text: buffer.trim(),
                            paragraphIndex: pIdx,
                            chunkIndex: chunks.length,
                            isParagraphEnd: false
                        });
                    }
                } else {
                    chunks.push({
                        text: sentence,
                        paragraphIndex: pIdx,
                        chunkIndex: chunks.length,
                        isParagraphEnd: false
                    });
                }
            });

            // Mark paragraph boundary for natural breath pause
            if (chunks.length > 0) {
                chunks[chunks.length - 1].isParagraphEnd = true;
            }
        });

        return chunks;
    }

    play() {
        if (!this.isSupported || this.chunks.length === 0) return;

        if (this.state === this.STATE_PAUSED) {
            this.resume();
            return;
        }

        this.currentChunkIndex = 0;
        this.state = this.STATE_PLAYING;
        this.updateUiState(this.STATE_PLAYING);
        this.speakCurrentChunk();
    }

    speakCurrentChunk() {
        if (!this.synth || this.currentChunkIndex >= this.chunks.length) {
            this.onFinish();
            return;
        }

        const chunk = this.chunks[this.currentChunkIndex];
        if (!chunk || !chunk.text) {
            this.currentChunkIndex++;
            this.speakCurrentChunk();
            return;
        }

        this.isHandlingChunkEnd = true;
        this.synth.cancel();
        this.isHandlingChunkEnd = false;

        this.highlightParagraph(chunk.paragraphIndex);
        this.updateProgress(this.currentChunkIndex);

        const utterance = new SpeechSynthesisUtterance(chunk.text);
        utterance.rate = this.playbackRate;
        utterance.pitch = this.playbackPitch;

        if (this.selectedVoice) {
            utterance.voice = this.selectedVoice;
        }

        utterance.onend = () => {
            if (this.isHandlingChunkEnd) return;
            if (this.state === this.STATE_PLAYING) {
                this.currentChunkIndex++;
                if (this.currentChunkIndex < this.chunks.length) {
                    // Add natural breath pause if at paragraph end (180ms), else slight pause (60ms)
                    const pauseMs = chunk.isParagraphEnd ? 180 : 60;
                    setTimeout(() => {
                        if (this.state === this.STATE_PLAYING) {
                            this.speakCurrentChunk();
                        }
                    }, pauseMs);
                } else {
                    this.onFinish();
                }
            }
        };

        utterance.onerror = (event) => {
            if (this.isHandlingChunkEnd || event.error === 'canceled' || event.error === 'interrupted') {
                return;
            }
            console.warn('[LORE TTS] Utterance error:', event.error);
            this.currentChunkIndex++;
            if (this.currentChunkIndex < this.chunks.length) {
                this.speakCurrentChunk();
            } else {
                this.onFinish();
            }
        };

        this.currentUtterance = utterance;
        this.synth.speak(utterance);
    }

    /**
     * Backward 10s: Moves narration backward by one speech chunk (~5-10s of storytelling)
     */
    stepBackward() {
        if (this.chunks.length === 0) return;

        if (this.currentChunkIndex > 0) {
            this.currentChunkIndex--;
        } else {
            this.currentChunkIndex = 0;
        }

        const chunk = this.chunks[this.currentChunkIndex];
        this.highlightParagraph(chunk ? chunk.paragraphIndex : 0);
        this.updateProgress(this.currentChunkIndex);

        if (this.state === this.STATE_PLAYING) {
            this.speakCurrentChunk();
        } else if (this.state === this.STATE_FINISHED) {
            this.state = this.STATE_PAUSED;
            this.updateUiState(this.STATE_PAUSED);
        }
    }

    /**
     * Forward 10s: Advances narration forward by one speech chunk (~5-10s of storytelling)
     */
    stepForward() {
        if (this.chunks.length === 0) return;

        if (this.currentChunkIndex < this.chunks.length - 1) {
            this.currentChunkIndex++;
            const chunk = this.chunks[this.currentChunkIndex];
            this.highlightParagraph(chunk ? chunk.paragraphIndex : 0);
            this.updateProgress(this.currentChunkIndex);

            if (this.state === this.STATE_PLAYING) {
                this.speakCurrentChunk();
            }
        } else {
            this.onFinish();
        }
    }

    /**
     * Direct chunk jump from interactive timeline scrubbing
     */
    jumpToChunk(index) {
        if (index < 0 || index >= this.chunks.length) return;
        this.currentChunkIndex = index;
        const chunk = this.chunks[this.currentChunkIndex];
        this.highlightParagraph(chunk ? chunk.paragraphIndex : 0);
        this.updateProgress(this.currentChunkIndex);

        if (this.state === this.STATE_PLAYING) {
            this.speakCurrentChunk();
        } else {
            this.state = this.STATE_PAUSED;
            this.updateUiState(this.STATE_PAUSED);
        }
    }

    pause() {
        if (!this.synth || this.state !== this.STATE_PLAYING) return;

        this.state = this.STATE_PAUSED;
        this.synth.pause();
        this.updateUiState(this.STATE_PAUSED);
    }

    resume() {
        if (!this.synth || this.state !== this.STATE_PAUSED) return;

        this.state = this.STATE_PLAYING;
        this.updateUiState(this.STATE_PLAYING);

        this.synth.resume();
        if (!this.synth.speaking) {
            this.speakCurrentChunk();
        }
    }

    stop() {
        if (this.synth) {
            this.isHandlingChunkEnd = true;
            this.synth.cancel();
            this.isHandlingChunkEnd = false;
        }

        this.state = this.STATE_IDLE;
        this.currentChunkIndex = 0;
        this.clearParagraphHighlights();
        this.updateProgress(0);
        this.updateUiState(this.STATE_IDLE);
    }

    onFinish() {
        this.state = this.STATE_FINISHED;
        this.currentChunkIndex = 0;
        this.clearParagraphHighlights();
        this.updateProgress(this.chunks.length);
        this.updateUiState(this.STATE_FINISHED);
    }

    updateProgress(chunkIdx) {
        const total = Math.max(1, this.chunks.length);
        const percent = Math.min(100, Math.round(((chunkIdx + 1) / total) * 100));

        if (this.dom.progressCurPos) {
            this.dom.progressCurPos.textContent = `Part ${Math.min(total, chunkIdx + 1)}`;
        }
        if (this.dom.progressFill) {
            this.dom.progressFill.style.width = `${percent}%`;
        }
        if (this.dom.progressDot) {
            this.dom.progressDot.style.left = `${percent}%`;
        }
        if (this.dom.progressBar) {
            this.dom.progressBar.setAttribute('aria-valuenow', percent);
        }

        // Mini player progress line
        if (this.dom.miniFill) {
            this.dom.miniFill.style.width = `${percent}%`;
        }
        if (this.dom.miniThumb) {
            this.dom.miniThumb.style.left = `${percent}%`;
        }
    }

    highlightParagraph(pIndex) {
        this.clearParagraphHighlights();
        const p = document.getElementById(`story-p-${pIndex}`);
        if (p) {
            p.classList.add('active-reading');
            p.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    clearParagraphHighlights() {
        const highlighted = document.querySelectorAll('.story-paragraph.active-reading');
        highlighted.forEach(el => el.classList.remove('active-reading'));
    }

    updateUiState(state) {
        if (!this.dom.btnListen) return;

        switch (state) {
            case this.STATE_PLAYING:
                this.dom.btnListen.classList.add('playing');
                this.dom.btnListen.classList.remove('paused');
                this.dom.btnListen.setAttribute('aria-label', 'Pause story narration');
                this.dom.btnListenIcon.textContent = '⏸';
                this.dom.btnListenText.textContent = 'Pause';
                if (this.dom.waveAnim) this.dom.waveAnim.style.display = 'inline-flex';
                if (this.dom.btnStop) this.dom.btnStop.style.display = 'inline-flex';
                if (this.dom.progressWrapper) this.dom.progressWrapper.style.display = 'flex';

                // Mini Player
                if (this.dom.miniPlayer) this.dom.miniPlayer.style.display = 'flex';
                if (this.dom.miniPlayIcon) this.dom.miniPlayIcon.textContent = '⏸';
                if (this.dom.miniPlayPauseBtn) this.dom.miniPlayPauseBtn.setAttribute('aria-label', 'Pause narration');
                break;

            case this.STATE_PAUSED:
                this.dom.btnListen.classList.remove('playing');
                this.dom.btnListen.classList.add('paused');
                this.dom.btnListen.setAttribute('aria-label', 'Resume story narration');
                this.dom.btnListenIcon.textContent = '▶';
                this.dom.btnListenText.textContent = 'Resume';
                if (this.dom.waveAnim) this.dom.waveAnim.style.display = 'none';
                if (this.dom.btnStop) this.dom.btnStop.style.display = 'inline-flex';
                if (this.dom.progressWrapper) this.dom.progressWrapper.style.display = 'flex';

                // Mini Player
                if (this.dom.miniPlayer) this.dom.miniPlayer.style.display = 'flex';
                if (this.dom.miniPlayIcon) this.dom.miniPlayIcon.textContent = '▶';
                if (this.dom.miniPlayPauseBtn) this.dom.miniPlayPauseBtn.setAttribute('aria-label', 'Resume narration');
                break;

            case this.STATE_FINISHED:
                this.dom.btnListen.classList.remove('playing', 'paused');
                this.dom.btnListen.setAttribute('aria-label', 'Listen to story again');
                this.dom.btnListenIcon.textContent = '↺';
                this.dom.btnListenText.textContent = 'Listen Again';
                if (this.dom.waveAnim) this.dom.waveAnim.style.display = 'none';
                if (this.dom.btnStop) this.dom.btnStop.style.display = 'none';

                // Mini Player
                if (this.dom.miniPlayer) this.dom.miniPlayer.style.display = 'none';
                break;

            case this.STATE_IDLE:
            default:
                this.dom.btnListen.classList.remove('playing', 'paused');
                this.dom.btnListen.setAttribute('aria-label', 'Listen to story');
                this.dom.btnListenIcon.textContent = '▶';
                this.dom.btnListenText.textContent = 'Listen to Story';
                if (this.dom.waveAnim) this.dom.waveAnim.style.display = 'none';
                if (this.dom.btnStop) this.dom.btnStop.style.display = 'none';

                // Mini Player
                if (this.dom.miniPlayer) this.dom.miniPlayer.style.display = 'none';
                break;
        }
    }
}

// Global Singleton Instance
window.LoreSpeech = new LoreSpeechController();

document.addEventListener('DOMContentLoaded', () => {
    window.LoreSpeech.init();
});
