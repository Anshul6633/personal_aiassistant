"""Video factory skill actions for JARVIS."""

import asyncio
from typing import Dict, Any, List
from jarvis.backend.video.pipeline import video_pipeline
from jarvis.backend.database.db import get_db_connection


def trigger_pipeline(video_path: str, num_clips: int = 3, target_duration: float = 45.0):
    asyncio.create_task(video_pipeline.process_video(video_path, num_clips=num_clips, target_duration=target_duration))
    return {"status": "PIPELINE_INITIATED", "video_path": video_path, "num_clips": num_clips}


def list_saved_clips(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clips ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

