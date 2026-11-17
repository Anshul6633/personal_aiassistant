"""Autonomous YouTube Live Stream Capture & Instant Clipping Engine.

Enables JARVIS to ingest ongoing, real-time live broadcasts (gaming streams,
news, podcasts, talk shows), capture a recent synchronized rolling slice,
and immediately process it through the 6-factor AI hook detector and 9:16
vertical video reframer with animated subtitles.
"""

import os
import re
import uuid
import shutil
import asyncio
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import yt_dlp

from jarvis.backend.config.settings import OUTPUT_DIR, WORKSPACE_ROOT
from jarvis.backend.video.source_manager import source_manager
from jarvis.backend.video.pipeline import video_pipeline
from jarvis.backend.core.state import state_manager, AssistantState

logger = logging.getLogger("JARVIS.LivestreamClipper")

LIVESTREAM_DIR = OUTPUT_DIR / "livestreams"
LIVESTREAM_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_LIVE_TOPICS = [
    "live gaming stream 24/7",
    "live news context and analysis",
    "live podcast conversation stream",
    "live esports tournament stream",
    "live tech discussion stream"
]


class LivestreamClipperManager:
    def __init__(self):
        self.is_running = False
        self.ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
        self.current_state: Dict[str, Any] = {
            "status": "IDLE",
            "step": "Standing by for live stream directive",
            "progress_percent": 0,
            "live_info": None,
            "slice_path": None,
            "clips_produced": [],
            "log": []
        }

    def _log(self, message: str):
        logger.info(message)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.current_state["log"].append(f"[{timestamp}] {message}")
        if len(self.current_state["log"]) > 40:
            self.current_state["log"].pop(0)

    def get_status(self) -> Dict[str, Any]:
        return self.current_state

    def discover_live_streams(self, query: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search YouTube for active, ongoing live streams."""
        search_query = query.strip() if (query and query.strip()) else "live stream 24/7"
        if not search_query.startswith("ytsearch"):
            search_query = f"ytsearch10:{search_query}"

        self._log(f"Searching YouTube for ongoing live streams: '{search_query}'...")
        opts = {
            "quiet": True,
            "extract_flat": True,
            "skip_download": True,
            "remote_components": ["ejs:github"]
        }
        node_path = shutil.which("node")
        if node_path:
            opts["js_runtimes"] = {"node": {"path": node_path}}

        live_results = []
        with yt_dlp.YoutubeDL(opts) as ydl:
            res = ydl.extract_info(search_query, download=False)
            entries = res.get("entries", [])
            for e in entries:
                if not e:
                    continue
                is_live = e.get("is_live") or e.get("live_status") == "is_live"
                if is_live:
                    vid_id = e.get("id")
                    live_results.append({
                        "id": vid_id,
                        "title": e.get("title", "Live Stream"),
                        "url": f"https://www.youtube.com/watch?v={vid_id}",
                        "uploader": e.get("uploader", "Live Broadcaster"),
                        "is_live": True
                    })
                    if len(live_results) >= limit:
                        break

        # Fallback if specific query didn't have active live streams: check popular streams
        if not live_results and query:
            return self.discover_live_streams(query=None, limit=limit)

        return live_results

    def capture_live_slice(self, live_url: str, duration_seconds: int = 60) -> Dict[str, Any]:
        """Extract live HLS stream manifests and record synchronized rolling slice."""
        self._log(f"Extracting live stream manifest from: {live_url}...")
        browser_profile = WORKSPACE_ROOT / "jarvis" / "browser_profile"
        node_path = shutil.which("node")

        opts = {
            "quiet": True,
            "skip_download": True,
            "remote_components": ["ejs:github"]
        }
        if node_path:
            opts["js_runtimes"] = {"node": {"path": node_path}}

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(live_url, download=False)
            title = info.get("title", "Live Stream")
            uploader = info.get("uploader", "Broadcaster")
            formats = info.get("formats", [])

            # Locate video-capable and audio-capable HLS streams
            v_formats = [f for f in formats if f.get("vcodec") != "none" and ("m3u8" in f.get("url", "") or f.get("protocol") in ["m3u8", "m3u8_native"])]
            a_formats = [f for f in formats if f.get("acodec") != "none" and ("m3u8" in f.get("url", "") or f.get("protocol") in ["m3u8", "m3u8_native"])]

            if not v_formats:
                # Combined format fallback
                v_formats = [f for f in formats if "m3u8" in f.get("url", "")]

            if not v_formats:
                raise ValueError(f"Could not extract live HLS stream URLs from {live_url}")

            best_v = v_formats[-1]
            best_a = a_formats[-1] if a_formats else None

        safe_stem = re.sub(r"[^\w\-]", "_", title)[:40]
        slice_id = str(uuid.uuid4())[:8]
        out_slice = LIVESTREAM_DIR / f"live_{safe_stem}_{slice_id}.mp4"

        self._log(f"Recording {duration_seconds}s slice of live stream with FFmpeg...")

        # Build FFmpeg dual or single-input recording command
        if best_a and best_a.get("url") != best_v.get("url"):
            cmd = [
                self.ffmpeg,
                "-y",
                "-i", best_v["url"],
                "-i", best_a["url"],
                "-t", str(duration_seconds),
                "-c:v", "copy",
                "-c:a", "aac",
                str(out_slice)
            ]
        else:
            cmd = [
                self.ffmpeg,
                "-y",
                "-i", best_v["url"],
                "-t", str(duration_seconds),
                "-c:v", "copy",
                "-c:a", "aac",
                str(out_slice)
            ]

        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0 or not out_slice.exists() or out_slice.stat().st_size == 0:
            raise RuntimeError(f"FFmpeg failed to record live stream slice: {proc.stderr[:200]}")

        meta = source_manager.extract_metadata(str(out_slice))
        self._log(f"Successfully recorded live slice ({meta['duration']}s, {meta['width']}x{meta['height']})")

        return {
            "title": title,
            "uploader": uploader,
            "url": live_url,
            "file_path": str(out_slice.resolve()),
            "duration": meta["duration"],
            "width": meta["width"],
            "height": meta["height"],
            "audio_codec": meta["audio_codec"]
        }

    async def clip_ongoing_livestream(
        self,
        live_url_or_topic: Optional[str] = None,
        duration_seconds: int = 60,
        num_clips: int = 2,
        target_clip_duration: float = 30.0,
        style_preset: str = "podcast",
        auto_upload_youtube: bool = False,
        visibility: str = "public"
    ) -> Dict[str, Any]:
        """End-to-end autonomous live stream capture, hook analysis, and 9:16 short rendering."""
        if self.is_running:
            return {"success": False, "message": "A live stream capture is already actively running!"}

        self.is_running = True
        self.current_state = {
            "status": "RUNNING",
            "step": "Discovering active live stream",
            "progress_percent": 10,
            "live_info": None,
            "slice_path": None,
            "clips_produced": [],
            "log": []
        }

        try:
            target_url = live_url_or_topic

            # 1. Resolve live stream URL if a topic or empty string was provided
            if not target_url or not source_manager.is_youtube_url(target_url):
                topic = live_url_or_topic or "live news analysis"
                candidates = self.discover_live_streams(topic, limit=3)
                if not candidates:
                    candidates = self.discover_live_streams("live stream 24/7", limit=3)
                if not candidates:
                    raise ValueError(f"No active live streams could be discovered on YouTube.")
                selected = candidates[0]
                target_url = selected["url"]
                self.current_state["live_info"] = selected
                self._log(f"Targeting active live stream: '{selected['title']}' ({target_url})")

            # 2. Record rolling live stream slice with FFmpeg
            # Ensure slice is long enough to yield requested num_clips (each clip needs ~45s)
            actual_duration = max(duration_seconds, int(num_clips * 45))
            self.current_state["step"] = f"Recording {actual_duration}s rolling slice from live broadcast"
            self.current_state["progress_percent"] = 30
            await state_manager.set_status(AssistantState.EXECUTING, f"Capturing live stream slice ({actual_duration}s)...")

            loop = asyncio.get_event_loop()
            capture_meta = await loop.run_in_executor(None, self.capture_live_slice, target_url, actual_duration)
            self.current_state["slice_path"] = capture_meta["file_path"]
            self.current_state["live_info"] = capture_meta

            # 3. Process captured slice through 6-factor AI pipeline
            self.current_state["step"] = f"Transcribing & rendering {num_clips} vertical 9:16 viral shorts"
            self.current_state["progress_percent"] = 60
            await state_manager.set_status(AssistantState.EXECUTING, "Transcribing live stream & detecting viral hooks...")
            self._log(f"Extracting {num_clips} viral hooks from live slice with Whisper + animated subtitles...")

            clips = await video_pipeline.process_video(
                video_path=capture_meta["file_path"],
                num_clips=num_clips,
                target_duration=target_clip_duration,
                style_preset=style_preset,
                auto_publish_youtube=False
            )

            self.current_state["clips_produced"] = clips

            # 4. Optional Autonomous YouTube Studio Upload
            upload_result = None
            if auto_upload_youtube and clips:
                self.current_state["step"] = "Publishing live stream Short to YouTube Studio via Playwright"
                self._log("Initiating Playwright browser automation to publish live stream Short to YouTube Studio...")
                await state_manager.set_status(AssistantState.EXECUTING, "Publishing live stream Short to YouTube Studio...")
                from jarvis.backend.social.youtube_browser import youtube_browser
                from jarvis.backend.social.scheduler_engine import scheduler_engine
                from jarvis.backend.database.db import get_db_connection
                from datetime import datetime, timedelta

                # Pause background scheduler queue to avoid Playwright profile collision
                scheduler_engine.pause_queue()
                try:
                    best_clip = clips[0]
                    short_path = best_clip.get("output_path") or best_clip.get("video_path")
                    raw_title = best_clip.get("title") or f"Insane Live Stream Moment: {capture_meta.get('title', 'Gaming')[:40]}"
                    if "#Shorts" not in raw_title and "#shorts" not in raw_title:
                        raw_title += " #Shorts"
                    short_desc = best_clip.get("caption") or best_clip.get("description") or f"Captured live from ongoing broadcast: {capture_meta.get('title', 'Gaming Stream')}!\n\n#Shorts #Gaming #LiveStream #Viral"
                    tags = ["Shorts", "Gaming", "LiveStream", "Viral", "Trending"]

                    upload_res = await youtube_browser.upload_video(
                        video_path=short_path,
                        title=raw_title,
                        description=short_desc,
                        tags=tags,
                        privacy=visibility
                    )
                    upload_result = upload_res
                    self.current_state["upload_result"] = upload_res
                    self._log(f"🚀 YouTube Studio upload complete: {upload_res.get('status')} | URL: {upload_res.get('video_url')}")

                    # Update status in DB
                    try:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE clips SET status = 'PUBLISHED', published_youtube = ? WHERE output_path = ?",
                            (upload_res.get("video_url") or "PUBLISHED_STUDIO", short_path)
                        )
                        conn.commit()
                        conn.close()
                    except Exception as de:
                        logger.warning(f"Could not update published status in DB: {de}")

                    # Enqueue remaining clips spaced 45m apart
                    for rem_idx, rem_clip in enumerate(clips[1:], 1):
                        slot_dt = datetime.now() + timedelta(minutes=45 * rem_idx)
                        rem_title = rem_clip.get("title") or f"Live Stream Highlight #{rem_idx+1} #Shorts"
                        if "#Shorts" not in rem_title and "#shorts" not in rem_title:
                            rem_title += " #Shorts"
                        rem_desc = rem_clip.get("caption") or rem_clip.get("description") or f"Highlight from live stream {capture_meta.get('title', '')}!\n\n#Shorts #Gaming #Viral"
                        rem_path = rem_clip.get("output_path") or rem_clip.get("video_path")
                        scheduler_engine.enqueue_clip(
                            clip_id=rem_clip.get("id", str(uuid.uuid4())[:8]),
                            video_path=rem_path,
                            title=rem_title,
                            description=rem_desc,
                            tags=tags,
                            scheduled_time=slot_dt.isoformat(),
                            privacy="public"
                        )
                        self._log(f"📅 Enqueued live stream clip #{rem_idx+1} for scheduled upload at {slot_dt.strftime('%I:%M %p')}")

                except Exception as ue:
                    logger.error(f"Failed to auto-upload livestream short: {ue}", exc_info=True)
                    self._log(f"⚠️ YouTube upload warning: {ue}")
                    upload_result = {"status": "FAILED", "error": str(ue)}
                finally:
                    scheduler_engine.resume_queue()

            self.current_state["status"] = "COMPLETED"
            self.current_state["step"] = f"Successfully generated {len(clips)} vertical shorts from live stream!"
            self.current_state["progress_percent"] = 100
            self._log(f"🎉 Generated {len(clips)} vertical 9:16 Shorts from live broadcast '{capture_meta['title']}'!")

            await state_manager.set_status(AssistantState.IDLE, f"Live stream clipping complete! Produced {len(clips)} shorts.")

            return {
                "success": True,
                "live_stream": capture_meta,
                "clips": clips,
                "upload": upload_result,
                "count": len(clips)
            }

        except Exception as e:
            logger.error(f"Livestream clipping failed: {e}", exc_info=True)
            self.current_state["status"] = "ERROR"
            self.current_state["step"] = f"Error: {e}"
            self._log(f"❌ Livestream Error: {e}")
            await state_manager.set_status(AssistantState.ERROR, f"Live stream capture error: {e}")
            return {"success": False, "error": str(e)}

        finally:
            self.is_running = False


livestream_clipper = LivestreamClipperManager()

