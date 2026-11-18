"""YouTube video downloader skill for JARVIS.

Powered by yt-dlp and local FFmpeg. Zero paid API cost.
Downloads video/audio from YouTube and prepares it for clipping into multiple Shorts & Reels.
"""

import os
import re
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yt_dlp

from jarvis.backend.config.settings import OUTPUT_DIR, WORKSPACE_ROOT
from jarvis.backend.core.state import state_manager, AssistantState

from jarvis.backend.video.ytdlp_utils import safe_extract_info, get_ytdlp_download_opts

logger = logging.getLogger("JARVIS.Skill.YouTubeDownloader")

DOWNLOADS_DIR = OUTPUT_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
FFMPEG_BIN_DIR = str(WORKSPACE_ROOT / "jarvis" / "assets" / "bin")


def sanitize_filename(name: str) -> str:
    """Remove invalid filesystem characters."""
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")[:60]


def extract_metadata(url: str) -> Dict[str, Any]:
    """Inspect YouTube video metadata without downloading."""
    info = safe_extract_info(url, download=False)
    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "duration": info.get("duration", 0),
        "uploader": info.get("uploader"),
        "view_count": info.get("view_count"),
        "thumbnail": info.get("thumbnail"),
        "description": (info.get("description") or "")[:200]
    }


def download_youtube_video(
    url: str,
    output_dir: Optional[Path] = None,
    auto_clip: bool = False,
    num_clips: int = 5,
    target_duration: float = 45.0,
    style_preset: str = "podcast"
) -> Dict[str, Any]:
    """Download a YouTube video into MP4 format and optionally trigger multi-clip extraction."""
    target_dir = output_dir or DOWNLOADS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    out_template = str(target_dir / "%(id)s_%(title).50s.%(ext)s")
    ydl_opts = get_ytdlp_download_opts(out_template=out_template, ffmpeg_location=FFMPEG_BIN_DIR)

    logger.info(f"Downloading YouTube video from: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Determine actual file downloaded
        expected_filename = ydl.prepare_filename(info)
        file_path = Path(expected_filename)
        if not file_path.exists():
            file_path = file_path.with_suffix(".mp4")
        if not file_path.exists():
            candidates = list(target_dir.glob(f"*{info.get('id')}*.mp4"))
            if candidates:
                file_path = candidates[0]

        file_size_mb = round(file_path.stat().st_size / (1024 * 1024), 2) if file_path.exists() else 0

        result = {
            "status": "DOWNLOAD_COMPLETED",
            "video_id": info.get("id"),
            "title": info.get("title"),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader"),
            "file_path": str(file_path),
            "file_name": file_path.name,
            "thumbnail": info.get("thumbnail"),
            "file_size_mb": file_size_mb,
            "ready_for_editing": file_path.exists()
        }

    # If auto_clip is enabled, schedule video_pipeline in background
    if auto_clip and file_path.exists():
        from jarvis.backend.video.pipeline import video_pipeline
        import threading
        logger.info(f"Auto-clipping requested: splitting '{file_path.name}' into {num_clips} short vertical clips")

        def _run_clipping():
            try:
                asyncio.run(
                    video_pipeline.process_video(
                        str(file_path),
                        num_clips=num_clips,
                        target_duration=target_duration,
                        style_preset=style_preset
                    )
                )
            except Exception as ex:
                logger.error(f"Background clipping error: {ex}", exc_info=True)

        threading.Thread(target=_run_clipping, daemon=True).start()
        result["clipping_status"] = "CLIPPING_PIPELINE_INITIATED"
        result["num_clips_queued"] = num_clips

    return result


def list_downloaded_podcasts() -> list:
    """Return all downloaded podcast and long-form videos ready for editing."""
    podcasts = []
    if not DOWNLOADS_DIR.exists():
        return podcasts

    for p in sorted(DOWNLOADS_DIR.glob("*.mp4"), key=os.path.getmtime, reverse=True):
        if p.name.endswith(".part"):
            continue
        try:
            sz = round(p.stat().st_size / (1024 * 1024), 2)
            mtime = os.path.getmtime(p)
            # Clean title from filename
            name_part = p.stem
            if "_" in name_part:
                parts = name_part.split("_", 1)
                title = parts[1] if len(parts) > 1 else parts[0]
            else:
                title = name_part

            podcasts.append({
                "id": p.stem[:11],
                "filename": p.name,
                "file_path": str(p.resolve()),
                "title": title.replace("_", " "),
                "size_mb": sz,
                "created_at": mtime,
                "ready_for_editing": True
            })
        except Exception:
            continue

    return podcasts

