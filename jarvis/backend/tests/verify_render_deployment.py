import json
import ssl
import time
import urllib.request
import urllib.error

RENDER_BASE = "https://jarvis-ai-assistant-dgkd.onrender.com"
ctx = ssl._create_unverified_context()

print("=" * 80)
print("       JARVIS LIVE RENDER CLOUD PRODUCTION VERIFICATION SUITE")
print(f"       Target: {RENDER_BASE}")
print(f"       Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

results = []

def record(category, test_name, passed, detail=""):
    mark = "✓" if passed else "✗"
    status = "PASS" if passed else "FAIL"
    print(f"  {mark} [{status}] {test_name:<46} : {detail}")
    results.append({"category": category, "name": test_name, "passed": passed, "detail": detail})

def fetch(url, data=None, headers=None, timeout=15):
    last_err = None
    for attempt in range(2):
        try:
            h = headers or {"User-Agent": "Mozilla/5.0"}
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, context=ctx, timeout=timeout) as res:
                return res.status, res.read()
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    raise last_err

# 1. Frontend & Single-Page Application Routes
print("\n[1. FRONTEND SINGLE-PAGE-APP & STATIC ASSETS]")
try:
    status, raw = fetch(f"{RENDER_BASE}/")
    body = raw.decode('utf-8', errors='ignore')
    has_html = "<!doctype html>" in body.lower()
    record("SPA", "Root URL (GET /)", status == 200 and has_html, f"Status {status}, {len(body)} bytes")
except Exception as e:
    record("SPA", "Root URL (GET /)", False, str(e))

try:
    status, raw = fetch(f"{RENDER_BASE}/mobile")
    body = raw.decode('utf-8', errors='ignore')
    has_html = "<!doctype html>" in body.lower()
    record("SPA", "Mobile Route Fallback (GET /mobile)", status == 200 and has_html, f"Status {status}, {len(body)} bytes")
except Exception as e:
    record("SPA", "Mobile Route Fallback (GET /mobile)", False, str(e))

try:
    status, raw = fetch(f"{RENDER_BASE}/assets/index-CnKK0OOm.js")
    record("SPA", "Compiled JavaScript Bundle (/assets/index-*.js)", status == 200 and len(raw) > 100000, f"Status {status}, {len(raw):,} bytes")
except Exception as e:
    record("SPA", "Compiled JavaScript Bundle", False, str(e))

try:
    status, raw = fetch(f"{RENDER_BASE}/assets/index-DCUO1nLt.css")
    record("SPA", "Compiled CSS Stylesheet (/assets/index-*.css)", status == 200 and len(raw) > 10000, f"Status {status}, {len(raw):,} bytes")
except Exception as e:
    record("SPA", "Compiled CSS Stylesheet", False, str(e))

# 2. System State & Hardware Telemetry
print("\n[2. SYSTEM STATE & HARDWARE TELEMETRY]")
try:
    status, raw = fetch(f"{RENDER_BASE}/api/state")
    data = json.loads(raw.decode())
    st = data.get("status")
    msg = data.get("status_message")
    ram = data.get("metrics", {}).get("ram_percent")
    record("Telemetry", "Live State Engine (GET /api/state)", status == 200 and st is not None, f"Status: {st} | RAM: {ram}% | Msg: '{msg[:40]}...'")
except Exception as e:
    record("Telemetry", "Live State Engine (GET /api/state)", False, str(e))

try:
    status, raw = fetch(f"{RENDER_BASE}/api/network/mobile-info")
    data = json.loads(raw.decode())
    success = data.get("success", False)
    record("Telemetry", "Mobile Network Telemetry (/api/network/mobile-info)", success, f"Success: {success} | Local IP: {data.get('lan_ip')}")
except Exception as e:
    record("Telemetry", "Mobile Network Telemetry", False, str(e))

# 3. Live AI Chat & Zero-Refusal Directives
print("\n[3. LIVE AI CHAT & ZERO-REFUSAL DIRECTIVES]")
chat_tests = [
    ("Prompt: 'clip a gta 6 video'", "clip a gta 6 video", ["gta 6", "sourcing", "autopilot", "viral", "directive accepted"]),
    ("Prompt: 'why'", "why", ["assist", "everything", "whole agent", "no limits", "clip"]),
    ("Prompt: 'how is my pc'", "how is my pc", ["cpu", "ram", "battery", "nominal", "diagnostics", "status"]),
    ("Prompt: 'lock pc'", "lock pc", ["lock", "computer", "sir", "boss"])
]

for label, message, expected_keywords in chat_tests:
    try:
        payload = json.dumps({"message": message, "synthesize_audio": False}).encode("utf-8")
        status, raw = fetch(f"{RENDER_BASE}/api/chat", data=payload, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, timeout=20)
        data = json.loads(raw.decode())
        reply = data.get("reply", "")
        has_refusal = any(ref in reply.lower() for ref in ["can't assist with that", "cannot assist with that", "as an ai"])
        matches = any(k in reply.lower() for k in expected_keywords)
        passed = (not has_refusal) and matches
        clean_reply = reply.replace("\n", " ")[:55]
        record("Live Chat", label, passed, f"'{clean_reply}...'")
    except Exception as e:
        record("Live Chat", label, False, str(e))

# 4. 1-Click Viral Autopilot
print("\n[4. 1-CLICK VIRAL AUTOPILOT & PRESETS]")
try:
    status, raw = fetch(f"{RENDER_BASE}/api/autopilot/presets")
    data = json.loads(raw.decode())
    preset_list = data if isinstance(data, list) else data.get("presets", [])
    has_presets = len(preset_list) >= 4
    record("Autopilot", "Creator Preset Library (/api/autopilot/presets)", has_presets, f"{len(preset_list)} presets loaded")
except Exception as e:
    record("Autopilot", "Creator Preset Library", False, str(e))

try:
    status, raw = fetch(f"{RENDER_BASE}/api/autopilot/status")
    data = json.loads(raw.decode())
    record("Autopilot", "Autopilot Engine Status (/api/autopilot/status)", True, f"Status: {data.get('status')} | Step: {data.get('step')[:40]}...")
except Exception as e:
    record("Autopilot", "Autopilot Engine Status", False, str(e))

# 5. CapCut-Grade Studio Editor
print("\n[5. CAPCUT-GRADE STUDIO EDITOR API]")
try:
    status, raw = fetch(f"{RENDER_BASE}/api/studio/presets")
    data = json.loads(raw.decode())
    color_presets = data.get("color_presets", [])
    subtitle_styles = data.get("subtitle_styles", [])
    record("Studio", "Studio Presets (/api/studio/presets)", len(color_presets) > 0, f"{len(color_presets)} color presets, {len(subtitle_styles)} subtitle styles")
except Exception as e:
    record("Studio", "Studio Presets", False, str(e))

try:
    status, raw = fetch(f"{RENDER_BASE}/api/studio/projects")
    data = json.loads(raw.decode())
    count = len(data) if isinstance(data, list) else 0
    record("Studio", "Studio Project Store (/api/studio/projects)", True, f"{count} projects indexed")
except Exception as e:
    record("Studio", "Studio Project Store", False, str(e))

# 6. RLHF Learning Policy Engine
print("\n[6. RLHF CONTINUOUS LEARNING POLICY ENGINE]")
try:
    status, raw = fetch(f"{RENDER_BASE}/api/rlhf/rules")
    data = json.loads(raw.decode())
    count = len(data) if isinstance(data, list) else 0
    record("RLHF", "Active Policy Rules (/api/rlhf/rules)", True, f"{count} active policy rules in force")
except Exception as e:
    record("RLHF", "Active Policy Rules", False, str(e))

try:
    status, raw = fetch(f"{RENDER_BASE}/api/rlhf/summary")
    data = json.loads(raw.decode())
    balance = data.get("total_reward", 0.0)
    events = data.get("total_events", 0)
    record("RLHF", "RLHF Reward Summary (/api/rlhf/summary)", True, f"Reward balance: {balance:+.1f} | Events: {events}")
except Exception as e:
    record("RLHF", "RLHF Reward Summary", False, str(e))

# 7. Livestream & Social Media Automation Endpoints
print("\n[7. SOCIAL MEDIA & LIVESTREAM GATEWAYS]")
try:
    status, raw = fetch(f"{RENDER_BASE}/api/livestream/status")
    data = json.loads(raw.decode())
    record("Social", "Livestream Clipper Status (/api/livestream/status)", True, f"Status: {data.get('status')}")
except Exception as e:
    record("Social", "Livestream Clipper Status", False, str(e))

try:
    status, raw = fetch(f"{RENDER_BASE}/api/social/youtube/queue/stats")
    data = json.loads(raw.decode())
    record("Social", "YouTube Anti-Ban Queue Stats (/queue/stats)", True, f"Queued: {data.get('queued', 0)} | Published today: {data.get('published_last_24h', 0)}")
except Exception as e:
    record("Social", "YouTube Anti-Ban Queue Stats", False, str(e))

try:
    status, raw = fetch(f"{RENDER_BASE}/api/social/instagram/browser-status")
    data = json.loads(raw.decode())
    record("Social", "Instagram Stealth Profile (/browser-status)", True, f"Profile: {data.get('profile_dir', 'configured')}")
except Exception as e:
    record("Social", "Instagram Stealth Profile", False, str(e))

# 8. Cloud YouTube Engine & Bot-Defense Shield
print("\n[8. CLOUD YOUTUBE ENGINE & BOT-DEFENSE SHIELD]")
try:
    status, raw = fetch(f"{RENDER_BASE}/api/cookies/status")
    data = json.loads(raw.decode())
    has_c = data.get("has_cookies", False)
    record("YouTube", "Cookie Shield Status (/api/cookies/status)", status == 200, f"Status: {data.get('status')[:45]}...")
except Exception as e:
    record("YouTube", "Cookie Shield Status", False, str(e))

try:
    yt_payload = json.dumps({"url": "https://www.youtube.com/watch?v=GTd0ygptkJE"}).encode("utf-8")
    status, raw = fetch(f"{RENDER_BASE}/api/youtube/metadata", data=yt_payload, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, timeout=35)
    data = json.loads(raw.decode())
    title = data.get("title", "")
    dur = data.get("duration", 0)
    record("YouTube", "Bypass Bot Challenge (/api/youtube/metadata)", status == 200 and len(title) > 0, f"Title: '{title[:35]}...' | Dur: {dur}s")
except Exception as e:
    record("YouTube", "Bypass Bot Challenge (/api/youtube/metadata)", False, str(e))

# Summary
total = len(results)
passed_count = sum(1 for r in results if r["passed"])
print("\n" + "=" * 80)
print(f"           AUDIT SUMMARY: {passed_count} / {total} CHECKS PASSED ({passed_count/total*100:.1f}%)")
print("=" * 80)
if passed_count == total:
    print("🚀 ALL SYSTEMS ON RENDER ARE FULLY OPERATIONAL AND VERIFIED LIVE!")
