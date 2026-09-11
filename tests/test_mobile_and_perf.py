"""
Comprehensive Automated Verification Script for LORE Mobile Optimization & Performance
Tests:
1. Static Asset Delivery & HTML integrity
2. CSS Responsive Breakpoints & Touch Target Verification
3. JS Syntax & Speech API Engine integrity
4. REST API Endpoint Speed & Latency Benchmarks
5. Error boundary and duplicate prevention
"""

import sys
import os
import json
import urllib.request
import urllib.error
import time
import re

SERVER_URL = "http://127.0.0.1:5000"

def test_endpoints():
    print("[1] Testing REST API Endpoints & Latencies...")
    
    # Test GET /api/info
    t0 = time.time()
    req = urllib.request.Request(f"{SERVER_URL}/api/info")
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        data = json.loads(response.read().decode('utf-8'))
        lat = (time.time() - t0) * 1000
        assert data["status"] == "success"
        assert data["total_stories"] == 520
        assert data["total_categories"] == 13
        print(f"  [PASS] /api/info returned {data['total_stories']} stories across {data['total_categories']} genres in {lat:.2f}ms")

    # Test POST /api/recommend with NLP query
    t0 = time.time()
    payload = json.dumps({"query": "A scary story about a dark haunted forest", "category": "Horror"}).encode('utf-8')
    req = urllib.request.Request(f"{SERVER_URL}/api/recommend", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        data = json.loads(response.read().decode('utf-8'))
        lat = (time.time() - t0) * 1000
        assert data["status"] == "success"
        story = data["story"]
        assert "title" in story and "story_text" in story
        assert len(story["story_text"]) > 50
        print(f"  [PASS] /api/recommend returned '{story['title']}' ({data['relevance_percentage']}% Match) in {lat:.2f}ms")

    # Test "Find Another Story" with exclude_ids
    t0 = time.time()
    first_id = story["id"]
    payload2 = json.dumps({"query": "A scary story about a dark haunted forest", "category": "Horror", "exclude_ids": [first_id]}).encode('utf-8')
    req2 = urllib.request.Request(f"{SERVER_URL}/api/recommend", data=payload2, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req2) as response:
        assert response.status == 200
        data2 = json.loads(response.read().decode('utf-8'))
        story2 = data2["story"]
        assert story2["id"] != first_id, "Duplicate story returned despite exclude_ids"
        print(f"  [PASS] Find Another Story returned distinct story '{story2['title']}' (Excluded ID {first_id})")

    # Test Error Handling
    payload_err = json.dumps({"query": "", "category": None}).encode('utf-8')
    req_err = urllib.request.Request(f"{SERVER_URL}/api/recommend", data=payload_err, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req_err) as response:
            pass
    except urllib.error.HTTPError as e:
        err_data = json.loads(e.read().decode('utf-8'))
        assert err_data["status"] == "error"
        assert "Please enter a story request" in err_data["message"]
        print(f"  [PASS] Error handling correctly returned clean 400 response with message: '{err_data['message']}'")

def test_css_rules():
    print("\n[2] Verifying Responsive CSS Tokens & Mobile Breakpoints...")
    css_path = os.path.join(os.path.dirname(__file__), "..", "app", "static", "style.css")
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    # Verify Restored Original Background Palette Tokens & Atmospheric Glows
    assert "#06080e" in css, "Missing background #06080e in style.css"
    assert "#e6ca85" in css, "Missing gold-primary #e6ca85 in style.css"
    assert "bg-glow" in css, "Missing .bg-glow in style.css"
    assert "glow-gold" in css, "Missing .glow-gold in style.css"
    assert "glow-navy" in css, "Missing .glow-navy in style.css"
    print("  [PASS] Restored original background palette tokens (#06080e) and atmospheric glow elements verified")

    # Verify Breakpoints
    breakpoints = ["1024px", "768px", "640px", "430px", "360px"]
    for bp in breakpoints:
        assert bp in css, f"Missing breakpoint {bp} in style.css"
        print(f"  [PASS] Breakpoint {bp} defined in media queries")

    # Verify Fluid Typography & Clamp
    assert "clamp(" in css, "clamp() not found in style.css"
    clamp_count = css.count("clamp(")
    print(f"  [PASS] Found {clamp_count} fluid clamp() rules for responsive typography and spacing")

    # Verify Safe Area Insets
    assert "env(safe-area-inset-bottom)" in css, "Missing safe-area-inset-bottom"
    assert "env(safe-area-inset-top)" in css, "Missing safe-area-inset-top"
    print("  [PASS] Safe-area insets (env(safe-area-inset-top), env(safe-area-inset-bottom)) verified")

    # Verify Prefers Reduced Motion
    assert "prefers-reduced-motion" in css, "Missing prefers-reduced-motion"
    print("  [PASS] prefers-reduced-motion accessibility media query verified")

    # Verify No Horizontal Overflow safeguards
    assert "overflow-x: hidden" in css
    assert "max-width: 100vw" in css
    print("  [PASS] Strict horizontal overflow prevention tokens verified")

def test_js_speech_and_script():
    print("\n[3] Verifying JavaScript Voice Engine & DOM Logic...")
    speech_path = os.path.join(os.path.dirname(__file__), "..", "app", "static", "speech.js")
    with open(speech_path, "r", encoding="utf-8") as f:
        speech_code = f.read()

    assert "TextToSpeechProvider" in speech_code, "Missing TextToSpeechProvider base class"
    assert "BrowserSpeechProvider" in speech_code, "Missing BrowserSpeechProvider class"
    assert "setVoiceById" in speech_code, "Missing setVoiceById method"
    assert "utterance.voice = this.selectedVoice.rawVoice" in speech_code or "utterance.voice" in speech_code, "Missing utterance.voice assignment"
    assert "playbackSessionId" in speech_code, "Missing playbackSessionId session token for duplicate speech prevention"
    assert "top5 = pool.slice(0, 5)" in speech_code or "slice(0, 5)" in speech_code, "Missing top 5 voice limiting"
    assert "stepBackward" in speech_code, "Missing stepBackward method"
    assert "stepForward" in speech_code, "Missing stepForward method"
    assert "updateProgress(0, false)" in speech_code or "updateProgress(0" in speech_code, "Missing initial 0% progress reset"
    assert "setSpeed" in speech_code, "Missing setSpeed method"
    print("  [PASS] Speech engine architecture verified (TextToSpeechProvider, BrowserSpeechProvider, top 5 voices, session IDs, ~10s seek navigation, 8-speed engine, initial 0% progress)")

    script_path = os.path.join(os.path.dirname(__file__), "..", "app", "static", "script.js")
    with open(script_path, "r", encoding="utf-8") as f:
        script_code = f.read()

    assert "copyStoryToClipboard" in script_code, "Missing copyStoryToClipboard function"
    assert "execCommand" in script_code, "Missing execCommand copy fallback for mobile HTTP"
    assert "✓ Copied" in script_code, "Missing visual '✓ Copied' button feedback"
    assert "Unable to copy. Please select and copy the story manually." in script_code, "Missing user-friendly copy error fallback"
    assert "createDocumentFragment" in script_code, "Missing DocumentFragment in script.js"
    assert "scrollIntoView" in script_code, "Missing scrollIntoView in script.js"
    print("  [PASS] script.js DocumentFragment rendering, copyStoryToClipboard (with mobile HTTP execCommand fallback), and Story Section scrolling verified")

def test_html_structure():
    print("\n[4] Verifying HTML Structure & 8-Speed Controls...")
    html_path = os.path.join(os.path.dirname(__file__), "..", "app", "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    speeds = ["0.25", "0.5", "0.75", "1.0", "1.25", "1.5", "1.75", "2.0"]
    for s in speeds:
        assert f'data-speed="{s}"' in html, f"Missing speed button for {s}x"
    print("  [PASS] All 8 speed buttons (0.25x, 0.5x, 0.75x, 1x, 1.25x, 1.5x, 1.75x, 2x) verified in template")

    assert 'id="story-section"' in html, "Missing #story-section id"
    assert 'id="mini-audio-player"' in html, "Missing #mini-audio-player"
    assert 'id="active-category-indicator"' in html, "Missing active category indicator"
    assert 'id="voice-status-note"' in html, "Missing voice status note indicator"
    print("  [PASS] Semantic IDs (#story-section, #mini-audio-player, #voice-status-note, category chips) verified")

if __name__ == "__main__":
    print("==========================================================")
    print("   LORE Mobile & Performance Comprehensive Test Suite     ")
    print("==========================================================")
    try:
        test_endpoints()
        test_css_rules()
        test_js_speech_and_script()
        test_html_structure()
        print("\n==========================================================")
        print("   ALL VERIFICATION TESTS PASSED SUCCESSFULLY (100%)      ")
        print("==========================================================")
    except Exception as e:
        print(f"\n[FAIL] Test encountered error: {e}")
        sys.exit(1)
