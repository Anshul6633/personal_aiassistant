"""JARVIS Global Configuration & Settings."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Base Directories
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
JARVIS_DIR = WORKSPACE_ROOT / "jarvis"
BACKEND_ROOT = JARVIS_DIR / "backend"
OUTPUT_DIR = JARVIS_DIR / "output"
MODELS_DIR = JARVIS_DIR / "models"
LOGS_DIR = JARVIS_DIR / "logs"
ASSETS_DIR = JARVIS_DIR / "assets"
DB_PATH = JARVIS_DIR / "database.sqlite"

# Create output subdirectories if they do not exist
for sub in ["reels", "shorts", "videos", "thumbnails", "subtitles", "audio", "screenshots"]:
    (OUTPUT_DIR / sub).mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "JARVIS - Autonomous Desktop Agent"
    VERSION: str = "2.0.0-PRO"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # AI & Cloud Fallback Configuration (Supports zero-cost Groq Cloud & local Ollama)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    PRIMARY_MODEL: str = os.getenv("PRIMARY_MODEL", "qwen2.5:1.5b")
    FALLBACK_MODEL: str = os.getenv("FALLBACK_MODEL", "qwen2.5:1.5b")
    VISION_MODEL: str = os.getenv("VISION_MODEL", "qwen2.5-vl:3b")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() == "true"

    # Speech Recognition (faster-whisper)
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "tiny")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")  # CPU int8 for instant universally compatible transcription
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    # Speech Synthesis (TTS)
    TTS_ENGINE: str = os.getenv("TTS_ENGINE", "edge-tts")  # edge-tts or pyttsx3
    DEFAULT_VOICE: str = os.getenv("DEFAULT_VOICE", "en-US-ChristopherNeural")  # English Jarvis style
    HINDI_VOICE: str = os.getenv("HINDI_VOICE", "hi-IN-MadhurNeural")
    TTS_RATE: str = "+0%"
    TTS_PITCH: str = "+0Hz"

    # Autonomy Modes: MANUAL, SUPERVISED, PREAPPROVED_AUTONOMOUS
    AUTONOMY_MODE: str = os.getenv("AUTONOMY_MODE", "SUPERVISED")

    # Video Engine Settings
    MAX_DAILY_CLIPS: int = 50
    DEFAULT_CLIP_DURATION: int = 45  # seconds
    SUBTITLE_FONT_SIZE: int = 40
    SUBTITLE_HIGHLIGHT_COLOR: str = "&H00FFFF&"  # Cyan/Yellow
    SUBTITLE_BASE_COLOR: str = "&HFFFFFF&"

    # Social Integrations
    GOOGLE_CLIENT_SECRETS_FILE: Path = WORKSPACE_ROOT / "client_secret.json"
    YOUTUBE_ENABLED: bool = True
    INSTAGRAM_ENABLED: bool = True

    # FFmpeg Binary Path detection (Portable Local Bin or System Fallback)
    LOCAL_FFMPEG: Path = ASSETS_DIR / "bin" / "ffmpeg.exe"
    LOCAL_FFPROBE: Path = ASSETS_DIR / "bin" / "ffprobe.exe"
    LOCAL_FFPLAY: Path = ASSETS_DIR / "bin" / "ffplay.exe"
    FFMPEG_PATH: str = str(ASSETS_DIR / "bin" / "ffmpeg.exe") if (ASSETS_DIR / "bin" / "ffmpeg.exe").exists() else "ffmpeg"
    FFPROBE_PATH: str = str(ASSETS_DIR / "bin" / "ffprobe.exe") if (ASSETS_DIR / "bin" / "ffprobe.exe").exists() else "ffprobe"
    FFPLAY_PATH: str = str(ASSETS_DIR / "bin" / "ffplay.exe") if (ASSETS_DIR / "bin" / "ffplay.exe").exists() else "ffplay"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
