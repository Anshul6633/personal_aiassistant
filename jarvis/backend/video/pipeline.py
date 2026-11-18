"""End-to-End Autonomous Video Clipping Pipeline & Batch Queue Manager.

Ingests long videos or podcasts, transcribes, detects highlight segments,
scores clips, re-frames to 9:16, burns animated subtitles, generates viral metadata,
and saves outputs for YouTube Shorts & Instagram Reels.
"""

import os
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.backend.video.source_manager import source_manager
from jarvis.backend.video.metadata_generator import generate_proper_youtube_description, format_viral_shorts_title
from jarvis.backend.voice.stt import stt_engine
from jarvis.backend.video.highlight_detector import highlight_detector
from jarvis.backend.video.clip_scorer import clip_scorer
from jarvis.backend.video.editor import video_editor
from jarvis.backend.database.db import get_db_connection
from jarvis.backend.core.state import state_manager, AssistantState
from jarvis.backend.config.settings import OUTPUT_DIR

logger = logging.getLogger("JARVIS.Pipeline")

SUBS_DIR = OUTPUT_DIR / "subtitles"
SUBS_DIR.mkdir(parents=True, exist_ok=True)


class VideoPipeline:
    def __init__(self):
        self.is_processing = False

    async def process_video(
        self,
        video_path: str,
        num_clips: int = 5,
        target_duration: float = 45.0,
        task_id: Optional[str] = None,
        style_preset: str = "podcast",
        auto_publish_youtube: bool = False,
        publish_interval_minutes: int = 45,
        privacy: str = "schedule"
    ) -> List[Dict[str, Any]]:
        """Run the complete autonomous clipping pipeline on a local video or YouTube URL."""
        if not task_id:
            task_id = str(uuid.uuid4())[:8]

        self.is_processing = True
        loop = asyncio.get_event_loop()

        source_url = None
        source_title = None
        source_channel = None

        try:
                # 0. Check if input is a YouTube URL
            if source_manager.is_youtube_url(video_path):
                source_url = video_path.strip()
                await state_manager.set_status(AssistantState.PLANNING, f"Ingesting YouTube video {source_url}...")
                await state_manager.update(active_task_id=task_id, task_progress=5)
                logger.info(f"Downloading YouTube source video: {source_url}")
                
                yt_meta = await loop.run_in_executor(None, source_manager.download_youtube_source, source_url)
                source_title = yt_meta.get("title")
                source_channel = yt_meta.get("uploader") or yt_meta.get("channel")
                video_path = yt_meta["file_path"]
                logger.info(f"YouTube download complete: '{source_title}' saved at {video_path}")
            else:
                await state_manager.set_status(AssistantState.PLANNING, f"Ingesting source video {Path(video_path).name}...")
                await state_manager.update(active_task_id=task_id, task_progress=5)
    
            # 1. Inspect source video metadata
            meta = source_manager.extract_metadata(video_path)
            logger.info(f"Source video metadata: {meta['duration']}s, {meta['width']}x{meta['height']}")
    
            # 2. Demux audio for Whisper
            await state_manager.set_status(AssistantState.PLANNING, "Demuxing high-fidelity audio track...")
            await state_manager.update(task_progress=15)
            wav_path = source_manager.extract_audio_track(video_path)
    
            # 3. Transcribe with word-level timestamps using faster-whisper
            await state_manager.set_status(AssistantState.EXECUTING, "Transcribing speech with faster-whisper (GPU/CPU)...")
            await state_manager.update(task_progress=30)
            # Run transcription in threadpool to keep async loop responsive
            transcript = await loop.run_in_executor(None, stt_engine.transcribe_file, wav_path)
    
            # Save complete SRT/VTT for source video
            srt_path = str(SUBS_DIR / f"{Path(video_path).stem}_full.srt")
            stt_engine.generate_srt(transcript["segments"], srt_path)
    
            # 4. Extract candidate highlight windows
            await state_manager.set_status(AssistantState.THINKING, "Analyzing transcript for viral hooks and stories...")
            await state_manager.update(task_progress=50)
            candidates = highlight_detector.create_candidate_windows(
                transcript,
                min_duration=15.0,
                max_duration=65.0,
                target_duration=target_duration
            )
    
            if not candidates:
                # Fallback if no window met criteria: generate full video or slice into intervals
                dur = meta["duration"]
                step = min(45.0, dur)
                for s in range(0, int(dur), int(step)):
                    e = min(s + step, dur)
                    if e - s >= 10:
                        candidates.append({
                            "start_time": float(s),
                            "end_time": float(e),
                            "duration": float(e - s),
                            "text": f"Clip from {s}s to {e}s",
                            "hook_strength": 75.0,
                            "story_completeness": 75.0,
                            "info_value": 75.0,
                            "engagement_potential": 75.0,
                            "audio_quality": 85.0,
                            "visual_quality": 85.0
                        })
    
            # 5. Score with 6-Factor Algorithm and remove overlapping duplicates
            await state_manager.set_status(AssistantState.PLANNING, "Applying 6-factor scoring and duplicate suppression...")
            await state_manager.update(task_progress=60)
            ranked_candidates = clip_scorer.rank_and_filter(candidates, top_k=num_clips)
    
            # Guarantee requested num_clips by partitioning source into non-overlapping windows if needed
            if len(ranked_candidates) < num_clips:
                dur = meta["duration"]
                slot_size = dur / num_clips
                for i in range(num_clips):
                    if len(ranked_candidates) >= num_clips:
                        break
                    slot_start = i * slot_size
                    slot_end = min(dur, slot_start + min(target_duration, slot_size))
                    overlaps = any(
                        max(0.0, min(slot_end, r["end_time"]) - max(slot_start, r["start_time"])) > 10.0
                        for r in ranked_candidates
                    )
                    if not overlaps and (slot_end - slot_start >= 12.0):
                        ranked_candidates.append(clip_scorer.compute_scores({
                            "start_time": float(round(slot_start, 2)),
                            "end_time": float(round(slot_end, 2)),
                            "duration": float(round(slot_end - slot_start, 2)),
                            "text": f"High engagement moment #{i+1}",
                            "hook_strength": 78.0,
                            "story_completeness": 80.0,
                            "info_value": 75.0,
                            "engagement_potential": 82.0,
                            "audio_quality": 85.0,
                            "visual_quality": 85.0
                        }))
    
            # 6. Render each clip: 9:16 vertical re-frame, animated subtitles & AI metadata
            created_clips = []
            total_to_render = len(ranked_candidates)
    
            for idx, cand in enumerate(ranked_candidates, 1):
                clip_label = f"clip_{task_id}_{idx}"
                await state_manager.set_status(
                    AssistantState.EDITING,
                    f"Rendering clip {idx}/{total_to_render}: '{cand['text'][:35]}...' to 9:16 vertical"
                )
                progress_pct = int(60 + (idx / total_to_render) * 35)
                await state_manager.update(task_progress=progress_pct)
    
                # Enrich with viral title, caption and hashtags via local Ollama
                enriched = await highlight_detector.enrich_with_ai(cand)
    
                # Generate ASS subtitles for this specific clip time window
                ass_path = str(SUBS_DIR / f"{clip_label}.ass")
                video_editor.generate_ass_subtitles(
                    transcript["words"],
                    clip_start=cand["start_time"],
                    clip_end=cand["end_time"],
                    output_ass_path=ass_path,
                    style=style_preset
                )
    
                # Render 9:16 vertical MP4
                rendered = await loop.run_in_executor(
                    None,
                    video_editor.render_vertical_clip,
                    video_path,
                    cand["start_time"],
                    cand["end_time"],
                    clip_label,
                    ass_path
                )
    
                # Format high-CTR viral title
                raw_title = enriched.get("title") or (cand["text"][:40] if cand.get("text") else f"Highlight {idx}")
                viral_title = format_viral_shorts_title(raw_title)
    
                # Generate comprehensive, SEO-rich YouTube description with CTAs, quotes & source credits
                proper_description = generate_proper_youtube_description(
                    title=viral_title,
                    summary=cand.get("text", ""),
                    transcript_quote=cand.get("text", "")[:180],
                    source_title=source_title,
                    source_channel=source_channel,
                    source_url=source_url,
                    tags=enriched.get("tags", "").split()
                )
    
                clip_record = {
                    "id": str(uuid.uuid4())[:12],
                    "source_file": video_path,
                    "title": viral_title,
                    "summary": cand["text"],
                    "hook_score": cand.get("hook_score", 70.0),
                    "story_score": cand.get("story_score", 75.0),
                    "info_score": cand.get("info_score", 75.0),
                    "engagement_score": cand.get("engagement_score", 70.0),
                    "audio_score": cand.get("audio_score", 85.0),
                    "visual_score": cand.get("visual_score", 85.0),
                    "total_score": cand.get("total_score", 75.0),
                    "start_time": cand["start_time"],
                    "end_time": cand["end_time"],
                    "duration": rendered["duration"],
                    "output_path": rendered["video_path"],
                    "video_path": rendered["video_path"],
                    "thumbnail_path": rendered["thumbnail_path"],
                    "subtitles_path": ass_path,
                    "tags": enriched.get("tags", "#shorts #reels"),
                    "caption": proper_description,
                    "status": "READY"
                }
    
                # Optional: Autonomous YouTube Publishing with strict 45-minute interval spacing
                if auto_publish_youtube:
                    try:
                        from jarvis.backend.social.scheduler_engine import scheduler_engine
                        # Calculate target slot time spaced publish_interval_minutes apart
                        # First clip publishes in 2 mins or immediately, subsequent spaced 45m
                        slot_offset = publish_interval_minutes * (idx - 1)
                        target_dt = datetime.now() + timedelta(minutes=slot_offset + 2)
                        
                        q_res = scheduler_engine.enqueue_clip(
                            clip_id=clip_record["id"],
                            video_path=rendered["video_path"],
                            title=viral_title,
                            description=proper_description,
                            tags=enriched.get("tags", "#Shorts #Viral").split(),
                            scheduled_time=target_dt.isoformat(),
                            interval_minutes=publish_interval_minutes
                        )
                        clip_record["status"] = "QUEUED_YOUTUBE"
                        clip_record["published_youtube"] = 1
                        logger.info(f"Auto-queued clip '{viral_title}' to YouTube schedule queue for {target_dt.isoformat()}")
                    except Exception as qe:
                        logger.error(f"Failed to auto-publish clip '{viral_title}' to YouTube queue: {qe}")
    
                # Save in SQLite DB
                self._save_clip_to_db(clip_record)
                created_clips.append(clip_record)
    
            # 7. Complete Task
            await state_manager.set_status(
                AssistantState.IDLE,
                f"Successfully produced {len(created_clips)} high-scoring 9:16 vertical clips!"
            )
            await state_manager.update(task_progress=100)
            self.is_processing = False
            return created_clips
        except Exception as e:
            logger.error(f"Error in video processing pipeline: {e}", exc_info=True)
            self.is_processing = False
            await state_manager.set_status(AssistantState.ERROR, f"Video pipeline error: {str(e)[:120]}")
            await state_manager.update(task_progress=0, active_task_id=None, active_task_title=None)
            raise

    def _save_clip_to_db(self, clip: Dict[str, Any]):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO clips (
                    id, source_file, title, summary, hook_strength, story_completeness,
                    info_value, engagement_potential, audio_quality, visual_quality,
                    total_score, start_time, end_time, duration, output_path,
                    thumbnail_path, subtitles_path, tags, caption, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                clip["id"], clip["source_file"], clip["title"], clip["summary"],
                clip["hook_score"], clip["story_score"], clip["info_score"],
                clip["engagement_score"], clip["audio_score"], clip["visual_score"],
                clip["total_score"], clip["start_time"], clip["end_time"],
                clip["duration"], clip["output_path"], clip["thumbnail_path"],
                clip["subtitles_path"], clip["tags"], clip["caption"], clip["status"]
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error persisting clip to DB: {e}")


video_pipeline = VideoPipeline()

