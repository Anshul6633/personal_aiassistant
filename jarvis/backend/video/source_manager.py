"""Source Video Ingestion, Metadata Extraction & Audio Demuxing.

Handles MP4, MOV, MKV, MP3, WAV and authorized YouTube sources via yt-dlp.
"""

import os
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.backend.config.settings import settings, OUTPUT_DIR

logger = logging.getLogger("JARVIS.SourceManager")

TEMP_AUDIO_DIR = OUTPUT_DIR / "temp_audio"
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class SourceVideoManager:
    def __init__(self):
        self.ffmpeg = settings.FFMPEG_PATH
        self.ffprobe = settings.FFPROBE_PATH

    def extract_metadata(self, media_path: str) -> Dict[str, Any]:
        """Extract duration, resolution, fps, bitrate and codec using ffprobe."""
        if not Path(media_path).exists():
            raise FileNotFoundError(f"Source file not found: {media_path}")

        cmd = [
            self.ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            media_path
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            data = json.loads(res.stdout)

            video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
            audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
            format_info = data.get("format", {})

            duration = float(format_info.get("duration", 0.0))
            if duration == 0.0 and video_stream:
                duration = float(video_stream.get("duration", 0.0))

            width = int(video_stream.get("width", 0)) if video_stream else 0
            height = int(video_stream.get("height", 0)) if video_stream else 0

            # Compute frame rate
            fps = 30.0
            if video_stream and "r_frame_rate" in video_stream:
                r_fps = video_stream["r_frame_rate"]
                if "/" in r_fps:
                    num, den = r_fps.split("/")
                    if float(den) > 0:
                        fps = round(float(num) / float(den), 2)

            return {
                "file_path": media_path,
                "file_name": Path(media_path).name,
                "duration": round(duration, 2),
                "width": width,
                "height": height,
                "aspect_ratio": f"{width}:{height}" if height > 0 else "N/A",
                "fps": fps,
                "video_codec": video_stream.get("codec_name") if video_stream else None,
                "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
                "size_mb": round(os.path.getsize(media_path) / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"Error extracting metadata from {media_path}: {e}")
            raise

    def extract_audio_track(self, video_path: str) -> str:
        """Demux audio track to 16kHz mono 16-bit PCM WAV for optimal Whisper STT accuracy."""
        stem = Path(video_path).stem
        out_wav = str(TEMP_AUDIO_DIR / f"{stem}_whisper.wav")

        # Fast direct audio extraction with FFmpeg
        cmd = [
            self.ffmpeg,
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            out_wav
        ]

        logger.info(f"Demuxing audio from {video_path} -> {out_wav}...")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        return out_wav

    def scan_folder_for_videos(self, folder_path: str) -> List[str]:
        """Scan a folder recursively for video files."""
        valid_exts = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".flv"}
        found = []
        p = Path(folder_path)
        if p.exists() and p.is_dir():
            for f in p.rglob("*"):
                if f.suffix.lower() in valid_exts and f.is_file():
                    found.append(str(f))
        return found

    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """Check if input string is a valid YouTube URL."""
        if not url or not isinstance(url, str):
            return False
        import re
        pattern = r"^(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/.+"
        return bool(re.match(pattern, url.strip()))

    def download_youtube_source(self, url: str) -> Dict[str, Any]:
        """Ingest video source from authorized YouTube URL via yt-dlp with rich metadata."""
        import yt_dlp
        import shutil
        from jarvis.backend.config.settings import WORKSPACE_ROOT
        downloads_dir = OUTPUT_DIR / "downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        out_template = str(downloads_dir / "%(id)s_%(title).60s.%(ext)s")
        ffmpeg_dir = str(Path(self.ffmpeg).parent) if self.ffmpeg else None

        from jarvis.backend.video.ytdlp_utils import get_ytdlp_base_opts, get_ytdlp_download_opts, safe_extract_info

        # Check if URL is an ongoing livestream to avoid infinite download hangs
        try:
            probe_opts = get_ytdlp_base_opts(download=False, quiet=True)
            with yt_dlp.YoutubeDL(probe_opts) as ydl_probe:
                probe_info = ydl_probe.extract_info(url, download=False)
                if probe_info and probe_info.get("is_live"):
                    logger.info(f"Target YouTube URL is an active ongoing livestream! Capturing synchronized rolling slice...")
                    from jarvis.backend.video.livestream_clipper import livestream_clipper
                    return livestream_clipper.capture_live_slice(url, duration_seconds=60)
        except Exception as pe:
            logger.debug(f"Live probe pass: {pe}")

        ydl_opts = get_ytdlp_download_opts(out_template=out_template, ffmpeg_location=ffmpeg_dir)

        logger.info(f"Downloading YouTube video from: {url}")
        info = safe_extract_info(url, download=True, extra_opts=ydl_opts)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            prep_file = Path(ydl.prepare_filename(info))
            if not prep_file.exists():
                prep_file = prep_file.with_suffix(".mp4")
            if not prep_file.exists():
                candidates = list(downloads_dir.glob(f"*{info.get('id')}*.mp4"))
                if candidates:
                    prep_file = candidates[0]

            return {
                "file_path": str(prep_file.resolve()),
                "title": info.get("title", "YouTube Video"),
                "uploader": info.get("uploader", "Unknown Creator"),
                "channel": info.get("channel", info.get("uploader", "Unknown Creator")),
                "description": info.get("description", ""),
                "tags": info.get("tags", []),
                "duration": float(info.get("duration", 0)),
                "url": url,
                "video_id": info.get("id"),
                "thumbnail": info.get("thumbnail")
            }


source_manager = SourceVideoManager()


