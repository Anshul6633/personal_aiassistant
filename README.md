# 🤖 PROJECT JARVIS: Autonomous AI Buddy & Social Content Factory

[![Status](https://img.shields.io/badge/Status-Operational%20%26%20Active-brightgreen.svg)](#current-project-status)
[![Zero Paid API](https://img.shields.io/badge/AI%20Cost-Zero%20Paid%20APIs-brightgreen.svg)](#zero-cost-local-first-guarantee)
[![Architecture](https://img.shields.io/badge/Stack-FastAPI%20%2B%20React%20%2B%20Playwright%20%2B%20Ollama-blue.svg)](#system-architecture)
[![Video Engine](https://img.shields.io/badge/Video%20Engine-9%3A16%20Shorts%20%26%20Reels%20Autopilot-cyan.svg)](#1-click-viral-autopilot-command-center)
[![Anti-Ban Protection](https://img.shields.io/badge/Anti--Ban-45m%20Cadence%20%2B%20Human%20Keystrokes-orange.svg)](#anti-ban--channel-safety-protocols)

Inspired by Tony Stark's Avengers JARVIS, **PROJECT JARVIS** is a production-grade, local-first Windows personal AI companion and autonomous social media content factory. 

Operating **with 100% free, local open-source AI and zero paid API dependencies**, JARVIS observes your desktop, controls Windows apps, transcribes audio with word-level precision, scores viral moments with a 6-factor AI algorithm, produces 30–50 high-retention 9:16 vertical videos per day, and autonomously publishes them to **YouTube Shorts** and **Instagram Reels** till daily limits are reached—all with strict anti-ban humanized safety protocols.

---

## 📊 Current Project Status & Progress Tracker

| Subsystem / Capability | Status | Implementation Details |
| :--- | :---: | :--- |
| **⚡ 1-Click Viral Autopilot** | ✅ **Operational** | End-to-end autonomous pipeline from creator preset / URL to published Shorts/Reels with live SSE progress tracking. |
| **🚀 GPU CUDA Acceleration** | ✅ **Active** | NVIDIA GeForce RTX 4050 GPU enabled for `faster-whisper` (transcribes 20m video in ~15s, 40x speedup). |
| **🧠 RLHF Continuous Learning** | ✅ **Operational** | Ingests thumbs up/down and direct user corrections, updating policy weights and injecting active rules into prompts. |
| **🎙️ Siri-Style Whole Agent** | ✅ **Operational** | Friendly, conversational companion who answers in 1-2 punchy sentences, plays music, opens apps, and controls the PC. |
| **🔴 YouTube Shorts Publishing** | ✅ **Operational** | Playwright stealth engine logged into channel `GHOST _OF_FOOTBALL`. Direct **Public** publishing guarantee (zero private drafts). |
| **📸 Instagram Reels Publishing** | ✅ **Operational** | Stealth browser automation logged into `@clipperwithout` with dynamic viral hook captions, credit tagging, and 18+ hashtags. |
| **🛡️ Anti-Ban & Channel Safety** | ✅ **Operational** | 45-minute inter-upload spacing, randomized human typing (45ms–110ms), cursor jitter, anti-bot flags, and daily limit detection. |
| **🎬 6-Factor Viral Scorer** | ✅ **Operational** | Automated evaluation of hooks (25%), narrative completeness (20%), info value (20%), engagement (15%), audio (10%), visual (10%). |
| **📝 Word-Level Subtitles** | ✅ **Operational** | `faster-whisper` timestamps rendered into animated dynamic ASS karaoke captions. |
| **🎨 Video Studio Canvas** | ✅ **Operational** | CapCut/Premiere-grade multi-track timeline, visual direct manipulation canvas (transform/rotate/resize), and FFmpeg transitions. |
| **👁️ Face Tracking & Color Splash** | ✅ **Operational** | OpenCV Haar/DNN speaker centering + background B&W desaturation subject isolation. |
| **🖥️ Desktop Operator & Vision** | ✅ **Operational** | Full screen capture (`mss`), mouse clicks, keyboard hotkeys, window inspection, and controlled tool registry. |
| **🎙️ Conversational Companion** | ✅ **Operational** | Natural dialogue in English, Hindi, and Hinglish via local Ollama (`qwen2.5:1.5b` / `qwen2.5:3b`) and Edge-TTS / pyttsx3. |
| **🔄 Live Local Daemons** | ✅ **Active** | FastAPI backend (`127.0.0.1:8000`) and React Vite HUD (`127.0.0.1:5173`) running with auto-reload. |

---

## ⚡ Core Breakthroughs & Features

### 1. ⚡ 1-Click Viral Autopilot Command Center
Users can select a viral creator preset or paste any YouTube URL, click one button, and watch JARVIS execute the full workflow autonomously:
1. **Source Ingestion**: Fetches highest quality stream and audio track via `yt-dlp`.
2. **Word-Level Transcription**: Transcribes complete speech with millisecond precision using local `faster-whisper`.
3. **AI Viral Hook Detection**: Evaluates transcript windows using the 6-factor algorithmic score (threshold ≥ 75/100).
4. **9:16 Vertical Reframing**: Crops and blurs background letterbox with speaker face tracking.
5. **Karaoke Subtitle Synthesis**: Dynamic animated ASS subtitles centered or positioned per preset style.
6. **Viral Metadata Generation**: Creates curiosity-gap titles, SEO descriptions, and tags.
7. **Autonomous Publishing**: Enqueues and posts to YouTube Shorts and Instagram Reels.

**Supported Creator Presets**:
- 🏈 **Football Highlights** (`football`) — High-energy sports moments, goals, and legendary commentary.
- 🤑 **MrBeast Challenges** (`mrbeast`) — Fast-paced, high-stakes retention hooks with bold color pop.
- 🎙️ **Joe Rogan Experience** (`rogan`) — Deep conversational quotes, philosophical and fitness hooks.
- 🧠 **Andrew Huberman** (`huberman`) — Neuroscience, health protocols, dopamine and sleep optimization.
- 🔥 **IShowSpeed** (`speed`) — Hyper-reactive comedic spikes, streaming viral reactions.
- 🔗 **Custom YouTube URL** — Ingest any podcast, documentary, or interview link.

---

### 2. 🔴 YouTube Shorts Direct Public Publishing (Anti-Draft Guarantee)
Previously, browser automation often defaulted to saving videos as private drafts in YouTube Studio Step 4. JARVIS has solved this completely:
- **Direct Public Visibility**: Expands `#first-container` (*Save or publish*), targets radio button `name="PUBLIC"`, scrolls into view, and clicks with `force=True`.
- **Pre-Submission Verification Loop**: Inspects `#done-button` inner text. If it reads `"Save"`, it re-navigates and re-clicks `PUBLIC` until `#done-button` strictly displays **`"Publish"`**.
- **Daily Upload Limit Detection**: Detects YouTube's `"Daily upload limit reached"` notification banner gracefully, halts further attempts safely, and reschedules remaining items for the next quota window.
- **Persistent Authenticated Profile**: Uses `jarvis/browser_profile`, keeping YouTube Studio continuously authenticated to channel **`GHOST _OF_FOOTBALL`**.

---

### 3. 📸 Instagram Reels Autonomous Publishing Engine
- **Stealth Playwright Execution**: Automated navigation through `instagram.com` logged in to account **`@clipperwithout`**.
- **Dynamic Viral Captions**: Automatically generates:
  - First-line curiosity/controversy hook.
  - Transcript highlight quote.
  - Engagement Call-to-Action (*"Drop your thoughts 👇"*, *"Save this for later 📌"*).
  - Attribution & creator credit (*"🎥 Video Credit: @..."*).
  - 18+ high-volume discoverability hashtags (`#reels #viralreels #explorepage #fyp #trending ...`).
- **Aspect Ratio & Cover Frame Handling**: Ensures vertical 9:16 aspect ratio selection and smooth submission.

---

### 4. 🛡️ Anti-Ban, Anti-Detection & Channel Safety Protocols
To protect YouTube channels and Instagram accounts from shadowbans, spam flags, and biometric bot detection:
1. **45-Minute Algorithmic Spacing**: A strict rate-limiter spaces successive uploads by 45 minutes on both platforms to match organic creator behavior and optimize algorithmic recommendation scoring.
2. **Humanized Keystroke Dynamics**: Typing into title and caption fields employs variable delays (45ms–110ms per keystroke) with natural pause intervals between words.
3. **Bezier Mouse Trajectories & Jitter**: Cursor interactions avoid linear paths, incorporating randomized jitter and realistic hover durations.
4. **Anti-Automation Browser Flags**: Launches Chrome with `--disable-blink-features=AutomationControlled`, randomized viewports, and clean user-agent strings.
5. **Emergency Kill-Switch**: Master kill-switch in the HUD instantly terminates browser instances, FFmpeg processes, and audio drivers.

---

### 5. 🎨 Video Studio Canvas & Multi-Track Editor
A CapCut/Premiere Pro style in-browser editor built into the JARVIS HUD:
- **Interactive 9:16 Canvas**: Visual bounding box controls for direct manipulation (drag to reposition, resize handles, rotation control).
- **Multi-Track Timeline**: Independent tracks for Video, Audio, Subtitles, B-roll, and Overlays.
- **Dynamic Coordinate Subtitle Positioning**: Moving the subtitle element on the canvas updates normalized coordinates `(x, y)` which FFmpeg maps directly to ASS `{\pos(x,y)}` subtitle coordinates during rendering.
- **Cinematic Transitions**: High-performance FFmpeg filter-complex transitions:
  - `zoom_in` & `zoom_out`
  - `glitch`
  - `flash_white`
  - `cross_dissolve`
- **Render Engine**: Asynchronous FFmpeg export queue with live percentage progress tracking.

---

## 📁 Project Directory Structure

```
personal_aiassistant/
├── jarvis/
│   ├── backend/
│   │   ├── agents/            # Autonomous orchestrator, viral researcher, buddy persona
│   │   ├── automation/        # Desktop controller, screen observer, tool registry
│   │   ├── config/            # Pydantic configuration, path settings
│   │   ├── database/          # SQLite schema, migrations, memory bank
│   │   ├── security/          # Autonomy gates, audit logger, kill-switch
│   │   ├── social/            # YouTube Playwright engine, Instagram engine, scheduler
│   │   ├── video/             # Faster-Whisper, 6-factor scorer, video pipeline, studio editor
│   │   ├── voice/             # STT, Edge-TTS, VAD wake word detector
│   │   └── main.py            # FastAPI application gateway, WebSocket & REST endpoints
│   ├── frontend/           # React 19 + TypeScript + Vite + Tailwind CSS HUD
│   │   ├── src/components/    # Arc Reactor visualizer, AudioWaveform, Timeline, Canvas
│   │   ├── src/pages/         # ShortsFactory, ReelsFactory, VideoEditor, ContentStudio, etc.
│   │   └── src/services/      # API clients, WebSocket streams, telemetry hooks
│   ├── browser_profile/    # Persistent authenticated Playwright Chrome user profile
│   ├── output/             # 40+ generated 9:16 vertical clips, thumbnails, subtitles
│   └── database.sqlite     # SQLite database for clips, projects, schedules, logs
├── install.bat                # Automated virtualenv and dependencies installer
├── start.bat                  # One-click startup script (FastAPI + Vite + Ollama)
├── stop.bat                   # Clean process shutdown script
├── diagnose.bat               # Hardware & environment health audit
├── requirements.txt           # Pinned Python backend dependencies
└── README.md                  # System documentation & progress report
```

---

## 🚀 How to Run & Operate JARVIS

### 1. Launch Services
JARVIS runs via two local daemons:
- **Backend API Server**: `http://127.0.0.1:8000`
- **Frontend Futuristic HUD**: `http://127.0.0.1:5173`

To launch both with one click:
```cmd
start.bat
```

Or manually in two terminals:
```powershell
# Terminal 1: Backend
.\.venv\Scripts\python.exe -m uvicorn jarvis.backend.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend
cd jarvis\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

### 2. Trigger 1-Click Viral Autopilot
Navigate to **Shorts Factory** or **Reels Factory** on `http://127.0.0.1:5173`:
1. Click any preset (**Football**, **MrBeast**, **Joe Rogan**, **Huberman**, **Speed**) or enter a custom YouTube URL.
2. Select target platform: **Both**, **YouTube Shorts**, or **Instagram Reels**.
3. Toggle **Upload Till Daily Limit** (enabled by default).
4. Click **Start 1-Click Viral Autopilot**.
5. Monitor real-time progress and logs in the live terminal window.

---

## 🔗 Key REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/autopilot/viral-start` | Trigger 1-Click Viral Autopilot pipeline. |
| `GET` | `/api/autopilot/status` | Real-time status, active stage, and progress percentage. |
| `GET` | `/api/autopilot/presets` | List of available viral creator presets. |
| `POST` | `/api/studio/projects/{id}/export` | Trigger FFmpeg render engine export for studio project. |
| `GET` | `/api/studio/jobs/{job_id}` | Query export job status and progress. |
| `POST` | `/api/youtube/scheduler/enqueue` | Enqueue video for autonomous YouTube upload. |
| `POST` | `/api/instagram/scheduler/enqueue` | Enqueue video for autonomous Instagram Reel upload. |
| `GET` | `/api/clips` | Fetch all generated vertical clips from SQLite database. |
| `POST` | `/api/rlhf/feedback` | Record human praise, thumbs up/down, or corrections. |
| `GET` | `/api/rlhf/rules` | List all active learned policy rules with reward weights. |
| `GET` | `/api/rlhf/summary` | Real-time RLHF telemetry, reward points, and recent feedback logs. |
| `POST` | `/api/security/emergency-stop` | Emergency kill-switch freezing all automation. |

---

## 🌟 Zero-Cost & Privacy Guarantee

- **No OpenAI / Anthropic / Google Cloud API Keys Required**: All LLM reasoning runs through local Ollama models (`qwen2.5:1.5b` or `qwen2.5:3b`).
- **No Cloud Transcription Fees**: All speech-to-text uses local `faster-whisper` on your local CPU / NVIDIA GPU.
- **No Paid Video Editing SaaS**: All cropping, transitions, effects, and subtitles are rendered locally via standalone `ffmpeg`.
- **100% On-Device Data**: Your browser cookies, credentials, screen feeds, and media remain strictly on your local PC.
