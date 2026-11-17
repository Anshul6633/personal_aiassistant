"""Long video to multiple short clips conversion skill for JARVIS.

Ingests full-length podcasts, discussions, interviews, or lectures and autonomously:
1. Demuxes & transcribes audio using local faster-whisper.
2. Discovers high-scoring standalone hooks and storytelling segments.
3. Automatically reframes into 9:16 vertical format (1080x1920).
4. Generates animated word-level ASS subtitles.
5. Saves clips ready for YouTube Shorts and Instagram Reels.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.backend.video.pipeline import video_pipeline
from jarvis.backend.video.source_manager import source_manager
from jarvis.backend.database.db import get_db_connection

logger = logging.getLogger("JARVIS.Skill.LongVideoToShorts")


async def convert_long_video_to_shorts(
    video_path: str,
    num_clips: int = 5,
    target_duration: float = 45.0,
    style_preset: str = "podcast"
) -> Dict[str, Any]:
    """Slice and convert a single long video into multiple short vertical clips."""
    src = Path(video_path)
    if not src.exists():
        raise FileNotFoundError(f"Source video not found at: {video_path}")

    # Inspect source duration
    meta = source_manager.extract_metadata(str(src))
    total_duration = meta.get("duration", 0)

    logger.info(f"Initiating long-to-shorts pipeline on '{src.name}' ({total_duration}s) -> targeting {num_clips} clips")

    # Start processing in background pipeline
    task = asyncio.create_task(
        video_pipeline.process_video(
            video_path=str(src),
            num_clips=num_clips,
            target_duration=target_duration,
            style_preset=style_preset
        )
    )

    return {
        "status": "PROCESSING_STARTED",
        "video_path": str(src),
        "source_name": src.name,
        "source_duration_sec": total_duration,
        "requested_clips": num_clips,
        "target_duration_sec": target_duration,
        "style_preset": style_preset
    }


def list_processed_shorts(limit: int = 30) -> List[Dict[str, Any]]:
    """Retrieve all ready vertical shorts created by JARVIS."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, source_file, title, summary, total_score, start_time, end_time,
               duration, output_path, thumbnail_path, tags, caption, status, created_at
        FROM clips
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        out_p = Path(d.get("output_path", ""))
        thumb_p = Path(d.get("thumbnail_path", ""))
        d["video_url"] = f"/output/reels/{out_p.name}" if out_p.exists() else None
        d["thumb_url"] = f"/output/thumbnails/{thumb_p.name}" if thumb_p.exists() else None
        results.append(d)

    return results

