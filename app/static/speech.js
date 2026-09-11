/**
 * LORE — Natural Audiobook-Style Voice Narration Architecture
 * 
 * Modular Architecture:
 * - TextToSpeechProvider: Abstract base interface for TTS engines (ready for future CloudTTSProvider)
 * - BrowserSpeechProvider: Production Web Speech API implementation optimized for Mobile (iOS Safari & Android Chrome) & Desktop
 * - LoreSpeechController: Coordinates player UI, timeline scrub bar, paragraph synchronization, 8-speed engine, and reliable 10s seek
 */

// ============================================================================
// 1. TextToSpeechProvider (Abstract Base Interface)
// ============================================================================
class TextToSpeechProvider {
    constructor() {
        this.onStart = null;
        this.onEnd = null;
        this.onError = null;
        this.onBoundary = null;
        this.onVoicesChanged = null;
    }

    isSupported() {
        return false;
    }

    getVoices() {
        return [];
    }

    speak(text, options = {}) {
        throw new Error('speak() must be implemented by concrete provider');
    }

    pause() {
        throw new Error('pause() must be implemented by concrete provider');
    }

    resume() {
        throw new Error('resume() must be implemented by concrete provider');
    }

    stop() {
        throw new Error('stop() must be implemented by concrete provider');
    }
}

// ============================================================================
// 2. BrowserSpeechProvider (Web Speech API Engine with Mobile Fixes)
// ============================================================================
class BrowserSpeechProvider extends TextToSpeechProvider {
    constructor() {
        super();
        this.synth = typeof window !== 'undefined' ? (window.speechSynthesis || null) : null;
        this.voices = []; // Maximum 5 top-ranked voices
        this.selectedVoice = null;
        this.activeUtterance = null;
        this.isCancelling = false;
        this.heartbeatTimer = null;
        this.voiceLoadAttempts = 0;
        this.playbackSessionId = 0;

        this.init();
    }

    isSupported() {
        return !!this.synth && typeof window !== 'undefined' && 'SpeechSynthesisUtterance' in window;
    }

    init() {
        if (!this.isSupported()) {
            console.warn('[LORE TTS Engine] Web Speech API is not supported in this browser.');
            return;
        }

        this.loadVoices();

        // Standard event listener for voice loading
        if (this.synth.onvoiceschanged !== undefined) {
            this.synth.onvoiceschanged = () => {
                this.loadVoices();
            };
        }

        // Mobile fallback polling: Android Chrome and iOS Safari may not fire onvoiceschanged
        const pollIntervals = [100, 300, 800, 1500, 3000];
        pollIntervals.forEach(ms => {
            setTimeout(() => {
                if (this.voices.length === 0 || this.voiceLoadAttempts < 3) {
                    this.loadVoices();
                }
            }, ms);
        });
    }

    /**
     * Scores voices based on naturalness and storytelling suitability.
     */
    scoreVoice(v) {
        let score = 0;
        const name = (v.name || '').toLowerCase();
        const lang = (v.lang || '').toLowerCase();
        const uri = (v.voiceURI || '').toLowerCase();
        const full = `${name} ${lang} ${uri}`;

        // 1. Language Priority (English first)
        if (lang.startsWith('en')) {
            score += 160;
            if (lang.includes('us')) score += 30;
            else if (lang.includes('gb') || lang.includes('uk')) score += 25;
            else if (lang.includes('au') || lang.includes('ca')) score += 20;
            else if (lang.includes('ie') || lang.includes('in')) score += 15;
        } else {
            return -500; // Deprioritize non-English
        }

        // 2. High-Fidelity Neural / Natural Terminology
        if (full.includes('natural')) score += 140;
        if (full.includes('neural')) score += 140;
        if (full.includes('online')) score += 90;
        if (full.includes('premium')) score += 80;
        if (full.includes('enhanced')) score += 80;
        if (full.includes('siri')) score += 70;
        if (full.includes('google')) score += 60;

        // 3. Known Premium Storyteller Voice Personas
        const naturalNames = [
            'ava', 'jenny', 'aria', 'guy', 'samantha', 'steffan', 
            'ryan', 'daniel', 'sonia', 'andrew', 'brian', 'emma', 
            'oliver', 'serena', 'karen', 'george', 'susan', 'david', 'mark', 'zira'
        ];
        
        naturalNames.forEach((n, idx) => {
            if (name.includes(n)) {
                score += Math.max(10, 60 - (idx * 2));
            }
        });

        if (v.default) score += 20;
        if (!v.localService) score += 15; // Remote neural voices on Edge/Chrome are typically higher quality

        return score;
    }

    /**
     * Loads, ranks, and selects EXACTLY top 5 (or fewer if device has fewer) available English voices.
     * Generates clean, human-friendly names (e.g. Natural 1 (Jenny), Natural 2 (Aria)).
     */
    loadVoices() {
        if (!this.synth) return [];

        this.voiceLoadAttempts++;
        const rawVoices = this.synth.getVoices() || [];

        if (rawVoices.length === 0) {
            return [];
        }

        // Score all available voices
        const scored = rawVoices.map((v, idx) => ({
            rawVoice: v,
            index: idx,
            score: this.scoreVoice(v)
        }));

        // Filter for English voices first, fallback to all if none
        const englishScored = scored.filter(s => s.score > 0);
        const pool = englishScored.length > 0 ? englishScored : scored;

        // Sort descending by score
        pool.sort((a, b) => b.score - a.score);

        // Limit to EXACTLY a maximum of 5 top voices
        const top5 = pool.slice(0, 5);

        this.voices = top5.map((item, idx) => {
            const v = item.rawVoice;
            const voiceId = v.voiceURI || `${v.name}_${v.lang}_${idx}`;
            const label = this.formatVoiceLabel(v, idx + 1);

            return {
                id: voiceId,
                number: idx + 1,
                name: v.name || `Natural Voice ${idx + 1}`,
                lang: v.lang || 'en-US',
                voiceURI: v.voiceURI || '',
                isDefault: !!v.default,
                isLocal: !!v.localService,
                label: label,
                rawVoice: v
            };
        });

        // Auto-select best default voice
        this.selectDefaultVoice();

        if (typeof this.onVoicesChanged === 'function') {
            this.onVoicesChanged(this.voices);
        }

        console.log(`[LORE Voice Engine] Selected EXACTLY ${this.voices.length} Top Voices:`, 
            this.voices.map(v => `${v.label} [${v.lang}]`));

        return this.voices;
    }

    /**
     * Formats technical voice names into clean, simple, intuitive labels.
     */
    formatVoiceLabel(v, number) {
        const rawName = (v.name || '').trim();

        let clean = rawName
            .replace(/Microsoft\s+/gi, '')
            .replace(/Google\s+/gi, '')
            .replace(/Apple\s+/gi, '')
            .replace(/Desktop/gi, '')
            .replace(/\(Natural\)/gi, '')
            .replace(/\(Neural\)/gi, '')
            .replace(/Online/gi, '')
            .replace(/-\s*English.*$/gi, '')
            .replace(/\s+/g, ' ')
            .trim();

        if (clean && !clean.toLowerCase().includes('voice') && clean.length <= 15) {
            return `Natural ${number} (${clean})`;
        } else {
            return `Natural ${number}`;
        }
    }

    selectDefaultVoice() {
        if (this.voices.length === 0) return;

        const savedId = sessionStorage.getItem('lore_preferred_voice_id') || localStorage.getItem('lore_preferred_voice_id');
        let matched = null;

        if (savedId) {
            matched = this.voices.find(v => v.id === savedId || v.voiceURI === savedId || v.name === savedId);
        }

        if (!matched && this.voices.length > 0) {
            matched = this.voices[0];
        }

        this.selectedVoice = matched;
    }

    setVoiceById(voiceId) {
        if (!voiceId || this.voices.length === 0) return false;

        const matched = this.voices.find(v => v.id === voiceId || v.voiceURI === voiceId || v.name === voiceId);
        if (matched) {
            this.selectedVoice = matched;
            sessionStorage.setItem('lore_preferred_voice_id', matched.id);
            localStorage.setItem('lore_preferred_voice_id', matched.id);

            console.log('[LORE TTS] Voice Switched to:', {
                number: matched.number,
                name: matched.name,
                label: matched.label,
                lang: matched.lang,
                voiceURI: matched.voiceURI,
                rawVoiceObj: matched.rawVoice,
                platform: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown'
            });

            return true;
        }

        console.warn('[LORE TTS] Voice ID not found in available top 5:', voiceId);
        return false;
    }

    /**
     * Speaks a text chunk with session token protection against race conditions.
     */
    speak(text, options = {}) {
        if (!this.synth || !this.isSupported()) {
            if (typeof this.onError === 'function') {
                this.onError(new Error('Web Speech API is unavailable'));
            }
            return;
        }

        const rate = Math.max(0.25, Math.min(2.0, parseFloat(options.rate) || 1.0));
        const pitch = Math.max(0.5, Math.min(1.5, parseFloat(options.pitch) || 1.0));

        // Increment session ID to invalidate callbacks from any previous utterances
        const currentSessionId = ++this.playbackSessionId;

        // Safely cancel any active speech
        this.stopHeartbeat();
        this.isCancelling = true;
        this.synth.cancel();
        this.isCancelling = false;

        if (!text || !text.trim()) {
            if (typeof this.onEnd === 'function') this.onEnd(currentSessionId);
            return;
        }

        const utterance = new SpeechSynthesisUtterance(text.trim());
        utterance.rate = rate;
        utterance.pitch = pitch;

        // CRITICAL: Look up live voice directly from window.speechSynthesis.getVoices()
        const liveVoices = this.synth.getVoices() || [];
        let liveVoiceToUse = null;

        if (this.selectedVoice) {
            liveVoiceToUse = liveVoices.find(lv => 
                (this.selectedVoice.voiceURI && lv.voiceURI === this.selectedVoice.voiceURI) ||
                (lv.name === this.selectedVoice.name && lv.lang === this.selectedVoice.lang) ||
                lv.name === this.selectedVoice.name
            );
        }

        if (!liveVoiceToUse && this.voices.length > 0) {
            const fallbackVoice = this.voices[0];
            liveVoiceToUse = liveVoices.find(lv => lv.name === fallbackVoice.name) || liveVoices[0];
        }

        if (liveVoiceToUse) {
            utterance.voice = liveVoiceToUse;
            utterance.lang = liveVoiceToUse.lang || 'en-US';
        }

        // Utterance Event Listeners with Session ID Guard
        utterance.onstart = () => {
            if (this.playbackSessionId !== currentSessionId) return;
            this.startHeartbeat();
            if (typeof this.onStart === 'function') {
                this.onStart(currentSessionId);
            }
        };

        utterance.onend = () => {
            this.stopHeartbeat();
            this.activeUtterance = null;
            if (this.isCancelling) return;
            if (this.playbackSessionId !== currentSessionId) return; // Prevent duplicate speech from cancelled callbacks

            if (typeof this.onEnd === 'function') {
                this.onEnd(currentSessionId);
            }
        };

        utterance.onerror = (event) => {
            this.stopHeartbeat();
            this.activeUtterance = null;

            if (this.isCancelling || event.error === 'canceled' || event.error === 'interrupted') {
                return;
            }
            if (this.playbackSessionId !== currentSessionId) return;

            console.warn('[LORE TTS] Utterance error event:', event.error || event);
            if (typeof this.onError === 'function') {
                this.onError(event, currentSessionId);
            }
        };

        this.activeUtterance = utterance;

        try {
            this.synth.speak(utterance);
        } catch (err) {
            console.error('[LORE TTS] Exception calling synth.speak():', err);
            if (typeof this.onError === 'function') {
                this.onError(err, currentSessionId);
            }
        }
    }

    pause() {
        if (!this.synth) return;
        this.stopHeartbeat();
        this.synth.pause();
    }

    resume() {
        if (!this.synth) return;
        this.synth.resume();
        this.startHeartbeat();

        if (!this.synth.speaking && this.activeUtterance) {
            try {
                this.synth.speak(this.activeUtterance);
            } catch (e) {
                // Ignore
            }
        }
    }

    stop() {
        this.stopHeartbeat();
        this.playbackSessionId++; // Invalidate running callbacks
        this.activeUtterance = null;

        if (this.synth) {
            this.isCancelling = true;
            this.synth.cancel();
            this.isCancelling = false;
        }
    }

    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatTimer = setInterval(() => {
            if (this.synth && this.synth.speaking && !this.synth.paused) {
                this.synth.pause();
                this.synth.resume();
            }
        }, 12000);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }
}

// ============================================================================
// 3. LoreSpeechController (Story Narrator & UI Controller)
// ============================================================================
class LoreSpeechController {
    constructor() {
        this.provider = new BrowserSpeechProvider();

        // Playback States
        this.STATE_IDLE = 'IDLE';
        this.STATE_PLAYING = 'PLAYING';
        this.STATE_PAUSED = 'PAUSED';
        this.STATE_FINISHED = 'FINISHED';
        this.state = this.STATE_IDLE;

        // Story Chunks for Navigation (~10-15s granularity per chunk)
        this.currentTitle = '';
        this.currentText = '';
        this.chunks = []; // Array of { text, paragraphIndex, chunkIndex, isParagraphEnd }
        this.currentChunkIndex = 0;

        // Natural Storytelling Playback Defaults
        this.playbackRate = 1.0;
        this.playbackPitch = 1.0;

        // DOM Elements Cache
        this.dom = {};
    }

    init() {
        this.cacheDom();

        if (!this.provider.isSupported()) {
            console.warn('[LORE TTS Controller] TTS is not supported in this browser.');
            if (this.dom.toolbar) {
                this.dom.toolbar.innerHTML = `
                    <div class="speech-unsupported-notice" style="padding: 12px; color: var(--text-muted); font-size: 0.88rem; text-align: center;">
                        <span>ℹ Voice narration isn't supported by this browser.</span>
                    </div>
                `;
            }
            return;
        }

        this.bindEvents();
        this.setupProviderCallbacks();

        const voices = this.provider.loadVoices();
        if (voices.length > 0) {
            this.renderVoiceOptions(voices);
        }

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                if (this.state === this.STATE_PLAYING && !this.provider.synth.speaking) {
                    this.updateUiState(this.STATE_PAUSED);
                    this.state = this.STATE_PAUSED;
                }
            }
        });
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
            voiceSelectGroup: document.getElementById('voice-select-group'),
            voiceSelect: document.getElementById('voice-select'),
            voiceStatusNote: document.getElementById('voice-status-note'),
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

    setupProviderCallbacks() {
        this.provider.onVoicesChanged = (voices) => {
            this.renderVoiceOptions(voices);
        };

        this.provider.onStart = () => {
            // Started playback
        };

        this.provider.onEnd = (sessionId) => {
            if (this.state === this.STATE_PLAYING) {
                this.currentChunkIndex++;
                if (this.currentChunkIndex < this.chunks.length) {
                    this.speakCurrentChunk();
                } else {
                    this.onFinish();
                }
            }
        };

        this.provider.onError = (err, sessionId) => {
            console.warn('[LORE TTS Controller] Provider Error Callback:', err);
            if (this.state === this.STATE_PLAYING) {
                this.currentChunkIndex++;
                if (this.currentChunkIndex < this.chunks.length) {
                    this.speakCurrentChunk();
                } else {
                    this.onFinish();
                }
            }
        };
    }

    renderVoiceOptions(voices) {
        if (!this.dom.voiceSelect) return;

        this.dom.voiceSelect.innerHTML = '';

        if (!voices || voices.length === 0) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = 'Natural 1 (Default)';
            this.dom.voiceSelect.appendChild(opt);
            this.updateVoiceStatusNote('No browser voices detected.');
            return;
        }

        voices.forEach(v => {
            const opt = document.createElement('option');
            opt.value = v.id;
            opt.textContent = v.label;
            this.dom.voiceSelect.appendChild(opt);
        });

        if (this.provider.selectedVoice) {
            this.dom.voiceSelect.value = this.provider.selectedVoice.id;
        }

        if (voices.length === 1) {
            this.updateVoiceStatusNote('Your device provides only one browser voice.');
        } else {
            this.updateVoiceStatusNote(null);
        }
    }

    updateVoiceStatusNote(message) {
        if (!this.dom.voiceStatusNote) {
            if (this.dom.voiceSelectGroup && message) {
                const note = document.createElement('span');
                note.id = 'voice-status-note';
                note.className = 'voice-status-note';
                note.style.cssText = 'font-size: 0.72rem; color: var(--text-muted); font-style: italic; width: 100%; display: block; margin-top: 4px;';
                note.textContent = message;
                this.dom.voiceSelectGroup.appendChild(note);
                this.dom.voiceStatusNote = note;
            }
            return;
        }

        if (message) {
            this.dom.voiceStatusNote.textContent = message;
            this.dom.voiceStatusNote.style.display = 'block';
        } else {
            this.dom.voiceStatusNote.style.display = 'none';
        }
    }

    bindEvents() {
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

        if (this.dom.btnBack) {
            this.dom.btnBack.addEventListener('click', () => this.stepBackward());
        }

        if (this.dom.btnForward) {
            this.dom.btnForward.addEventListener('click', () => this.stepForward());
        }

        if (this.dom.btnStop) {
            this.dom.btnStop.addEventListener('click', () => this.stop());
        }

        if (this.dom.voiceSelect) {
            this.dom.voiceSelect.addEventListener('change', (e) => {
                this.setVoice(e.target.value);
            });
        }

        if (this.dom.speedButtons) {
            this.dom.speedButtons.forEach((btn) => {
                btn.addEventListener('click', () => {
                    const speed = parseFloat(btn.getAttribute('data-speed') || '1.0');
                    this.setSpeed(speed);
                });
            });
        }

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

        if (this.dom.progressBar) {
            this.dom.progressBar.addEventListener('click', (e) => this.handleTrackClick(e, this.dom.progressBar));
        }

        if (this.dom.miniTrack) {
            this.dom.miniTrack.addEventListener('click', (e) => this.handleTrackClick(e, this.dom.miniTrack));
        }

        window.addEventListener('keydown', (e) => this.handleKeyboardNav(e));
    }

    handleKeyboardNav(e) {
        const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
        if (activeTag === 'input' || activeTag === 'textarea' || activeTag === 'select') {
            return;
        }

        if (e.key === 'ArrowLeft' && (this.state === this.STATE_PLAYING || this.state === this.STATE_PAUSED)) {
            e.preventDefault();
            this.stepBackward();
        } else if (e.key === 'ArrowRight' && (this.state === this.STATE_PLAYING || this.state === this.STATE_PAUSED)) {
            e.preventDefault();
            this.stepForward();
        } else if (e.key === ' ' && (this.state === this.STATE_PLAYING || this.state === this.STATE_PAUSED)) {
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

    setVoice(voiceId) {
        if (!voiceId) return;
        const changed = this.provider.setVoiceById(voiceId);

        if (changed && this.state === this.STATE_PLAYING) {
            this.speakCurrentChunk();
        }
    }

    setSpeed(speed) {
        const parsedSpeed = Math.max(0.25, Math.min(2.0, parseFloat(speed) || 1.0));
        this.playbackRate = parsedSpeed;

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

        if (this.dom.miniSpeed) {
            this.dom.miniSpeed.textContent = `${parsedSpeed}×`;
        }

        if (this.state === this.STATE_PLAYING) {
            this.speakCurrentChunk();
        }
    }

    /**
     * Resets all playback state and initializes progress strictly at 0% (far left).
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

        // Strictly reset visual progress to 0%
        this.updateProgress(0, false);
        this.updateUiState(this.STATE_IDLE);

        console.log(`[LORE Story Narration] Loaded: "${this.currentTitle}". Created ${this.chunks.length} navigable speech chunks (~10-15s each). Initial Progress: 0%`);
    }

    /**
     * Splits paragraphs into navigable speech units (~150-250 characters each, ~10-15s speech).
     * Provides genuine, responsive Forward 10s and Backward 10s seek granularity.
     */
    createStoryChunks(paragraphs) {
        const chunks = [];

        paragraphs.forEach((pText, pIdx) => {
            const cleanPara = pText.trim();
            if (!cleanPara) return;

            // Protect common abbreviations from premature splitting
            const protectedText = cleanPara
                .replace(/\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc|i\.e|e\.g|Fig|No)\./gi, '$1__DOT__')
                .trim();

            // Split on sentence boundaries (. ! ?)
            const rawSentences = protectedText.match(/[^.!?]+[.!?]+(\s+|$)|[^.!?]+$/g) || [protectedText];
            let buffer = '';

            rawSentences.forEach((s) => {
                const sentence = s.replace(/__DOT__/g, '.').trim();
                if (!sentence) return;

                // Group ~1 to 2 sentences (~180-240 characters) per chunk for ~10-15s seek step
                if ((buffer + ' ' + sentence).trim().length <= 220 && buffer.length > 0) {
                    buffer = `${buffer} ${sentence}`;
                } else {
                    if (buffer.trim().length > 0) {
                        chunks.push({
                            text: buffer.trim(),
                            paragraphIndex: pIdx,
                            chunkIndex: chunks.length,
                            isParagraphEnd: false
                        });
                    }
                    buffer = sentence;
                }
            });

            if (buffer.trim().length > 0) {
                chunks.push({
                    text: buffer.trim(),
                    paragraphIndex: pIdx,
                    chunkIndex: chunks.length,
                    isParagraphEnd: true
                });
            }
        });

        if (chunks.length === 0 && this.currentText.trim()) {
            chunks.push({
                text: this.currentText.trim(),
                paragraphIndex: 0,
                chunkIndex: 0,
                isParagraphEnd: true
            });
        }

        return chunks;
    }

    play() {
        if (!this.provider.isSupported() || this.chunks.length === 0) return;

        if (this.state === this.STATE_PAUSED) {
            this.resume();
            return;
        }

        // If played after finished or idle, start cleanly at chunk 0
        this.currentChunkIndex = 0;
        this.state = this.STATE_PLAYING;
        this.updateUiState(this.STATE_PLAYING);
        this.updateProgress(0, false);
        this.speakCurrentChunk();
    }

    speakCurrentChunk() {
        if (this.currentChunkIndex >= this.chunks.length) {
            this.onFinish();
            return;
        }

        const chunk = this.chunks[this.currentChunkIndex];
        if (!chunk || !chunk.text) {
            this.currentChunkIndex++;
            this.speakCurrentChunk();
            return;
        }

        if (chunk.paragraphIndex !== undefined) {
            this.highlightParagraph(chunk.paragraphIndex);
        }
        this.updateProgress(this.currentChunkIndex, false);

        this.provider.speak(chunk.text, {
            rate: this.playbackRate,
            pitch: this.playbackPitch
        });
    }

    /**
     * Backward 10s: Moves to previous chunk (~10-15s earlier) and re-speaks immediately.
     */
    stepBackward() {
        if (this.chunks.length === 0) return;

        if (this.currentChunkIndex > 0) {
            this.currentChunkIndex--;
        } else {
            this.currentChunkIndex = 0;
        }

        const chunk = this.chunks[this.currentChunkIndex];
        if (chunk && chunk.paragraphIndex !== undefined) {
            this.highlightParagraph(chunk.paragraphIndex);
        }
        this.updateProgress(this.currentChunkIndex, false);

        if (this.state === this.STATE_PLAYING) {
            this.speakCurrentChunk();
        } else if (this.state === this.STATE_FINISHED || this.state === this.STATE_PAUSED) {
            this.state = this.STATE_PAUSED;
            this.updateUiState(this.STATE_PAUSED);
        }
    }

    /**
     * Forward 10s: Moves to next chunk (~10-15s ahead) and speaks immediately.
     */
    stepForward() {
        if (this.chunks.length === 0) return;

        if (this.currentChunkIndex < this.chunks.length - 1) {
            this.currentChunkIndex++;
            const chunk = this.chunks[this.currentChunkIndex];
            if (chunk && chunk.paragraphIndex !== undefined) {
                this.highlightParagraph(chunk.paragraphIndex);
            }
            this.updateProgress(this.currentChunkIndex, false);

            if (this.state === this.STATE_PLAYING) {
                this.speakCurrentChunk();
            } else {
                this.state = this.STATE_PAUSED;
                this.updateUiState(this.STATE_PAUSED);
            }
        } else {
            this.onFinish();
        }
    }

    jumpToChunk(index) {
        if (index < 0 || index >= this.chunks.length) return;
        this.currentChunkIndex = index;
        const chunk = this.chunks[this.currentChunkIndex];
        if (chunk && chunk.paragraphIndex !== undefined) {
            this.highlightParagraph(chunk.paragraphIndex);
        }
        this.updateProgress(this.currentChunkIndex, false);

        if (this.state === this.STATE_PLAYING) {
            this.speakCurrentChunk();
        } else {
            this.state = this.STATE_PAUSED;
            this.updateUiState(this.STATE_PAUSED);
        }
    }

    pause() {
        if (this.state !== this.STATE_PLAYING) return;
        this.state = this.STATE_PAUSED;
        this.provider.pause();
        this.updateUiState(this.STATE_PAUSED);
    }

    resume() {
        if (this.state !== this.STATE_PAUSED) return;
        this.state = this.STATE_PLAYING;
        this.updateUiState(this.STATE_PLAYING);
        this.provider.resume();
    }

    stop() {
        this.provider.stop();
        this.state = this.STATE_IDLE;
        this.currentChunkIndex = 0;
        this.clearParagraphHighlights();
        this.updateProgress(0, false);
        this.updateUiState(this.STATE_IDLE);
    }

    onFinish() {
        this.provider.stop();
        this.state = this.STATE_FINISHED;
        this.clearParagraphHighlights();
        this.updateProgress(this.chunks.length, true); // Sets progress to 100% only on final finish
        this.updateUiState(this.STATE_FINISHED);
    }

    /**
     * Accurate Progress Calculation:
     * - Idle / Load / Stop: starts at 0% (far left)
     * - Chunk i out of N: (i / N) * 100% (progresses from 0% towards 100%)
     * - Finished: 100%
     */
    updateProgress(chunkIdx, isFinished = false) {
        const total = Math.max(1, this.chunks.length);
        let percent = 0;

        if (isFinished || this.state === this.STATE_FINISHED) {
            percent = 100;
        } else {
            percent = Math.min(100, Math.max(0, Math.round((chunkIdx / total) * 100)));
        }

        if (this.dom.progressCurPos) {
            const displayPart = isFinished ? total : Math.min(total, chunkIdx + 1);
            this.dom.progressCurPos.textContent = `Part ${displayPart}`;
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
                if (this.dom.btnListenIcon) this.dom.btnListenIcon.textContent = '⏸';
                if (this.dom.btnListenText) this.dom.btnListenText.textContent = 'Pause';
                if (this.dom.waveAnim) this.dom.waveAnim.style.display = 'inline-flex';
                if (this.dom.btnStop) this.dom.btnStop.style.display = 'inline-flex';
                if (this.dom.progressWrapper) this.dom.progressWrapper.style.display = 'flex';

                if (this.dom.miniPlayer) this.dom.miniPlayer.style.display = 'flex';
                if (this.dom.miniPlayIcon) this.dom.miniPlayIcon.textContent = '⏸';
                if (this.dom.miniPlayPauseBtn) this.dom.miniPlayPauseBtn.setAttribute('aria-label', 'Pause narration');
                break;

            case this.STATE_PAUSED:
                this.dom.btnListen.classList.remove('playing');
                this.dom.btnListen.classList.add('paused');
                this.dom.btnListen.setAttribute('aria-label', 'Resume story narration');
                if (this.dom.btnListenIcon) this.dom.btnListenIcon.textContent = '▶';
                if (this.dom.btnListenText) this.dom.btnListenText.textContent = 'Resume';
                if (this.dom.waveAnim) this.dom.waveAnim.style.display = 'none';
                if (this.dom.btnStop) this.dom.btnStop.style.display = 'inline-flex';
                if (this.dom.progressWrapper) this.dom.progressWrapper.style.display = 'flex';

                if (this.dom.miniPlayer) this.dom.miniPlayer.style.display = 'flex';
                if (this.dom.miniPlayIcon) this.dom.miniPlayIcon.textContent = '▶';
                if (this.dom.miniPlayPauseBtn) this.dom.miniPlayPauseBtn.setAttribute('aria-label', 'Resume narration');
                break;

            case this.STATE_FINISHED:
                this.dom.btnListen.classList.remove('playing', 'paused');
                this.dom.btnListen.setAttribute('aria-label', 'Listen to story again');
                if (this.dom.btnListenIcon) this.dom.btnListenIcon.textContent = '↺';
                if (this.dom.btnListenText) this.dom.btnListenText.textContent = 'Listen Again';
                if (this.dom.waveAnim) this.dom.waveAnim.style.display = 'none';
                if (this.dom.btnStop) this.dom.btnStop.style.display = 'none';

                if (this.dom.miniPlayer) this.dom.miniPlayer.style.display = 'none';
                break;

            case this.STATE_IDLE:
            default:
                this.dom.btnListen.classList.remove('playing', 'paused');
                this.dom.btnListen.setAttribute('aria-label', 'Listen to story');
                if (this.dom.btnListenIcon) this.dom.btnListenIcon.textContent = '▶';
                if (this.dom.btnListenText) this.dom.btnListenText.textContent = 'Listen to Story';
                if (this.dom.waveAnim) this.dom.waveAnim.style.display = 'none';
                if (this.dom.btnStop) this.dom.btnStop.style.display = 'none';

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
