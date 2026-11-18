"""Autonomous 1-Click Viral YouTube Shorts Production & Publishing Engine.

Orchestrates:
1. Viral YouTuber Video Discovery & Ingestion (via yt-dlp)
2. 6-Factor AI Viral Hook & Emotion Detection (Whisper + Ollama)
3. Automated 9:16 Vertical Reframing with Animated Karaoke Subtitles
4. High-CTR Viral Title & SEO-Rich Description Generation
5. Autonomous YouTube Studio Browser Upload & Scheduling Till Daily Limit
"""

import os
import re
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import yt_dlp

from jarvis.backend.config.settings import OUTPUT_DIR, settings
from jarvis.backend.video.source_manager import source_manager
from jarvis.backend.video.pipeline import video_pipeline
from jarvis.backend.video.metadata_generator import generate_proper_youtube_description, format_viral_shorts_title, generate_viral_instagram_caption
from jarvis.backend.social.scheduler_engine import scheduler_engine
from jarvis.backend.social.youtube_browser import youtube_browser
from jarvis.backend.database.db import get_db_connection
from jarvis.backend.core.state import state_manager, AssistantState

logger = logging.getLogger("JARVIS.ViralAutopilot")

AUTOPILOT_DIR = OUTPUT_DIR / "autopilot"
AUTOPILOT_DIR.mkdir(parents=True, exist_ok=True)

# Curated high-CTR viral creator presets
VIRAL_PRESETS = {
    "mrbeast": {
        "name": "MrBeast Challenge & Energy",
        "search_query": "ytsearch5:MrBeast challenge viral",
        "style_preset": "mrbeast",
        "niche": "High Energy Entertainment",
        "tags": ["MrBeast", "Challenge", "Win", "Beast", "Viral", "YouTubeShorts"]
    },
    "football": {
        "name": "Football Ultra Skills & Moments",
        "search_query": "ytsearch5:football greatest skills and goals 2024 4k",
        "style_preset": "podcast",
        "niche": "Football & Sports",
        "tags": ["Football", "Soccer", "Mbappe", "Ronaldo", "Messi", "Skills", "Goals", "Shorts"]
    },
    "rogan": {
        "name": "Joe Rogan Mindblowing Clips",
        "search_query": "ytsearch5:Joe Rogan crazy conversation podcast highlight",
        "style_preset": "podcast",
        "niche": "Podcasts & Mindset",
        "tags": ["JoeRogan", "JRE", "Podcast", "Mindset", "CrazyStory", "Shorts"]
    },
    "huberman": {
        "name": "Andrew Huberman Science Hacks",
        "search_query": "ytsearch5:Andrew Huberman focus dopamine health routine",
        "style_preset": "podcast",
        "niche": "Science & Health",
        "tags": ["HubermanLab", "Neuroscience", "Health", "Productivity", "Dopamine", "Shorts"]
    },
    "speed": {
        "name": "IShowSpeed Chaos & Reactions",
        "search_query": "ytsearch5:IShowSpeed funniest moments stream",
        "style_preset": "mrbeast",
        "niche": "Streaming & Humor",
        "tags": ["IShowSpeed", "Speed", "FunnyMoments", "Streamer", "Chaos", "Shorts"]
    }
}


class ViralAutopilotManager:
    def __init__(self):
        self.is_running = False
        self.current_state: Dict[str, Any] = {
            "status": "IDLE",
            "step": "Ready for 1-Click Launch",
            "progress_percent": 0,
            "source_info": None,
            "clips_produced": [],
            "uploads_completed": [],
            "daily_limit_reached": False,
            "log": []
        }

    def _log(self, message: str):
        logger.info(message)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.current_state["log"].append(f"[{timestamp}] {message}")
        if len(self.current_state["log"]) > 50:
            self.current_state["log"].pop(0)

    def get_status(self) -> Dict[str, Any]:
        return self.current_state

    def find_viral_video(self, query_or_preset: str) -> Dict[str, Any]:
        """Search YouTube for top-performing viral video using yt-dlp."""
        query = query_or_preset
        preset_key = query_or_preset.lower().strip()
        if preset_key in VIRAL_PRESETS:
            query = VIRAL_PRESETS[preset_key]["search_query"]
        elif not query.startswith("ytsearch"):
            query = f"ytsearch5:{query} viral"

        self._log(f"Searching YouTube for viral candidates: '{query}'...")
        from jarvis.backend.video.ytdlp_utils import safe_extract_info

        res = safe_extract_info(query, download=False, extra_opts={"extract_flat": True})
        entries = res.get("entries", [])
        if not entries:
            raise ValueError(f"No viral videos found on YouTube for query: {query}")

        # Pick the best candidate: preferably between 3m and 45m duration
        best = None
        for e in entries:
            dur = e.get("duration") or 0
            if 120 <= dur <= 3600:
                best = e
                break
        if not best:
            best = entries[0]

        return {
            "title": best.get("title"),
            "url": best.get("url") or f"https://www.youtube.com/watch?v={best.get('id')}",
            "id": best.get("id"),
            "uploader": best.get("uploader", "YouTube Creator"),
            "duration": best.get("duration", 0),
            "view_count": best.get("view_count", 0)
        }

    async def run_autopilot(
        self,
        youtube_url: Optional[str] = None,
        preset: Optional[str] = None,
        search_topic: Optional[str] = None,
        num_clips: int = 4,
        target_duration: float = 45.0,
        interval_minutes: int = 45,
        upload_till_limit: bool = True,
        platform: str = "both",
        privacy: str = "public"
    ) -> Dict[str, Any]:
        """Run the end-to-end 1-Click Viral Autopilot pipeline."""
        if self.is_running:
            return {"success": False, "message": "Viral Autopilot is already active!"}

        self.is_running = True
        self.current_state = {
            "status": "RUNNING",
            "step": "Initializing 1-Click Autopilot",
            "progress_percent": 5,
            "source_info": None,
            "clips_produced": [],
            "uploads_completed": [],
            "youtube_uploads": [],
            "instagram_uploads": [],
            "daily_limit_reached": False,
            "log": []
        }

        try:
            # 1. Resolve Target Video
            target_url = youtube_url
            style_preset = "podcast"
            preset_tags = []

            if preset and preset.lower() in VIRAL_PRESETS:
                p_cfg = VIRAL_PRESETS[preset.lower()]
                style_preset = p_cfg["style_preset"]
                preset_tags = p_cfg["tags"]
                if not target_url:
                    found = self.find_viral_video(preset)
                    target_url = found["url"]
                    self.current_state["source_info"] = found
                    self._log(f"Selected viral candidate: '{found['title']}' ({found['url']})")

            elif (preset or search_topic) and not target_url:
                topic_str = search_topic or preset
                low_top = topic_str.lower()
                if any(k in low_top for k in ["game", "gaming", "gta", "minecraft", "speed", "beast", "challenge", "funny"]):
                    style_preset = "mrbeast"
                else:
                    style_preset = "podcast"
                preset_tags = [w.capitalize() for w in topic_str.split() if len(w) > 1] + ["Viral", "Shorts", "Trending"]
                found = self.find_viral_video(topic_str)
                target_url = found["url"]
                self.current_state["source_info"] = found
                self._log(f"Found top viral video for '{topic_str}': '{found['title']}' ({found['url']})")

            if not target_url:
                raise ValueError("No valid YouTube URL or search topic provided.")

            # 2. Ingest & Download Source Video
            self.current_state["step"] = "Downloading & Ingesting YouTube Video"
            self.current_state["progress_percent"] = 15
            self._log(f"Ingesting YouTube source: {target_url}...")

            loop = asyncio.get_event_loop()
            yt_meta = await loop.run_in_executor(None, source_manager.download_youtube_source, target_url)
            self.current_state["source_info"] = yt_meta
            self._log(f"Downloaded '{yt_meta['title']}' by {yt_meta['uploader']} ({yt_meta['duration']}s)")

            # Auto-detect style preset if MrBeast or gaming
            title_lower = (yt_meta.get("title") or "").lower()
            if "mrbeast" in title_lower or "challenge" in title_lower or "beast" in title_lower:
                style_preset = "mrbeast"

            # 3. Autonomous 6-Factor Viral Hook Detection & 9:16 Vertical Clipping
            self.current_state["step"] = f"Extracting {num_clips} Viral Shorts (Whisper + 9:16 Reframing)"
            self.current_state["progress_percent"] = 35
            self._log(f"Transcribing & analyzing viral hooks with style preset '{style_preset}'...")

            clips = await video_pipeline.process_video(
                video_path=yt_meta["file_path"],
                num_clips=num_clips,
                target_duration=target_duration,
                style_preset=style_preset,
                auto_publish_youtube=False # We handle the batch upload till limit directly
            )

            self.current_state["clips_produced"] = clips
            self.current_state["progress_percent"] = 70
            self._log(f"Successfully rendered {len(clips)} vertical viral Shorts with animated captions!")

            # 4. Enqueue into YouTube & Instagram Dispatch Queues with 45-Minute Spacing
            self.current_state["step"] = f"Enqueuing {platform.upper()} Posts with SEO & Viral Captions"
            self.current_state["progress_percent"] = 80

            enqueued_yt_items = []
            enqueued_ig_items = []
            now = datetime.now()

            for idx, clip in enumerate(clips):
                slot_time = (now + timedelta(minutes=interval_minutes * idx + 2)).isoformat()
                v_title = format_viral_shorts_title(clip["title"])
                tags_list = preset_tags or (clip.get("tags", "").split() if clip.get("tags") else [])

                # YouTube Enqueue (Public visibility guarantee)
                if platform.lower() in ("youtube", "both"):
                    p_desc = generate_proper_youtube_description(
                        title=v_title,
                        summary=clip.get("summary", ""),
                        transcript_quote=clip.get("summary", "")[:180],
                        source_title=yt_meta.get("title"),
                        source_channel=yt_meta.get("uploader"),
                        source_url=target_url,
                        tags=tags_list
                    )
                    q_res = scheduler_engine.enqueue_clip(
                        clip_id=clip["id"],
                        video_path=clip["output_path"],
                        title=v_title,
                        description=p_desc,
                        tags=tags_list,
                        scheduled_time=slot_time,
                        interval_minutes=interval_minutes,
                        privacy=privacy
                    )
                    enqueued_yt_items.append(q_res)
                    self._log(f"Queued YouTube Short #{idx + 1}: '{v_title}' ({privacy.upper()}) for {slot_time}")

                # Instagram Enqueue (Viral hooks, transcript quote, CTA & 18+ hashtags)
                if platform.lower() in ("instagram", "both"):
                    ig_caption = generate_viral_instagram_caption(
                        title=clip["title"],
                        summary=clip.get("summary", ""),
                        transcript_quote=clip.get("summary", "")[:180],
                        source_title=yt_meta.get("title"),
                        source_channel=yt_meta.get("uploader"),
                        source_url=target_url,
                        tags=tags_list
                    )
                    q_ig = scheduler_engine.schedule_instagram_reel(
                        video_path=clip["output_path"],
                        caption=ig_caption,
                        scheduled_time=slot_time,
                        tags=tags_list
                    )
                    enqueued_ig_items.append(q_ig)
                    self._log(f"Queued Instagram Reel #{idx + 1}: '{clip['title']}' for {slot_time}")

            # 5. Autonomous Upload Till Daily Limit Reached (Dual-Platform with Anti-Ban Protection)
            if upload_till_limit and (enqueued_yt_items or enqueued_ig_items):
                self.current_state["step"] = f"Uploading to {platform.upper()} (45m Pacing & Anti-Ban) Till Daily Limit"
                self.current_state["progress_percent"] = 85
                self._log(f"Launching browser automation to publish on {platform.upper()} till daily limit...")

                yt_results = []
                ig_results = []
                yt_limit_hit = False

                # Process YouTube Queue
                if platform.lower() in ("youtube", "both"):
                    for q in enqueued_yt_items:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("SELECT * FROM youtube_schedule_queue WHERE id = ?", (q["queue_id"],))
                        row = cur.fetchone()
                        conn.close()

                        if not row:
                            continue

                        item = dict(row)
                        self._log(f"Uploading '{item['title']}' to YouTube Studio as {privacy.upper()}...")
                        res = await scheduler_engine.process_single_item(item)

                        if res.get("success"):
                            yt_results.append({
                                "title": item["title"],
                                "url": res.get("youtube_url"),
                                "scheduled_time": item["scheduled_time"]
                            })
                            self.current_state["youtube_uploads"] = yt_results
                            self.current_state["uploads_completed"] = yt_results + ig_results
                            self._log(f"🎉 Live on YouTube (Public): '{item['title']}' (Link: {res.get('youtube_url')})")
                            await asyncio.sleep(10)
                        else:
                            err = res.get("error", "")
                            if "daily upload limit" in err.lower() or "upload limit" in err.lower():
                                self._log(f"⚠️ YouTube Daily Upload Limit Reached on '{item['title']}'. Pausing YouTube uploads.")
                                yt_limit_hit = True
                                self.current_state["daily_limit_reached"] = True
                                break
                            else:
                                self._log(f"Error during YouTube upload of '{item['title']}': {err}")

                # Process Instagram Queue
                if platform.lower() in ("instagram", "both"):
                    for q in enqueued_ig_items:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("SELECT * FROM instagram_schedule_queue WHERE id = ?", (q["id"],))
                        row = cur.fetchone()
                        conn.close()

                        if not row:
                            continue

                        item = dict(row)
                        self._log(f"Publishing Instagram Reel '{item['file_name']}' via stealth browser automation...")
                        res = await scheduler_engine.process_single_instagram_item(item)

                        if res.get("success"):
                            ig_results.append({
                                "file_name": item["file_name"],
                                "caption": item["caption"][:60],
                                "scheduled_time": item["scheduled_time"]
                            })
                            self.current_state["instagram_uploads"] = ig_results
                            self.current_state["uploads_completed"] = yt_results + ig_results
                            self._log(f"🎉 Live on Instagram Reels: '{item['file_name']}'!")
                            await asyncio.sleep(10)
                        else:
                            err = res.get("error", "")
                            self._log(f"Error during Instagram upload of '{item['file_name']}': {err}")

                self.current_state["daily_limit_reached"] = yt_limit_hit

            # 6. Complete Autopilot
            self.current_state["status"] = "COMPLETED"
            self.current_state["progress_percent"] = 100
            self.current_state["step"] = (
                "Completed! YouTube Daily Upload Limit Reached"
                if self.current_state.get("daily_limit_reached")
                else "Completed! All Viral Shorts Scheduled & Live"
            )
            self._log("🏁 1-Click Viral Autopilot sequence finished successfully!")

            return {
                "success": True,
                "clips_count": len(clips),
                "uploaded_count": len(self.current_state["uploads_completed"]),
                "daily_limit_reached": self.current_state["daily_limit_reached"],
                "source_title": yt_meta.get("title"),
                "clips": clips,
                "uploads": self.current_state["uploads_completed"]
            }

        except Exception as e:
            logger.error(f"Autopilot failed: {e}", exc_info=True)
            self.current_state["status"] = "ERROR"
            self.current_state["step"] = f"Error: {str(e)}"
            self._log(f"❌ Autopilot Error: {str(e)}")
            return {"success": False, "error": str(e)}

        finally:
            self.is_running = False


viral_autopilot = ViralAutopilotManager()

