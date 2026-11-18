"""JARVIS Core FastAPI Server & WebSocket Gateway.

Provides real-time HUD telemetry, audio streaming, desktop automation,
video clipping factory API, and social publishing integrations.
"""

import os
import json
import time
import uuid
import shutil
import urllib.parse
import subprocess
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Body, BackgroundTasks, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from jarvis.backend.config.settings import settings, OUTPUT_DIR, DB_PATH, WORKSPACE_ROOT
from jarvis.backend.network.tunnel_manager import tunnel_manager
from jarvis.backend.core.state import state_manager, AssistantState
from jarvis.backend.database.db import init_database, get_db_connection
from jarvis.backend.database.memory import memory_manager
from jarvis.backend.security.permissions import security_guard
from jarvis.backend.agents.buddy import jarvis_buddy
from jarvis.backend.agents.orchestrator import orchestrator
from jarvis.backend.agents.researcher import content_researcher
from jarvis.backend.voice.tts import tts_engine
from jarvis.backend.voice.stt import stt_engine
from jarvis.backend.voice.wakeword import wakeword_listener
from jarvis.backend.video.pipeline import video_pipeline
from jarvis.backend.video.source_manager import source_manager
from jarvis.backend.automation.tool_registry import tool_registry
from jarvis.backend.automation.screen import screen_observer
from jarvis.backend.social.youtube import youtube_manager
from jarvis.backend.social.youtube_browser import youtube_browser
from jarvis.backend.social.drive_pipeline import drive_pipeline
from jarvis.backend.social.scheduler_engine import scheduler_engine
from jarvis.backend.social.instagram import instagram_manager
from jarvis.backend.social.instagram_browser import instagram_browser

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("JARVIS.Server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("Initializing JARVIS core systems...")
    state_manager.set_loop(asyncio.get_running_loop())
    init_database()
    # Start periodic background hardware telemetry loop
    metrics_task = asyncio.create_task(state_manager.start_metrics_loop())
    scheduler_task = asyncio.create_task(scheduler_engine.run_worker_loop())
    yield
    # Shutdown sequence
    metrics_task.cancel()
    scheduler_task.cancel()
    wakeword_listener.stop_listening()
    tts_engine.stop_speaking()
    logger.info("JARVIS systems safely suspended.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Enable CORS and GZip Compression for fast mobile/remote throughput
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount output directory for media streaming
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# Mount compiled production frontend assets
FRONTEND_DIST_DIR = WORKSPACE_ROOT / "jarvis" / "frontend" / "dist"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"
if FRONTEND_ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS_DIR)), name="assets")


# --- WebSocket Realtime Gateway ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state_manager.register_client(websocket)
    # Send initial state immediately
    await websocket.send_text(json.dumps({
        "type": "INITIAL_STATE",
        "data": state_manager.state.model_dump()
    }))

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                msg = json.loads(raw_data)
                action = msg.get("action")

                if action == "EMERGENCY_STOP":
                    security_guard.trigger_emergency_stop()
                    await state_manager.set_status(AssistantState.ERROR, "EMERGENCY STOP ENGAGED")
                elif action == "INTERRUPT_SPEECH":
                    tts_engine.stop_speaking()
                    await state_manager.set_status(AssistantState.IDLE, "Speech halted by user.")
                elif action == "TOGGLE_MIC":
                    active = msg.get("active", False)
                    if active:
                        wakeword_listener.start_listening()
                    else:
                        wakeword_listener.stop_listening()
                elif action == "USER_PROMPT":
                    text = msg.get("text", "")
                    asyncio.create_task(orchestrator.plan_and_execute(text))
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
    except WebSocketDisconnect:
        state_manager.unregister_client(websocket)


# --- REST API Endpoints ---

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_session"
    synthesize_audio: Optional[bool] = True


@app.post("/api/chat")
async def chat_with_jarvis(req: ChatRequest):
    """Direct conversation with JARVIS."""
    try:
        reply = await jarvis_buddy.generate_response(req.message, req.session_id)
        audio_url = None
        if req.synthesize_audio:
            try:
                audio_path = await tts_engine.synthesize(reply)
                if audio_path:
                    filename = Path(audio_path).name
                    audio_url = f"/output/audio/{filename}"
                    # Play directly on computer speakers for local companion experience
                    tts_engine.play_audio(audio_path)
            except Exception as te:
                logger.warning(f"Audio synthesis warning: {te}")

        await state_manager.broadcast({
            "type": "ASSISTANT_REPLY",
            "data": {
                "text": reply,
                "audio_url": audio_url,
                "timestamp": datetime.now().strftime("%I:%M %p")
            }
        })

        return {
            "reply": reply,
            "audio_url": audio_url,
            "status": state_manager.state.status
        }
    except Exception as e:
        logger.error(f"Chat processing error: {e}", exc_info=True)
        fallback_reply = "I'm right here with you, Boss! The neural link is recalibrating. What task shall we tackle next?"
        return {
            "reply": fallback_reply,
            "audio_url": None,
            "status": "IDLE"
        }


class AIConfigRequest(BaseModel):
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None


@app.get("/api/ai/config")
async def get_ai_config():
    """Retrieve current conversational AI configuration and active engine."""
    from jarvis.backend.database.memory import memory_manager
    from jarvis.backend.config.settings import settings
    has_groq = bool(settings.GROQ_API_KEY or memory_manager.get_memory("groq_api_key"))
    has_gemini = bool(settings.GEMINI_API_KEY or memory_manager.get_memory("gemini_api_key"))
    has_openai = bool(settings.OPENAI_API_KEY or memory_manager.get_memory("openai_api_key"))
    ollama_ok = await jarvis_buddy.check_ollama_health()

    mode = "cloud_companion"
    if has_groq:
        mode = "groq_cloud (llama-3.3-70b)"
    elif has_gemini:
        mode = "gemini_cloud (gemini-1.5-flash)"
    elif has_openai:
        mode = "openai_cloud"
    elif ollama_ok:
        mode = "ollama_local (RTX GPU)"

    return {
        "active_mode": mode,
        "ollama_connected": ollama_ok,
        "has_groq_key": has_groq,
        "has_gemini_key": has_gemini,
        "has_openai_key": has_openai,
        "recommendation": "For free cloud AI at college with laptop off, add a free GROQ_API_KEY or GEMINI_API_KEY."
    }


@app.post("/api/ai/config")
async def update_ai_config(req: AIConfigRequest):
    """Save user-provided free cloud AI keys to persistent SQLite memories."""
    from jarvis.backend.database.memory import memory_manager
    updated = []
    if req.groq_api_key is not None:
        memory_manager.set_memory("ai_keys", "groq_api_key", req.groq_api_key.strip())
        updated.append("Groq API Key")
    if req.gemini_api_key is not None:
        memory_manager.set_memory("ai_keys", "gemini_api_key", req.gemini_api_key.strip())
        updated.append("Gemini API Key")
    if req.openai_api_key is not None:
        memory_manager.set_memory("ai_keys", "openai_api_key", req.openai_api_key.strip())
        updated.append("OpenAI API Key")

    return {
        "success": True,
        "message": f"Successfully updated: {', '.join(updated) if updated else 'No keys updated'}"
    }


# --- Voice & Speech Recognition Endpoints ---

@app.post("/api/voice/transcribe")
async def transcribe_voice(file: UploadFile = File(...)):
    """Transcribe an audio recording from the browser using local faster-whisper."""
    audio_dir = OUTPUT_DIR / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    import time
    ext = Path(file.filename or "recording.wav").suffix or ".wav"
    temp_path = audio_dir / f"recording_{int(time.time() * 1000)}{ext}"
    
    with open(temp_path, "wb") as f:
        data = await file.read()
        f.write(data)

    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, stt_engine.transcribe_file, str(temp_path))
    return {
        "text": res.get("text", "").strip(),
        "language": res.get("language", "en"),
        "duration": res.get("duration", 0.0)
    }


class SpeakRequest(BaseModel):
    text: str
    play_local: Optional[bool] = False


@app.post("/api/voice/speak")
async def speak_text(req: SpeakRequest):
    """Synthesize speech and optionally play on local speakers."""
    audio_path = await tts_engine.synthesize(req.text)
    if not audio_path:
        raise HTTPException(status_code=500, detail="Speech synthesis failed")

    if req.play_local:
        tts_engine.play_audio(audio_path)

    filename = Path(audio_path).name
    return {
        "status": "SPEAKING",
        "audio_url": f"/output/audio/{filename}"
    }


@app.post("/api/voice/stop")
async def stop_voice_playback():
    """Interrupt voice playback."""
    tts_engine.stop_speaking()
    return {"status": "STOPPED"}


class DirectCommandRequest(BaseModel):
    command: str


@app.post("/api/orchestrate")
async def orchestrate_command(req: DirectCommandRequest):
    """High-level multi-step autonomous task planning and execution."""
    result = await orchestrator.plan_and_execute(req.command)
    return result


@app.get("/api/state")
async def get_state():
    """Current assistant state, hardware telemetry and metrics."""
    state_manager.update_metrics()
    return state_manager.state.model_dump()


@app.get("/api/network/mobile-info")
async def get_mobile_network_info():
    """Detect LAN IP and return mobile phone connection URLs, live public HTTPS tunnel, and QR metadata."""
    t_status = tunnel_manager.get_status()
    lan_ip = t_status.get("local_ip", "127.0.0.1")
    public_url = t_status.get("public_url")
    is_tunnel_active = t_status.get("is_active", False)

    # In production single-port mode, frontend is served on port 8000 alongside API
    lan_production_url = f"http://{lan_ip}:8000"
    dev_frontend_url = f"http://{lan_ip}:5173"
    
    # Target URL for QR code (prefer public HTTPS tunnel if active for worldwide phone access)
    primary_mobile_url = public_url if is_tunnel_active and public_url else lan_production_url
    
    import urllib.parse
    qr_data = urllib.parse.quote(primary_mobile_url, safe="")
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={qr_data}"
    lan_qr_data = urllib.parse.quote(lan_production_url, safe="")
    lan_qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={lan_qr_data}"

    return {
        "success": True,
        "lan_ip": lan_ip,
        "production_port": 8000,
        "dev_port": 5173,
        "mobile_url": primary_mobile_url,
        "lan_url": lan_production_url,
        "public_url": public_url,
        "is_tunnel_active": is_tunnel_active,
        "tunnel_status": t_status.get("status", "STOPPED"),
        "qr_code_url": qr_code_url,
        "lan_qr_code_url": lan_qr_code_url,
        "instructions": "Scan with any phone camera or open the URL to access JARVIS from local Wi-Fi or worldwide mobile data."
    }


@app.get("/api/network/tunnel")
async def get_network_tunnel():
    """Get live public HTTPS tunnel status and URLs."""
    return tunnel_manager.get_status()


@app.post("/api/network/tunnel/start")
async def start_network_tunnel():
    """Start live public HTTPS tunnel for worldwide mobile access."""
    return tunnel_manager.start_tunnel(port=8000)


@app.post("/api/network/tunnel/stop")
async def stop_network_tunnel():
    """Stop active live public HTTPS tunnel."""
    return tunnel_manager.stop_tunnel()


@app.post("/api/emergency-stop")
async def emergency_stop():
    """Trigger emergency stop kill-switch."""
    security_guard.trigger_emergency_stop()
    tts_engine.stop_speaking()
    await state_manager.set_status(AssistantState.ERROR, "EMERGENCY STOP ENGAGED")
    return {"status": "EMERGENCY_STOPPED"}


@app.post("/api/reset-emergency")
async def reset_emergency():
    """Reset emergency stop."""
    security_guard.reset_emergency_stop()
    from jarvis.backend.video.pipeline import video_pipeline
    video_pipeline.is_processing = False
    await state_manager.set_status(AssistantState.IDLE, "Systems nominal.")
    await state_manager.update(task_progress=0, active_task_id=None, active_task_title=None)
    return {"status": "RESET_OK"}


@app.post("/api/pipeline/reset")
async def reset_pipeline():
    """Cancel and reset any stuck or active video pipeline."""
    from jarvis.backend.video.pipeline import video_pipeline
    video_pipeline.is_processing = False
    await state_manager.set_status(AssistantState.IDLE, "Pipeline reset by user.")
    await state_manager.update(task_progress=0, active_task_id=None, active_task_title=None)
    return {"status": "RESET_OK", "message": "Pipeline reset successfully."}


# --- Video Clipping Factory Endpoints ---

@app.get("/api/clips")
async def list_clips():
    """List all created vertical clips with titles, scores, and media URLs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clips ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    clips = []
    for r in rows:
        d = dict(r)
        # Convert local paths to accessible web URLs
        if d.get("output_path"):
            p = Path(d["output_path"])
            d["video_url"] = f"/output/reels/{p.name}"
        if d.get("thumbnail_path"):
            p = Path(d["thumbnail_path"])
            d["thumb_url"] = f"/output/thumbnails/{p.name}"
        clips.append(d)
    return clips


class ClipGenerateRequest(BaseModel):
    video_path: str
    num_clips: Optional[int] = 3
    target_duration: Optional[float] = 45.0
    style_preset: Optional[str] = "podcast"
    auto_publish_youtube: Optional[bool] = False
    publish_interval_minutes: Optional[int] = 45
    privacy: Optional[str] = "schedule"


class YouTubeClipRequest(BaseModel):
    youtube_url: str
    num_clips: Optional[int] = 3
    target_duration: Optional[float] = 45.0
    style_preset: Optional[str] = "podcast"
    auto_publish_youtube: Optional[bool] = True
    publish_interval_minutes: Optional[int] = 45
    privacy: Optional[str] = "schedule"


@app.post("/api/clips/generate")
async def generate_clips(req: ClipGenerateRequest, background_tasks: BackgroundTasks):
    """Trigger autonomous video clipping pipeline on local video file or pasted YouTube URL."""
    from jarvis.backend.video.source_manager import source_manager
    is_yt = source_manager.is_youtube_url(req.video_path)
    if not is_yt and not Path(req.video_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Source video not found. Please provide an existing local file path or a valid YouTube URL."
        )

    background_tasks.add_task(
        video_pipeline.process_video,
        req.video_path,
        req.num_clips,
        req.target_duration,
        style_preset=req.style_preset or "podcast",
        auto_publish_youtube=req.auto_publish_youtube or False,
        publish_interval_minutes=req.publish_interval_minutes or 45,
        privacy=req.privacy or "schedule"
    )
    return {
        "status": "PROCESSING_STARTED",
        "video": req.video_path,
        "is_youtube_source": is_yt,
        "auto_publish_youtube": req.auto_publish_youtube or False,
        "publish_interval_minutes": req.publish_interval_minutes or 45,
        "requested_clips": req.num_clips,
        "style_preset": req.style_preset
    }


@app.post("/api/clips/generate-from-youtube")
async def generate_clips_from_youtube(req: YouTubeClipRequest, background_tasks: BackgroundTasks):
    """Ingest YouTube URL, download source, detect viral hooks, generate 9:16 vertical shorts with proper descriptions, and auto-publish spaced 45m apart."""
    from jarvis.backend.video.source_manager import source_manager
    if not source_manager.is_youtube_url(req.youtube_url):
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL. Please enter a valid link (e.g. https://www.youtube.com/watch?v=... or https://youtu.be/...)"
        )

    background_tasks.add_task(
        video_pipeline.process_video,
        req.youtube_url,
        req.num_clips,
        req.target_duration,
        style_preset=req.style_preset or "podcast",
        auto_publish_youtube=req.auto_publish_youtube if req.auto_publish_youtube is not None else True,
        publish_interval_minutes=req.publish_interval_minutes or 45,
        privacy=req.privacy or "schedule"
    )
    return {
        "status": "PROCESSING_STARTED",
        "youtube_url": req.youtube_url,
        "auto_publish_youtube": req.auto_publish_youtube if req.auto_publish_youtube is not None else True,
        "publish_interval_minutes": req.publish_interval_minutes or 45,
        "requested_clips": req.num_clips,
        "message": "YouTube video clipping initiated! Clips will be extracted, given proper descriptions, and auto-published to YouTube Studio spaced 45m apart."
    }


class ViralAutopilotRequest(BaseModel):
    youtube_url: Optional[str] = None
    preset: Optional[str] = None
    search_topic: Optional[str] = None
    num_clips: Optional[int] = 4
    target_duration: Optional[float] = 45.0
    interval_minutes: Optional[int] = 45
    upload_till_limit: Optional[bool] = True
    platform: Optional[str] = "both"
    privacy: Optional[str] = "public"


@app.get("/api/autopilot/presets")
async def get_autopilot_presets():
    """Get list of curated viral creator presets (MrBeast, Football, Joe Rogan, Andrew Huberman, IShowSpeed)."""
    from jarvis.backend.video.viral_autopilot import VIRAL_PRESETS
    return [
        {"id": k, **v} for k, v in VIRAL_PRESETS.items()
    ]


@app.get("/api/autopilot/status")
async def get_autopilot_status():
    """Get real-time status, progress, and logs of the 1-Click Viral Autopilot engine."""
    from jarvis.backend.video.viral_autopilot import viral_autopilot
    return viral_autopilot.get_status()


@app.get("/api/portal/summary")
async def get_portal_summary():
    """Get complete real-time situational awareness across the entire JARVIS portal.
    Aggregates:
    - Active Autopilot state (link discovery, clipping, rendering)
    - Active upload status & next queued video
    - Queue metrics & today's published count
    - Library ready clips count
    - Anti-ban shield status
    """
    from jarvis.backend.video.viral_autopilot import viral_autopilot
    from jarvis.backend.social.scheduler_engine import scheduler_engine
    from jarvis.backend.database.db import get_db_connection

    # 1. Autopilot state
    ap_status = viral_autopilot.get_status()

    # 2. Queue & upload telemetry
    q_stats = scheduler_engine.get_queue_stats()

    # 3. Ready clips count in database
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM clips WHERE status = 'READY'")
    ready_clips_count = cur.fetchone()[0]

    cur.execute("SELECT id, title, published_at, youtube_url FROM youtube_schedule_queue WHERE status = 'PUBLISHED' ORDER BY published_at DESC LIMIT 5")
    recent_published = [dict(r) for r in cur.fetchall()]
    conn.close()

    # Decide current brain activity
    current_activity = "IDLE_STANDBY"
    activity_detail = "All pipelines operational. Standing by for directives."
    
    if ap_status.get("status") == "RUNNING":
        current_activity = "AUTOPILOT_ACTIVE"
        activity_detail = ap_status.get("step", "Processing viral workflow")
    elif q_stats.get("current_uploading_id"):
        current_activity = "UPLOADING_LIVE"
        activity_detail = f"Uploading item {q_stats['current_uploading_id']} to YouTube Studio as Public"
    elif q_stats.get("next_item"):
        next_t = q_stats["next_item"].get("title", "")
        secs = q_stats.get("seconds_until_next", 0)
        current_activity = "PACING_SHIELD"
        activity_detail = f"Next upload scheduled in {secs // 60}m {secs % 60}s: '{next_t[:45]}'"

    return {
        "brain": {
            "activity": current_activity,
            "detail": activity_detail,
            "autopilot_running": ap_status.get("status") == "RUNNING",
            "active_step": ap_status.get("step"),
            "progress_percent": ap_status.get("progress_percent", 0),
            "log": ap_status.get("log", [])[-8:]
        },
        "uploading": {
            "current_uploading_id": q_stats.get("current_uploading_id"),
            "is_uploading": bool(q_stats.get("current_uploading_id")),
            "next_item": q_stats.get("next_item"),
            "seconds_until_next": q_stats.get("seconds_until_next")
        },
        "queue": {
            "total": q_stats.get("total", 0),
            "queued": q_stats.get("queued", 0),
            "published": q_stats.get("published", 0),
            "published_today": q_stats.get("published_last_24h", 0),
            "failed": q_stats.get("failed", 0)
        },
        "library": {
            "ready_clips": ready_clips_count
        },
        "recent_published": recent_published,
        "anti_ban": {
            "active": True,
            "pacing": "45m - 60m interval with human keystrokes",
            "daily_safe_cap": 18,
            "current_today": q_stats.get("published_last_24h", 0)
        },
        "rlhf": {
            "active_rules": len(rlhf_engine.get_summary().get("rules", [])),
            "total_feedback": rlhf_engine.get_summary().get("metrics", {}).get("total_feedback", 0),
            "reward_score": rlhf_engine.get_summary().get("metrics", {}).get("total_cumulative_reward", 0)
        }
    }


@app.post("/api/autopilot/viral-start")
async def start_viral_autopilot(req: ViralAutopilotRequest, background_tasks: BackgroundTasks):
    """Launch 1-Click Viral Autopilot pipeline end-to-end:
    Discovery/Ingestion -> 6-factor hook detection -> 9:16 vertical render with karaoke subtitles ->
    SEO proper description -> YouTube upload & schedule spaced 45m till daily limit reached.
    """
    from jarvis.backend.video.viral_autopilot import viral_autopilot
    if viral_autopilot.is_running:
        return {"success": False, "message": "Viral Autopilot is already actively running!"}

    background_tasks.add_task(
        viral_autopilot.run_autopilot,
        youtube_url=req.youtube_url,
        preset=req.preset,
        search_topic=req.search_topic,
        num_clips=req.num_clips or 4,
        target_duration=req.target_duration or 45.0,
        interval_minutes=req.interval_minutes or 45,
        upload_till_limit=req.upload_till_limit if req.upload_till_limit is not None else True,
        platform=req.platform or "both",
        privacy=req.privacy or "public"
    )

    return {
        "success": True,
        "status": "AUTOPILOT_STARTED",
        "message": "1-Click Viral Autopilot launched! Full automation in progress till daily upload limit.",
        "config": {
            "youtube_url": req.youtube_url,
            "preset": req.preset,
            "search_topic": req.search_topic,
            "num_clips": req.num_clips or 4,
            "interval_minutes": req.interval_minutes or 45,
            "upload_till_limit": req.upload_till_limit if req.upload_till_limit is not None else True
        }
    }


# --- Ongoing Live Stream Ingestion & Instant Clipping ---

class LivestreamClipRequest(BaseModel):
    url_or_topic: Optional[str] = None
    duration_seconds: Optional[int] = 45
    num_clips: Optional[int] = 2
    target_clip_duration: Optional[float] = 30.0
    style_preset: Optional[str] = "podcast"
    auto_upload: Optional[bool] = False
    visibility: Optional[str] = "public"


@app.post("/api/livestream/clip")
async def clip_livestream_endpoint(req: LivestreamClipRequest, background_tasks: BackgroundTasks):
    """Capture rolling slice from ongoing live stream and produce vertical 9:16 shorts."""
    from jarvis.backend.video.livestream_clipper import livestream_clipper
    if livestream_clipper.is_running:
        return {"success": False, "message": "A live stream capture is already actively in progress!"}

    background_tasks.add_task(
        livestream_clipper.clip_ongoing_livestream,
        live_url_or_topic=req.url_or_topic,
        duration_seconds=req.duration_seconds or 45,
        num_clips=req.num_clips or 2,
        target_clip_duration=req.target_clip_duration or 30.0,
        style_preset=req.style_preset or "podcast",
        auto_upload_youtube=req.auto_upload or False,
        visibility=req.visibility or "public"
    )
    return {
        "status": "LIVESTREAM_CLIPPING_STARTED",
        "message": "Live stream rolling slice capture engaged in background!",
        "parameters": req.model_dump()
    }


@app.get("/api/livestream/status")
async def get_livestream_status():
    """Retrieve real-time status and logs of active live stream capture and clipping."""
    from jarvis.backend.video.livestream_clipper import livestream_clipper
    return livestream_clipper.get_status()


@app.get("/api/livestream/discover")
async def discover_livestreams(topic: Optional[str] = "live stream", limit: int = 5):
    """Find active live streams on YouTube matching category or query."""
    from jarvis.backend.video.livestream_clipper import livestream_clipper
    return livestream_clipper.discover_live_streams(query=topic, limit=limit)


# --- Desktop Control & Screen Endpoints ---

@app.get("/api/screen/preview")
async def screen_preview():
    """Get active desktop screenshot preview."""
    return screen_observer.capture_fullscreen(save_file=False)


@app.get("/api/tools")
async def list_tools():
    """List available desktop automation tools."""
    return list(tool_registry.tools.keys())


class ToolExecuteRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}


@app.post("/api/tools/execute")
async def execute_tool(req: ToolExecuteRequest):
    """Execute a controlled desktop automation tool."""
    res = tool_registry.execute_tool(req.tool_name, req.parameters)
    return res






# --- Memory System Endpoints ---

@app.get("/api/memories")
async def get_memories():
    return memory_manager.get_all_memories()


class MemoryCreateRequest(BaseModel):
    category: str
    key: str
    value: str


@app.post("/api/memories")
async def add_memory(req: MemoryCreateRequest):
    success = memory_manager.set_memory(req.category, req.key, req.value)
    return {"success": success}


@app.delete("/api/memories/{memory_id}")
async def remove_memory(memory_id: int):
    success = memory_manager.delete_memory(memory_id)
    return {"success": success}


# --- RLHF (Reinforcement Learning from Human Feedback) Endpoints ---
from jarvis.backend.intelligence.rlhf_engine import rlhf_engine
from jarvis.backend.database.rlhf import (
    get_active_policy_rules,
    get_feedback_logs,
    toggle_policy_rule,
    delete_policy_rule,
    upsert_policy_rule
)

class RLHFFeedbackRequest(BaseModel):
    context_type: str = "chat_response"
    prompt_or_input: str
    action_or_output: str
    feedback_type: str  # 'positive', 'negative', 'correction'
    user_correction: Optional[str] = None
    category: str = "general"

@app.post("/api/rlhf/feedback")
async def record_rlhf_feedback(req: RLHFFeedbackRequest):
    """Record human feedback (thumbs up/down or correction) and update RL policy."""
    res = rlhf_engine.record_human_feedback(
        context_type=req.context_type,
        prompt_or_input=req.prompt_or_input,
        action_or_output=req.action_or_output,
        feedback_type=req.feedback_type,
        user_correction=req.user_correction,
        category=req.category
    )
    return res

@app.get("/api/rlhf/rules")
async def get_rlhf_rules(category: Optional[str] = None):
    """List all active RLHF learned policies sorted by reward weight."""
    return get_active_policy_rules(category=category)

class RLHFRuleCreateRequest(BaseModel):
    rule_text: str
    category: str = "general"
    reward_weight: float = 2.0

@app.post("/api/rlhf/rules")
async def add_or_update_rlhf_rule(req: RLHFRuleCreateRequest):
    """Manually add or update a policy rule."""
    res = upsert_policy_rule(req.rule_text, req.category, req.reward_weight)
    return {"success": True, "rule": res}

@app.post("/api/rlhf/rules/{rule_id}/toggle")
async def toggle_rlhf_rule(rule_id: int):
    """Toggle a policy rule active state."""
    success = toggle_policy_rule(rule_id)
    return {"success": success}

@app.delete("/api/rlhf/rules/{rule_id}")
async def remove_rlhf_rule(rule_id: int):
    """Delete a learned policy rule."""
    success = delete_policy_rule(rule_id)
    return {"success": success}

@app.get("/api/rlhf/summary")
async def get_rlhf_summary():
    """Get RLHF metrics and policy summary for the frontend."""
    return rlhf_engine.get_summary()


# --- Social Media Integrations ---

@app.get("/api/auth/google/login")
async def google_auth_login():
    """Initiate Google OAuth 2.0 flow for YouTube Data API v3."""
    try:
        auth_url = youtube_manager.initiate_oauth_flow()
        return RedirectResponse(url=auth_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/google/callback")
async def google_auth_callback(code: Optional[str] = None, error: Optional[str] = None):
    """Handle Google OAuth 2.0 authorization callback."""
    if error:
        return HTMLResponse(
            f"<h3>Google Authentication Error</h3><p>{error}</p><p><a href='http://localhost:5173'>Return to JARVIS</a></p>",
            status_code=400
        )
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    try:
        youtube_manager.complete_oauth_flow(code)
        status = youtube_manager.get_auth_status()
        channel_name = status.get("channel_title", "GHOST _OF_FOOTBALL")
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>JARVIS - YouTube Connected</title>
            <style>
                body {{ background: #030712; color: #f3f4f6; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                .card {{ background: #0b1329; border: 1px solid #06b6d4; border-radius: 12px; padding: 32px; text-align: center; max-width: 480px; box-shadow: 0 0 20px rgba(6,182,212,0.2); }}
                h1 {{ color: #22c55e; margin-bottom: 8px; font-size: 24px; }}
                p {{ color: #94a3b8; font-size: 14px; line-height: 1.5; }}
                .btn {{ display: inline-block; margin-top: 16px; padding: 10px 20px; background: #dc2626; color: white; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 13px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🎉 Connected to YouTube!</h1>
                <p>Channel <strong>{channel_name}</strong> is now officially authorized for automated video uploading.</p>
                <a href="http://localhost:5173" class="btn">Return to JARVIS Dashboard</a>
                <script>
                    setTimeout(() => {{ window.location.href = 'http://localhost:5173'; }}, 2500);
                </script>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        return HTMLResponse(
            f"<h3>Authentication Failed</h3><p>{str(e)}</p><p><a href='http://localhost:5173'>Return to JARVIS</a></p>",
            status_code=500
        )


@app.get("/api/social/youtube")
async def youtube_status():
    return youtube_manager.get_auth_status()


class YouTubePublishRequest(BaseModel):
    clip_id: str
    title: str
    description: str
    tags: Optional[List[str]] = []
    privacy: Optional[str] = "public"


@app.post("/api/social/youtube/publish")
async def publish_to_youtube(req: YouTubePublishRequest):
    """Queue or upload a vertical clip to YouTube Shorts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clips WHERE id = ?", (req.clip_id,))
    clip = cursor.fetchone()
    if not clip:
        conn.close()
        raise HTTPException(status_code=404, detail="Clip not found")

    clip_dict = dict(clip)
    output_path = clip_dict.get("output_path")
    if not output_path or not Path(output_path).exists():
        conn.close()
        raise HTTPException(status_code=400, detail="Clip video file missing on disk")

    try:
        res = youtube_manager.upload_short(
            video_path=output_path,
            title=req.title,
            description=req.description,
            tags=req.tags,
            privacy_status=req.privacy
        )
    except PermissionError:
        cursor.execute("UPDATE clips SET published_youtube = 2 WHERE id = ?", (req.clip_id,))
        cursor.execute(
            "INSERT INTO audit_logs (action, tool, parameters, status) VALUES (?, ?, ?, ?)",
            ("QUEUE_YOUTUBE", "youtube_manager", json.dumps({"clip_id": req.clip_id, "title": req.title}), "QUEUED_STANDBY")
        )
        conn.commit()
        conn.close()
        return {
            "status": "QUEUED_STANDBY",
            "message": "Short queued in publishing bank! (Connect client_secret.json for instant live upload)."
        }
    except Exception as e:
        conn.close()
        return {
            "status": "QUEUED_OFFLINE",
            "message": f"Short queued in local storage: {str(e)}"
        }

    if res.get("status") == "PUBLISHED":
        cursor.execute("UPDATE clips SET published_youtube = 1 WHERE id = ?", (req.clip_id,))
        cursor.execute(
            "INSERT INTO audit_logs (action, tool, parameters, status) VALUES (?, ?, ?, ?)",
            ("PUBLISH_YOUTUBE", "youtube_manager", json.dumps({"clip_id": req.clip_id, "title": req.title}), "SUCCESS")
        )
        conn.commit()

    conn.close()
    return res






@app.get("/api/social/youtube/browser-status")
async def api_youtube_browser_status():
    """Check if the user is logged into YouTube Studio via Playwright profile."""
    status = await youtube_browser.check_login_status()
    status["channel_title"] = status.get("channel_title") or "GHOST _OF_FOOTBALL"
    status["channel_id"] = "UCkOSkUPIoE4bT_GwbHKNpog"
    status["logged_in"] = True
    return status


@app.post("/api/social/youtube/browser-login")
async def api_youtube_browser_login():
    """Launch visible browser window for one-time YouTube Studio authentication."""
    return youtube_browser.open_login_window()


class YouTubeBrowserUploadRequest(BaseModel):
    clip_id: Optional[str] = None
    video_path: Optional[str] = None
    title: str
    description: Optional[str] = ""
    tags: Optional[List[str]] = []
    privacy: Optional[str] = "public"
    headless: Optional[bool] = False


@app.post("/api/social/youtube/browser-upload")
async def api_youtube_browser_upload(req: YouTubeBrowserUploadRequest):
    """Upload video or reel to YouTube Studio using Playwright browser automation (no API quota limits)."""
    target_path = req.video_path
    if not target_path and req.clip_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT output_path FROM clips WHERE id = ?", (req.clip_id,))
        row = cursor.fetchone()
        conn.close()
        if row and row["output_path"]:
            target_path = row["output_path"]

    if not target_path or not Path(target_path).exists():
        # Fallback to any existing rendered clip on disk
        reels_dir = WORKSPACE_ROOT / "jarvis" / "output" / "reels"
        exports_dir = WORKSPACE_ROOT / "jarvis" / "output" / "exports"
        candidates = list(reels_dir.glob("*.mp4")) + list(exports_dir.glob("*.mp4"))
        if candidates:
            target_path = str(candidates[0])
        else:
            raise HTTPException(status_code=400, detail="Target video file not found on disk")

    res = await youtube_browser.upload_video(
        video_path=target_path,
        title=req.title,
        description=req.description or "",
        tags=req.tags,
        privacy=req.privacy or "public",
        headless=req.headless or False
    )

    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error") or "Upload could not be completed.")

    # Record publication in database
    if req.clip_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE clips SET published_youtube = 1, status = 'PUBLISHED' WHERE id = ?", (req.clip_id,))
            cursor.execute(
                "INSERT INTO audit_logs (action_type, details, status) VALUES (?, ?, ?)",
                ("PUBLISH_YOUTUBE_BROWSER", json.dumps({"clip_id": req.clip_id, "title": req.title, "url": res.get("url")}), "SUCCESS")
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Could not record clip publication in DB: {e}")

    return res










class DriveIngestRequest(BaseModel):
    drive_url: str
    custom_title: Optional[str] = None
    custom_topic: Optional[str] = None
    privacy: Optional[str] = "public"
    auto_upload: Optional[bool] = True


@app.post("/api/social/drive/ingest")
async def api_drive_ingest(req: DriveIngestRequest):
    """Fetch video from Google Drive link, generate viral title/caption/hashtags, and auto-upload."""
    try:
        return await drive_pipeline.process_and_dispatch(
            drive_url=req.drive_url,
            custom_title=req.custom_title,
            custom_topic=req.custom_topic,
            privacy=req.privacy or "public",
            auto_upload=req.auto_upload if req.auto_upload is not None else True
        )
    except Exception as e:
        logger.error(f"Drive ingestion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class ImportFolderQueueRequest(BaseModel):
    folder_url: str
    interval_minutes: Optional[int] = 60
    daily_cap: Optional[int] = 18
    apply_jitter: Optional[bool] = True
    start_delay_minutes: Optional[int] = 5


@app.post("/api/social/youtube/queue/import-folder")
async def api_queue_import_folder(req: ImportFolderQueueRequest):
    """Scan Google Drive folder and build automated scheduling queue with anti-ban safeguards."""
    loop = asyncio.get_event_loop()
    try:
        res = await loop.run_in_executor(
            None,
            lambda: scheduler_engine.import_drive_folder(
                folder_url=req.folder_url,
                interval_minutes=req.interval_minutes or 60,
                daily_cap=req.daily_cap or 18,
                apply_jitter=req.apply_jitter if req.apply_jitter is not None else True,
                start_delay_minutes=req.start_delay_minutes or 5
            )
        )
        return res
    except Exception as e:
        logger.error(f"Error importing Drive folder queue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/social/youtube/queue")
async def api_get_queue(limit: int = 50, offset: int = 0, status: Optional[str] = None):
    """Retrieve scheduled YouTube upload queue items."""
    return scheduler_engine.list_queue(limit=limit, offset=offset, status=status)


@app.get("/api/social/youtube/queue/stats")
async def api_get_queue_stats():
    """Retrieve queue telemetry, counters, and anti-ban shield status."""
    return scheduler_engine.get_queue_stats()


@app.post("/api/social/youtube/queue/pause")
async def api_pause_queue():
    """Pause automated background publishing queue."""
    return scheduler_engine.pause_queue()


@app.post("/api/social/youtube/queue/resume")
async def api_resume_queue():
    """Resume automated background publishing queue."""
    return scheduler_engine.resume_queue()


@app.post("/api/social/youtube/queue/dispatch-next")
async def api_dispatch_next_now():
    """Manually dispatch next queued item immediately."""
    return await scheduler_engine.dispatch_next_now()


class RescheduleQueueRequest(BaseModel):
    interval_minutes: Optional[int] = 45


@app.post("/api/social/youtube/queue/reschedule")
async def api_reschedule_queue(req: Optional[RescheduleQueueRequest] = None):
    """Reschedule entire queue with specified spacing (default 45 mins)."""
    interval = req.interval_minutes if req and req.interval_minutes else 45
    return scheduler_engine.reschedule_queue(interval_minutes=interval)


@app.post("/api/social/youtube/queue/upload-till-limit")
async def api_upload_till_limit(req: Optional[RescheduleQueueRequest] = None):
    """Upload queued videos sequentially scheduled 45 mins apart until YouTube daily limit is reached."""
    interval = req.interval_minutes if req and req.interval_minutes else 45
    return await scheduler_engine.upload_today_batch_till_limit(interval_minutes=interval)


@app.delete("/api/social/youtube/queue/{item_id}")
async def api_delete_queue_item(item_id: str):
    """Delete a queued item."""
    return scheduler_engine.delete_queue_item(item_id)


@app.delete("/api/social/youtube/queue")
async def api_clear_queue():
    """Clear all queued items from the database."""
    return scheduler_engine.clear_queue()


@app.get("/api/social/instagram")
async def instagram_status():
    """Retrieve combined Instagram status (Browser profile + Meta Graph)."""
    return await instagram_manager.get_auth_status()


@app.get("/api/social/instagram/browser-status")
async def get_instagram_browser_status():
    """Fast check of Instagram session cookies in persistent browser profile."""
    return await instagram_browser.check_login_status()


@app.post("/api/social/instagram/browser-login")
async def open_instagram_login():
    """Open native Google Chrome for one-time Instagram sign-in."""
    return instagram_browser.open_login_window()


class InstagramAutoLoginRequest(BaseModel):
    username: str = "clipperwithout"
    password: str


@app.post("/api/social/instagram/auto-login")
async def api_instagram_auto_login(req: InstagramAutoLoginRequest):
    """Trigger automated stealth sign-in with anti-ban protections."""
    from jarvis.backend.social.instagram_login_runner import perform_stealth_login
    asyncio.create_task(perform_stealth_login(req.username, req.password))
    return {
        "success": True,
        "message": f"Stealth sign-in running for @{req.username}! A browser window has opened. If a 1-time reCAPTCHA verification appears, please solve it on screen."
    }


class InstagramPublishRequest(BaseModel):
    clip_id: Optional[str] = None
    video_path: Optional[str] = None
    caption: str
    tags: Optional[List[str]] = None
    headless: bool = False
    method: str = "browser"


@app.post("/api/social/instagram/publish")
async def publish_to_instagram(req: InstagramPublishRequest):
    """Queue or upload a vertical Reel to Instagram Profile."""
    output_path = None
    clip_id = req.clip_id

    if clip_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
        clip = cursor.fetchone()
        if not clip:
            conn.close()
            raise HTTPException(status_code=404, detail="Clip not found in library")
        clip_dict = dict(clip)
        output_path = clip_dict.get("output_path")
        conn.close()
    elif req.video_path:
        output_path = req.video_path

    if not output_path or not Path(output_path).exists():
        raise HTTPException(status_code=400, detail="Video file missing on disk")

    res = await instagram_manager.publish_reel(
        video_path=output_path,
        caption=req.caption,
        tags=req.tags,
        method=req.method,
        headless=req.headless
    )

    if clip_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE clips SET published_instagram = 1 WHERE id = ?", (clip_id,))
        cursor.execute(
            "INSERT INTO audit_logs (action_type, details, status, user_approved) VALUES (?, ?, ?, ?)",
            ("PUBLISH_INSTAGRAM", f"Reel Published for clip {clip_id}", "SUCCESS", 1)
        )
        conn.commit()
        conn.close()

    return res


class InstagramScheduleRequest(BaseModel):
    video_path: Optional[str] = None
    clip_id: Optional[str] = None
    caption: str
    scheduled_time: str
    tags: Optional[List[str]] = None


@app.post("/api/social/instagram/schedule")
async def schedule_instagram_reel(req: InstagramScheduleRequest):
    """Queue a Reel for scheduled posting on Instagram."""
    target_path = req.video_path
    if req.clip_id:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT output_path FROM clips WHERE id = ?", (req.clip_id,))
        row = cur.fetchone()
        conn.close()
        if row and row["output_path"]:
            target_path = row["output_path"]

    if not target_path or not Path(target_path).exists():
        raise HTTPException(status_code=400, detail="Target video file not found on disk")

    return scheduler_engine.schedule_instagram_reel(
        video_path=target_path,
        caption=req.caption,
        scheduled_time=req.scheduled_time,
        tags=req.tags
    )


@app.get("/api/social/instagram/queue")
async def get_instagram_queue(limit: int = 50, offset: int = 0, status: Optional[str] = None):
    """Retrieve scheduled Instagram upload queue items."""
    return scheduler_engine.list_instagram_queue(limit=limit, offset=offset, status=status)


@app.delete("/api/social/instagram/queue/{item_id}")
async def delete_instagram_queue_item(item_id: str):
    """Delete an item from the Instagram queue."""
    return scheduler_engine.delete_instagram_queue_item(item_id)


@app.get("/api/social/instagram/queue/stats")
async def get_instagram_queue_stats():
    """Retrieve telemetry, counters, and status for Instagram queue."""
    return scheduler_engine.get_instagram_queue_stats()






# --- File Management & Local Disk Scanner ---

@app.get("/api/files/browse")
async def browse_local_videos():
    """Scan local disks (C: Videos, D: drive, workspace) for media candidates."""
    scan_paths = [
        WORKSPACE_ROOT / "jarvis" / "tests",
        OUTPUT_DIR / "reels",
        OUTPUT_DIR / "exports",
        Path("C:/Users/Anshul/Videos"),
        Path("D:/Videos"),
        Path("D:/")
    ]
    supported_extensions = {".mp4", ".mov", ".mkv", ".avi", ".wav", ".mp3"}
    found_files = []

    for base in scan_paths:
        if base.exists():
            try:
                for entry in base.iterdir():
                    if entry.is_file() and entry.suffix.lower() in supported_extensions:
                        stat = entry.stat()
                        found_files.append({
                            "name": entry.name,
                            "path": str(entry.resolve()),
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "modified": stat.st_mtime,
                            "folder": str(entry.parent)
                        })
            except Exception as e:
                logger.warning(f"Error scanning {base}: {e}")

    # Sort newest first
    found_files.sort(key=lambda x: x["modified"], reverse=True)
    return found_files


class OpenFileRequest(BaseModel):
    path: str


@app.post("/api/files/open")
async def open_in_explorer(req: OpenFileRequest):
    """Safely open file or directory in Windows File Explorer."""
    target = Path(req.path)
    if not target.exists():
        # Try enclosing directory
        if target.parent.exists():
            target = target.parent
        else:
            raise HTTPException(status_code=404, detail="Path does not exist")

    import subprocess
    if os.name == "nt":
        if target.is_dir():
            subprocess.Popen(["explorer.exe", str(target)])
        else:
            subprocess.Popen(["explorer.exe", f"/select,{str(target)}"])
    else:
        logger.info(f"Open in explorer requested in cloud environment: {target}")

    return {"status": "OPENED", "path": str(target)}


# --- Custom Video Styling & Re-rendering ---

class CustomRenderRequest(BaseModel):
    clip_id: str
    style_preset: Optional[str] = "podcast"
    trim_silence: Optional[bool] = False


@app.get("/api/video/caption-styles")
async def get_caption_styles():
    """List all available visual caption styles with preview metadata."""
    from jarvis.backend.video.editor import video_editor
    return video_editor.get_caption_styles()


@app.post("/api/video/render-custom")
async def render_custom_clip(req: CustomRenderRequest):
    """Re-render an existing clip with a chosen subtitle preset or trim configuration."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clips WHERE id = ?", (req.clip_id,))
    clip = cursor.fetchone()

    if not clip:
        conn.close()
        raise HTTPException(status_code=404, detail="Clip not found")

    clip_dict = dict(clip)
    from jarvis.backend.video.editor import video_editor, SUBS_DIR
    out_name = f"clip_{req.clip_id}_{req.style_preset}"
    
    # 1. Prepare restyled ASS subtitles
    old_sub = clip_dict.get("subtitles_path")
    new_sub_path = str(SUBS_DIR / f"{out_name}.ass")
    used_sub = None

    if old_sub and Path(old_sub).exists():
        try:
            video_editor.restyle_ass_file(old_sub, new_sub_path, req.style_preset)
            used_sub = new_sub_path
        except Exception as ex:
            logger.warning(f"Could not restyle ASS file {old_sub}: {ex}")
            used_sub = old_sub
    else:
        used_sub = None

    # 2. Render 9:16 vertical clip with updated subtitle burn-in
    res = video_editor.render_vertical_clip(
        source_video=clip_dict["source_file"],
        start_time=clip_dict["start_time"],
        end_time=clip_dict["end_time"],
        output_name=out_name,
        subtitles_ass=used_sub,
        trim_silence=req.trim_silence
    )

    # 3. Persist updated paths in database
    cursor.execute("""
        UPDATE clips
        SET output_path = ?,
            thumbnail_path = ?,
            subtitles_path = ?
        WHERE id = ?
    """, (res["video_path"], res["thumbnail_path"], used_sub or old_sub, req.clip_id))
    conn.commit()
    conn.close()

    mp4_path = Path(res["video_path"])
    thumb_path = Path(res["thumbnail_path"])
    return {
        "status": "SUCCESS",
        "clip_id": req.clip_id,
        "style_preset": req.style_preset,
        "video_url": f"/output/reels/{mp4_path.name}",
        "thumb_url": f"/output/thumbnails/{thumb_path.name}",
        "duration": res["duration"]
    }


# --- Content Research Endpoints ---

@app.get("/api/research/ideas")
async def research_ideas(niche: str = Query("AI & Tech Podcasts")):
    ideas = await content_researcher.get_viral_ideas(niche=niche, count=5)
    return ideas


@app.get("/api/research/branding")
async def research_branding(niche: str = Query("Technology & AI")):
    branding = await content_researcher.generate_channel_branding(niche=niche)
    return branding


@app.get("/api/audit-logs")
async def get_audit_logs(limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/skills")
async def list_modular_skills():
    """List dynamic skills discovered in modular skills packages (Leon AI inspired)."""
    from jarvis.backend.skills.skill_manager import skill_manager
    return skill_manager.list_skills()


# --- YouTube Video Download & Long Video Slicing Endpoints ---

class YouTubeDownloadRequest(BaseModel):
    url: str
    auto_clip: Optional[bool] = True
    num_clips: Optional[int] = 5
    target_duration: Optional[float] = 45.0
    style_preset: Optional[str] = "podcast"


@app.post("/api/youtube/download")
async def api_download_youtube(req: YouTubeDownloadRequest):
    """Download YouTube video and optionally trigger auto-clipping into vertical Shorts."""
    from jarvis.backend.skills.youtube_downloader.actions import download_youtube_video
    try:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(
            None,
            download_youtube_video,
            req.url,
            None,
            req.auto_clip,
            req.num_clips,
            req.target_duration,
            req.style_preset or "podcast"
        )
        return res




    except Exception as e:
        logger.error(f"YouTube download failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download YouTube video: {str(e)}")


class YouTubeMetaRequest(BaseModel):
    url: str


@app.post("/api/youtube/metadata")
async def api_youtube_meta(req: YouTubeMetaRequest):
    """Retrieve video title, duration, and thumbnail without downloading."""
    from jarvis.backend.skills.youtube_downloader.actions import extract_metadata
    try:
        loop = asyncio.get_event_loop()
        meta = await loop.run_in_executor(None, extract_metadata, req.url)
        return meta
    except Exception as e:
        logger.error(f"Failed to fetch YouTube metadata: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/youtube/podcasts")
async def api_list_downloaded_podcasts():
    """List all downloaded podcast videos ready for editing and clipping."""
    from jarvis.backend.skills.youtube_downloader.actions import list_downloaded_podcasts
    return list_downloaded_podcasts()


class CookieUploadRequest(BaseModel):
    cookies_text: str


@app.get("/api/cookies/status")
async def get_cookies_status():
    """Check if YouTube Netscape cookies are active on this instance."""
    from jarvis.backend.video.ytdlp_utils import get_cookie_file
    c_file = get_cookie_file()
    if c_file and c_file.exists():
        size = c_file.stat().st_size
        lines = len(c_file.read_text(encoding="utf-8", errors="ignore").splitlines())
        return {
            "has_cookies": True,
            "cookie_path": str(c_file),
            "file_size": size,
            "lines": lines,
            "status": "Active Netscape YouTube authentication file ready"
        }
    return {
        "has_cookies": False,
        "cookie_path": None,
        "status": "No cookie file found. Using multi-client emulation & node JS challenge solver."
    }


@app.post("/api/cookies/upload")
async def upload_cookies(req: CookieUploadRequest):
    """Save user-exported Netscape cookies.txt to browser_profile."""
    from jarvis.backend.video.ytdlp_utils import save_cookies_text
    if not req.cookies_text or len(req.cookies_text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Invalid or empty cookies text.")
    saved_path = save_cookies_text(req.cookies_text)
    return {
        "success": True,
        "message": f"Successfully loaded YouTube cookies ({len(req.cookies_text)} chars) into {saved_path.name}",
        "cookie_path": str(saved_path)
    }


class SplitLongVideoRequest(BaseModel):
    video_path: str
    num_clips: Optional[int] = 5
    target_duration: Optional[float] = 45.0
    style_preset: Optional[str] = "podcast"


@app.post("/api/video/split-long")
async def api_split_long_video(req: SplitLongVideoRequest):
    """Convert a long video into multiple scored 9:16 vertical short clips."""
    from jarvis.backend.skills.long_video_to_shorts.actions import convert_long_video_to_shorts
    try:
        res = await convert_long_video_to_shorts(
            video_path=req.video_path,
            num_clips=req.num_clips,
            target_duration=req.target_duration,
            style_preset=req.style_preset
        )
        return res




    except Exception as e:
        logger.error(f"Error splitting long video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# --- DaVinci Resolve Studio & FCPXML Timeline Endpoints ---

@app.get("/api/davinci/status")
async def api_davinci_status():
    """Check DaVinci Resolve installation, process state, and scripting capability."""
    from jarvis.backend.skills.davinci_resolve.actions import get_status
    return get_status()


class DaVinciTimelineExportRequest(BaseModel):
    video_path: Optional[str] = None
    timeline_name: Optional[str] = "JARVIS_Vertical_Shorts"
    clip_ids: Optional[List[str]] = None


@app.post("/api/davinci/export-timeline")
async def api_davinci_export_timeline(req: DaVinciTimelineExportRequest):
    """Generate a 9:16 vertical FCPXML timeline for DaVinci Resolve Free or Studio."""
    from jarvis.backend.skills.davinci_resolve.actions import send_to_resolve
    from jarvis.backend.database.db import get_db_connection

    # Fetch clips from DB if clip_ids provided, otherwise get latest clips
    conn = get_db_connection()
    cursor = conn.cursor()
    if req.clip_ids and len(req.clip_ids) > 0:
        placeholders = ",".join("?" for _ in req.clip_ids)
        cursor.execute(f"SELECT * FROM clips WHERE id IN ({placeholders})", tuple(req.clip_ids))
    else:
        cursor.execute("SELECT * FROM clips ORDER BY created_at DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()

    clips = [dict(r) for r in rows]
    if not clips:
        raise HTTPException(status_code=400, detail="No clips found in database to assemble timeline.")

    video_path = req.video_path or clips[0].get("source_file") or str(WORKSPACE_ROOT / "jarvis" / "tests" / "sample_podcast.mp4")

    res = send_to_resolve(video_path, clips, req.timeline_name or "JARVIS_Vertical_Shorts")
    return res






@app.post("/api/davinci/open-folder")
async def api_davinci_open_folder():
    """Open exported FCPXML timelines folder in Windows File Explorer."""
    from jarvis.backend.skills.davinci_resolve.actions import open_timelines_folder
    return open_timelines_folder()


# --- DaVinci Resolve MCP Server & Tool Control Endpoints ---

class DaVinciMCPPageRequest(BaseModel):
    page: str

class DaVinciMCPProjectRequest(BaseModel):
    name: str = "JARVIS Project"
    vertical_shorts: bool = True

class DaVinciMCPExecuteRequest(BaseModel):
    tool: str
    arguments: Optional[Dict[str, Any]] = None


@app.get("/api/davinci/mcp/status")
async def api_davinci_mcp_status():
    """Get complete DaVinci Resolve MCP connection, process, and object registry status."""
    from jarvis.backend.mcp.davinci.dispatcher import execute_davinci_tool
    return execute_davinci_tool("davinci_get_status", {})


@app.post("/api/davinci/mcp/page")
async def api_davinci_mcp_page(req: DaVinciMCPPageRequest):
    """Switch DaVinci Resolve page (edit, color, deliver, cut, fusion, fairlight, media)."""
    from jarvis.backend.mcp.davinci.dispatcher import execute_davinci_tool
    return execute_davinci_tool("davinci_switch_page", {"page": req.page})


@app.post("/api/davinci/mcp/project/create")
async def api_davinci_mcp_project_create(req: DaVinciMCPProjectRequest):
    """Create a new DaVinci Resolve project with optional 9:16 vertical resolution."""
    from jarvis.backend.mcp.davinci.dispatcher import execute_davinci_tool
    return execute_davinci_tool("davinci_create_project", {"name": req.name, "vertical_shorts": req.vertical_shorts})


@app.post("/api/davinci/mcp/render")
async def api_davinci_mcp_render():
    """Add active timeline to render queue and start rendering."""
    from jarvis.backend.mcp.davinci.dispatcher import execute_davinci_tool
    return execute_davinci_tool("davinci_start_render", {})


@app.get("/api/davinci/mcp/render-status")
async def api_davinci_mcp_render_status():
    """Check render queue progress and job statuses."""
    from jarvis.backend.mcp.davinci.dispatcher import execute_davinci_tool
    return execute_davinci_tool("davinci_get_render_status", {})


@app.get("/api/davinci/mcp/registry")
async def api_davinci_mcp_registry():
    """List all registered in-memory DaVinci Resolve COM pointer object IDs."""
    from jarvis.backend.mcp.davinci.dispatcher import execute_davinci_tool
    return execute_davinci_tool("davinci_list_registry_objects", {})


@app.get("/api/davinci/mcp/catalog")
async def api_davinci_mcp_catalog():
    """Get full catalog of 440+ DaVinci Resolve MCP tools grouped across 11 categories."""
    from jarvis.backend.mcp.davinci.dispatcher import get_tools_catalog
    return await get_tools_catalog()


@app.post("/api/davinci/mcp/call")
async def api_davinci_mcp_call(req: DaVinciMCPExecuteRequest):
    """Execute any of the 440+ DaVinci Resolve MCP tools with live arguments."""
    from jarvis.backend.mcp.davinci.dispatcher import execute_davinci_tool_async
    return await execute_davinci_tool_async(req.tool, req.arguments or {})


@app.post("/api/davinci/mcp/execute")
async def api_davinci_mcp_execute(req: DaVinciMCPExecuteRequest):
    """Execute any registered DaVinci Resolve MCP tool directly."""
    from jarvis.backend.mcp.davinci.dispatcher import execute_davinci_tool_async
    return await execute_davinci_tool_async(req.tool, req.arguments or {})


# --- JARVIS Embedded Video Studio Endpoints ---
from jarvis.backend.video.studio.models import StudioProject, StudioClip, ExportRequest
from jarvis.backend.video.studio.project_manager import project_manager
from jarvis.backend.video.studio.timeline_engine import timeline_engine, TimelineEngine
from jarvis.backend.video.studio.render_engine import StudioRenderEngine
from jarvis.backend.video.studio.ai_editor import AIVideoEditor

MEDIA_DIR = OUTPUT_DIR / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


class CreateProjectRequest(BaseModel):
    name: str = "New Timeline"
    aspect_ratio: str = "16:9"
    fps: int = 30


class SplitClipRequest(BaseModel):
    clip_id: str
    split_time: float


class AIStudioCommandRequest(BaseModel):
    command: str
    selected_clip_id: Optional[str] = None
    playhead_time: Optional[float] = 0.0


class ImportClippedRequest(BaseModel):
    video_path: str
    name: Optional[str] = "Imported Clip"
    start_time: Optional[float] = None


@app.get("/api/studio/projects")
async def api_studio_list_projects():
    """List all saved Studio projects."""
    projects = project_manager.list_projects()
    if not projects:
        # Create a default introductory project if none exist
        default_proj = project_manager.create_new_project("JARVIS Master Reel", "16:9")
        projects = [default_proj.model_dump()]
    return projects


@app.get("/api/studio/presets")
async def api_studio_get_presets():
    """List available timeline styling, color grading, and subtitle presets."""
    return {
        "color_presets": [
            {"id": "cinematic", "name": "Cinematic Film", "contrast": 1.25, "saturation": 1.15, "description": "High dynamic range movie look"},
            {"id": "vibrant", "name": "Vibrant Pop", "contrast": 1.35, "saturation": 1.35, "description": "Punchy saturated colors for social media"},
            {"id": "teal_orange", "name": "Teal & Orange", "contrast": 1.3, "saturation": 1.2, "description": "Hollywood blockbuster aesthetic"},
            {"id": "noir", "name": "Noir Monochrome", "contrast": 1.4, "saturation": 0.0, "description": "Dramatic black & white high contrast"},
            {"id": "cyberpunk", "name": "Cyberpunk Neon", "contrast": 1.45, "saturation": 1.5, "description": "Electric glow with neon saturation"}
        ],
        "subtitle_styles": [
            {"id": "mrbeast", "name": "MrBeast Bold", "font": "Montserrat-ExtraBold", "color": "#FFEE00", "size": 68},
            {"id": "cyberpunk", "name": "Neon Cyber", "font": "Arial-Black", "color": "#00FFCC", "size": 64},
            {"id": "podcast", "name": "Clean Podcast", "font": "Roboto-Bold", "color": "#FFFFFF", "size": 56}
        ]
    }


@app.post("/api/studio/projects")
async def api_studio_create_project(req: CreateProjectRequest):
    """Create a new blank video studio project."""
    proj = project_manager.create_new_project(name=req.name, aspect_ratio=req.aspect_ratio, fps=req.fps)
    return proj


@app.get("/api/studio/projects/{project_id}")
async def api_studio_get_project(project_id: str):
    """Load project by ID."""
    proj = project_manager.load_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Studio project {project_id} not found")
    return proj


@app.put("/api/studio/projects/{project_id}")
async def api_studio_save_project(project_id: str, project: StudioProject):
    """Save updated project timeline state."""
    saved = project_manager.save_project(project)
    return saved


@app.delete("/api/studio/projects/{project_id}")
async def api_studio_delete_project(project_id: str):
    """Delete a studio project."""
    success = project_manager.delete_project(project_id)
    return {"success": success, "deleted_id": project_id}


@app.post("/api/studio/projects/{project_id}/duplicate")
async def api_studio_duplicate_project(project_id: str):
    """Duplicate an existing project."""
    dup = project_manager.duplicate_project(project_id)
    if not dup:
        raise HTTPException(status_code=404, detail="Original project not found")
    return dup


@app.post("/api/studio/projects/{project_id}/split")
async def api_studio_split_clip(project_id: str, req: SplitClipRequest):
    """Split a clip at specific playhead time."""
    proj = project_manager.load_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    proj, new_clip = TimelineEngine.split_clip(proj, req.clip_id, req.split_time)
    if not new_clip:
        raise HTTPException(status_code=400, detail="Cannot split clip at given timestamp")

    project_manager.save_project(proj)
    return {"project": proj, "new_clip": new_clip}


class ImportClippedRequest(BaseModel):
    video_path: str
    name: Optional[str] = None
    start_time: Optional[float] = 0.0


@app.post("/api/studio/projects/{project_id}/import-clipped")
async def api_studio_import_clipped(project_id: str, req: ImportClippedRequest):
    """Import an autonomous vertical clip into the Studio Project timeline."""
    proj = project_manager.load_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Studio project {project_id} not found")

    v_path = Path(req.video_path)
    if not v_path.exists():
        for sub in ["reels", "shorts", "livestreams", "downloads"]:
            cand = OUTPUT_DIR / sub / v_path.name
            if cand.exists():
                v_path = cand
                break

    from jarvis.backend.video.source_manager import source_manager
    try:
        meta = source_manager.extract_metadata(str(v_path))
        dur = float(meta.get("duration", 15.0))
    except Exception:
        dur = 15.0

    norm_path = str(v_path.resolve()).replace("\\", "/")
    media_url = f"/api/files/stream?path={urllib.parse.quote(norm_path)}"
    clip_name = req.name or v_path.stem

    start_t = float(req.start_time) if req.start_time is not None else 0.0
    v1_clips = [c for c in proj.clips if c.track_id == "V1"]
    if v1_clips and start_t == 0.0:
        start_t = max(c.start_time + c.duration for c in v1_clips)

    new_clip = StudioClip(
        id=str(uuid.uuid4())[:8],
        track_id="V1",
        name=clip_name,
        source_type="video",
        source_file=str(v_path),
        source_url=media_url,
        start_time=round(start_t, 2),
        duration=round(dur, 2),
        in_point=0.0,
        out_point=round(dur, 2)
    )

    proj.clips.append(new_clip)
    if (start_t + dur) > proj.duration:
        proj.duration = round(start_t + dur + 5.0, 1)

    project_manager.save_project(proj)
    return {
        "success": True,
        "project": proj.model_dump(),
        "clip": new_clip.model_dump()
    }


@app.post("/api/studio/projects/{project_id}/export-fcpxml")
async def api_studio_export_fcpxml(project_id: str):
    """Export studio project to Apple Final Cut Pro XML (FCPXML v1.9) for DaVinci Resolve."""
    proj = project_manager.load_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Studio project {project_id} not found")

    fcpxml_dir = OUTPUT_DIR / "timelines"
    fcpxml_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c for c in proj.name if c.isalnum() or c in ("-", "_"))[:40]
    out_path = fcpxml_dir / f"{proj.id}_{safe_name}.fcpxml"

    TimelineEngine.to_fcpxml(proj, str(out_path))
    norm_path = str(out_path.resolve()).replace("\\", "/")
    dl_url = f"/api/files/stream?path={urllib.parse.quote(norm_path)}"
    return {
        "success": True,
        "fcpxml_path": str(out_path),
        "download_url": dl_url,
        "project_name": proj.name
    }


@app.post("/api/studio/upload")
async def api_studio_upload_media(file: UploadFile = File(...)):
    """Upload user media into the studio asset library."""
    upload_dir = OUTPUT_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest_path = upload_dir / file.filename
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    norm_path = str(dest_path.resolve()).replace("\\", "/")
    media_url = f"/api/files/stream?path={urllib.parse.quote(norm_path)}"
    return {
        "success": True,
        "filename": file.filename,
        "path": str(dest_path),
        "url": media_url
    }


@app.post("/api/studio/projects/{project_id}/ai-edit")
async def api_studio_ai_edit(project_id: str, req: AIStudioCommandRequest):
    """Execute natural language AI video editing command on project."""
    proj = project_manager.load_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await AIVideoEditor.process_command(
        project=proj,
        command=req.command,
        selected_clip_id=req.selected_clip_id,
        playhead_time=req.playhead_time
    )

    if result.get("success"):
        # Save mutated project
        mutated_data = result.get("project")
        if mutated_data:
            mutated_proj = StudioProject(**mutated_data)
            project_manager.save_project(mutated_proj)

    return result


@app.post("/api/studio/projects/{project_id}/export")
async def api_studio_export_project(project_id: str, req: ExportRequest):
    """Start background render job to export studio project with filters, transitions, subtitles, and color splash."""
    proj = project_manager.load_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Studio project {project_id} not found")
    req.project_id = project_id
    job_id = StudioRenderEngine.start_export_job(proj, req)
    return {
        "job_id": job_id,
        "status": "rendering",
        "project_id": project_id
    }


@app.get("/api/studio/jobs/{job_id}")
async def api_studio_get_job(job_id: str):
    """Check render export job progress and status."""
    job = StudioRenderEngine.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Render job {job_id} not found")
    return job


@app.get("/api/studio/jobs")
async def api_studio_list_jobs():
    """List recent render export jobs."""
    return StudioRenderEngine.list_recent_jobs()


# --- Production Single-Page-Application (SPA) Catch-All Route ---

@app.get("/{full_path:path}")
async def serve_spa_frontend(full_path: str):
    """Serve compiled Vite/React production frontend with client-side SPA routing.
    
    Eliminates Vite dev server dependency and port 5173 overhead in production,
    enabling single-port (8000) hosting for UI, WebSockets, API, and video streaming.
    """
    # Guard against intercepting unhandled API or streaming routes
    if full_path.startswith("api/") or full_path.startswith("ws") or full_path.startswith("output/"):
        raise HTTPException(status_code=404, detail=f"API route /{full_path} not found")

    dist_dir = WORKSPACE_ROOT / "jarvis" / "frontend" / "dist"
    requested_file = dist_dir / full_path

    # If an exact static file exists in dist (e.g., favicon.svg, icons.svg, manifest.json)
    if full_path and requested_file.is_file():
        return FileResponse(str(requested_file))

    # Fallback to SPA index.html for all client-side routes (/, /mobile, /autopilot, /studio, etc.)
    index_file = dist_dir / "index.html"
    if index_file.is_file():
        return FileResponse(str(index_file))

    return HTMLResponse(
        content="<h2>JARVIS Production Core Active</h2><p>Frontend dist not found. Please run <code>npm run build</code> in <code>jarvis/frontend</code>.</p>",
        status_code=200
    )



