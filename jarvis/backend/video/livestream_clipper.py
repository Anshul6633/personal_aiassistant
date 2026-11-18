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
        self.continuous_running = False
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
        from jarvis.backend.video.ytdlp_utils import safe_extract_info, get_ytdlp_base_opts

        live_results = []
        try:
            res = safe_extract_info(search_query, download=False, extra_opts={"extract_flat": True})
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
        except Exception as ex:
            self._log(f"Live stream discovery error: {ex}")

        # Fallback if specific query didn't have active live streams: check popular streams
        if not live_results and query:
            return self.discover_live_streams(query=None, limit=limit)

        return live_results

    def discover_international_gaming_stream(self) -> Optional[Dict[str, Any]]:
        """Discover ongoing top-tier international gaming live streams (US/UK/Global) to eliminate copyright strike risks."""
        queries = [
            "GTA 6 gameplay live english",
            "GTA RP english livestream",
            "Kai Cenat gaming livestream",
            "xQc gaming live stream",
            "IShowSpeed live gaming",
            "Grand Theft Auto live stream english 1080p",
            "Jynxzi live stream gaming"
        ]
        blacklisted = [
            "carry", "carryminati", "carryislive", "total gaming", "techno gamerz",
            "mortal", "scout", "mythpat", "hindustan", "star sports", "zee", "sony",
            "colors", "aaj tak", "abp", "india", "hindi"
        ]

        for q in queries:
            try:
                results = self.discover_live_streams(query=q, limit=5)
                for cand in results:
                    uploader = cand.get("uploader", "").lower()
                    title = cand.get("title", "").lower()
                    if not any(b in uploader or b in title for b in blacklisted):
                        self._log(f"🌍 Discovered International Stream: '{cand['title']}' by {cand['uploader']} ({cand['url']})")
                        return cand
            except Exception as e:
                self._log(f"International discovery search note for '{q}': {e}")

        # Fallback broad query
        try:
            results = self.discover_live_streams(query="GTA V online gaming livestream english", limit=5)
            for cand in results:
                uploader = cand.get("uploader", "").lower()
                if not any(b in uploader for b in blacklisted):
                    return cand
        except Exception:
            pass

        return None

    def capture_live_slice(self, live_url: str, duration_seconds: int = 60) -> Dict[str, Any]:
        """Extract live HLS stream manifests and record synchronized rolling slice."""
        self._log(f"Extracting live stream manifest from: {live_url}...")
        from jarvis.backend.video.ytdlp_utils import safe_extract_info

        info = safe_extract_info(live_url, download=False)
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

        # Sort video formats to guarantee the HIGHEST resolution (1080p60) and maximum bitrate
        v_formats.sort(key=lambda f: (f.get("height") or 0, f.get("tbr") or 0, f.get("fps") or 0))
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
        style_preset: str = "gta6",
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

    def stop_continuous_pipeline(self):
        """Signal the continuous streaming pipeline to stop gracefully."""
        self.continuous_running = False
        self._log("Stopping continuous livestream pipeline...")

    async def run_continuous_pipeline(
        self,
        live_url: str,
        slice_duration: int = 180,
        num_clips: int = 2,
        target_clip_duration: float = 45.0,
        style_preset: str = "gta6",
        custom_tags: Optional[List[str]] = None,
        credits_name: str = "CarryMinati",
        channel_handle: str = "@CarryisLive",
        sleep_between_cycles: int = 35,
        crop_mode: str = "auto"
    ) -> Dict[str, Any]:
        """Continuous live stream ingest, AI hook slicing, and YouTube Shorts auto-upload loop."""
        self.continuous_running = True
        self.is_running = True
        self.current_state["status"] = "STREAMING_CONTINUOUS"
        self.current_state["step"] = f"Continuous clipping active for {live_url}"
        self.current_state["clips_uploaded"] = []

        cycle = 0
        loop = asyncio.get_event_loop()
        from jarvis.backend.video.ytdlp_utils import safe_extract_info
        from jarvis.backend.social.youtube_browser import youtube_browser
        from jarvis.backend.social.scheduler_engine import scheduler_engine
        from jarvis.backend.database.db import get_db_connection

        default_tags = ["gta6", "carrryminanti", "carryminati", "CarryisLive", "GTA 6", "Gaming", "Shorts", "Viral", "Trending"]
        tags_to_use = custom_tags or default_tags
        # Ensure 180s capture produces 2 high-impact viral clips per slice
        clips_to_generate = max(num_clips, 2) if slice_duration >= 120 else max(1, num_clips)

        self._log(f"🔥 Starting continuous live stream clipping loop on {live_url}...")
        self._log(f"Targeting {clips_to_generate} clips per {slice_duration}s slice | Tags: {tags_to_use}")

        try:
            stream_title = "CARRYMINATI PLAYS GTA VI"
            broadcaster = credits_name or "CarryMinati"
            capture_failures = 0

            while self.continuous_running:
                # 1. Probe if stream is still alive; auto-failover to international stream when concluded
                try:
                    probe_info = await loop.run_in_executor(None, safe_extract_info, live_url, False)
                    is_live = probe_info.get("is_live") or probe_info.get("live_status") == "is_live"
                    if not is_live:
                        self._log(f"🛑 Stream '{stream_title}' ({live_url}) has concluded! Auto-switching to International Gaming Stream to eliminate copyright strikes...")
                        int_stream = await loop.run_in_executor(None, self.discover_international_gaming_stream)
                        if int_stream:
                            live_url = int_stream["url"]
                            stream_title = int_stream["title"]
                            broadcaster = int_stream["uploader"]
                            credits_name = broadcaster
                            channel_handle = f"@{broadcaster.replace(' ', '')}"
                            tags_to_use = ["#gta6", "#gtavi", "#gaming", "#shorts", "#reels", "#viral", "#gameplay"]
                            self._log(f"🎯 Switched to International Gaming Stream: '{stream_title}' by {broadcaster} ({live_url})")
                            await asyncio.sleep(5)
                            continue
                        else:
                            self._log("No international streams found immediately. Waiting 45s before retrying search...")
                            await asyncio.sleep(45)
                            continue
                except Exception as pe:
                    self._log(f"Live status check note: {pe}")

                cycle += 1
                self._log(f"=== [CYCLE #{cycle}] Capturing {slice_duration}s rolling slice from stream ===")
                self.current_state["step"] = f"Cycle #{cycle}: Recording {slice_duration}s slice from live broadcast"
                await state_manager.set_status(AssistantState.EXECUTING, f"Cycle #{cycle}: Capturing live stream slice ({slice_duration}s)...")

                try:
                    capture_meta = await loop.run_in_executor(None, self.capture_live_slice, live_url, slice_duration)
                    slice_path = capture_meta["file_path"]
                    stream_title = capture_meta.get("title", stream_title)
                    broadcaster = capture_meta.get("uploader", broadcaster)
                    capture_failures = 0
                except Exception as ce:
                    capture_failures += 1
                    self._log(f"Failed to record live slice in cycle #{cycle}: {ce}.")
                    if capture_failures >= 2:
                        self._log("Multiple stream capture failures. Checking if stream has ended & failing over to International stream...")
                        int_stream = await loop.run_in_executor(None, self.discover_international_gaming_stream)
                        if int_stream:
                            live_url = int_stream["url"]
                            stream_title = int_stream["title"]
                            broadcaster = int_stream["uploader"]
                            credits_name = broadcaster
                            channel_handle = f"@{broadcaster.replace(' ', '')}"
                            capture_failures = 0
                            continue
                    self._log("Retrying slice in 15s...")
                    await asyncio.sleep(15)
                    continue

                # 2. Transcribe & extract high-hook candidate windows (2 clips per 180s slice)
                self.current_state["step"] = f"Cycle #{cycle}: Transcribing & detecting {clips_to_generate} viral hooks"
                await state_manager.set_status(AssistantState.EXECUTING, f"Cycle #{cycle}: Transcribing audio & scoring {clips_to_generate} hooks...")
                try:
                    clips = await video_pipeline.process_video(
                        video_path=slice_path,
                        num_clips=clips_to_generate,
                        target_duration=target_clip_duration,
                        style_preset=style_preset,
                        auto_publish_youtube=False,
                        crop_mode=crop_mode or "auto",
                        cycle_index=cycle - 1
                    )
                except Exception as pe:
                    self._log(f"Error in clipping pipeline for cycle #{cycle}: {pe}")
                    clips = []

                if not clips:
                    self._log(f"No valid hooks extracted in cycle #{cycle}. Proceeding to next slice...")
                    await asyncio.sleep(sleep_between_cycles)
                    continue

                # 3. Format enhanced captions, credits and upload both clips
                for clip_idx, clip in enumerate(clips, 1):
                    short_path = clip.get("output_path") or clip.get("video_path")
                    raw_title = clip.get("title") or f"CarryMinati Insane GTA 6 Moment #{clip_idx}"
                    clean_title = raw_title.replace("#Shorts", "").replace("#shorts", "").strip()
                    if clip_idx == 1:
                        final_title = f"{clean_title[:45]} 🤯 #GTA6 #Shorts"
                    else:
                        final_title = f"{clean_title[:45]} 🔥 #CarryMinati #Shorts"
                    if len(final_title) > 90:
                        final_title = final_title[:80] + "... #Shorts"

                    # Rich, engaging YouTube description with clear hook, credits & viral tags
                    short_desc = (
                        f"⚡ {clip.get('caption', '')}\n\n"
                        f"Can CarryMinati survive this insane moment in GTA 6? Watch till the end! 😱🔥\n\n"
                        f"🎮 Stream: {stream_title}\n"
                        f"👑 Credits to {credits_name}: {broadcaster} ({channel_handle})\n"
                        f"🔗 Original Stream: {live_url}\n\n"
                        f"Subscribe for more epic gaming shorts & viral moments!\n\n"
                        f"#gta6 #carrryminanti #carryminati #gaming #shorts #viral #carryislive #gtavi #trending"
                    )

                    # 4. Schedule or Publish Short on YouTube Studio with Reach Pacing
                    yt_target_dt = scheduler_engine.calculate_adaptive_schedule_time(platform="youtube", base_interval_minutes=15)
                    # Format time without leading zero (e.g. '8:30 PM' instead of '08:30 PM') as required by YouTube Studio
                    sched_time_str = yt_target_dt.strftime("%I:%M %p").lstrip("0")
                    sched_date_str = yt_target_dt.strftime("%b %d, %Y")
                    mins_away_yt = max(1, int((yt_target_dt - datetime.now()).total_seconds() / 60))

                    self._log(f"🚀 [CYCLE #{cycle} - CLIP {clip_idx}/{len(clips)}] Scheduling Short on YouTube Studio for {sched_time_str} ({sched_date_str}, +{mins_away_yt}m): '{final_title}'...")
                    self.current_state["step"] = f"Cycle #{cycle} [Clip {clip_idx}/{len(clips)}]: Scheduling Short on YouTube Studio"
                    await state_manager.set_status(AssistantState.EXECUTING, f"Scheduling clip {clip_idx}/{len(clips)} on YouTube Studio ({sched_time_str})...")

                    scheduler_engine.pause_queue()
                    try:
                        upload_res = await youtube_browser.upload_video(
                            video_path=short_path,
                            title=final_title,
                            description=short_desc,
                            tags=tags_to_use,
                            privacy="schedule",
                            schedule_time=sched_time_str,
                            schedule_date=sched_date_str
                        )
                        if not upload_res.get("success"):
                            raise RuntimeError(upload_res.get("error") or "YouTube Studio browser automation schedule failed")
                        published_url = upload_res.get("video_url") or "SCHEDULED_STUDIO"
                        self._log(f"✅ [CYCLE #{cycle} - CLIP {clip_idx}/{len(clips)}] Scheduled on YouTube Studio successfully! Time: {sched_time_str} | URL: {published_url}")
                        self.current_state["clips_uploaded"].append({
                            "cycle": cycle,
                            "clip_num": clip_idx,
                            "title": final_title,
                            "video_path": short_path,
                            "url": published_url,
                            "scheduled_time": yt_target_dt.isoformat(),
                            "timestamp": datetime.now().isoformat()
                        })

                        # Record in database
                        try:
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute(
                                "UPDATE clips SET status = 'SCHEDULED', published_youtube = ? WHERE output_path = ?",
                                (published_url, short_path)
                            )
                            conn.commit()
                            conn.close()
                        except Exception as de:
                            logger.warning(f"Could not record scheduled status in DB: {de}")

                    except Exception as ue:
                        self._log(f"⚠️ YouTube Studio upload notice: {ue}. Auto-enqueuing to local YouTube schedule queue.")
                        try:
                            scheduler_engine.enqueue_clip(
                                video_path=short_path,
                                title=final_title,
                                description=short_desc,
                                tags=tags_to_use,
                                scheduled_time=yt_target_dt.isoformat(),
                                privacy="public"
                            )
                        except Exception as qe:
                            logger.warning(f"Could not enqueue YouTube clip: {qe}")
                    finally:
                        scheduler_engine.resume_queue()

                    # 5. Schedule Reel to Instagram with Progressive Reach Pacing
                    try:
                        from jarvis.backend.social.instagram_browser import instagram_browser
                        from jarvis.backend.social.anti_ban_guard import anti_ban_guard

                        ig_status = await instagram_browser.check_login_status()
                        if ig_status.get("logged_in"):
                            ig_target_dt = scheduler_engine.calculate_adaptive_schedule_time(platform="instagram", base_interval_minutes=15)
                            mins_away_ig = max(1, int((ig_target_dt - datetime.now()).total_seconds() / 60))
                            ig_caption = anti_ban_guard.generate_varied_caption(
                                base_title=clean_title,
                                broadcaster=broadcaster,
                                credits_name=credits_name,
                                stream_url=live_url,
                                platform="instagram"
                            )

                            sched_res = scheduler_engine.schedule_instagram_reel(
                                video_path=short_path,
                                caption=ig_caption,
                                scheduled_time=ig_target_dt.isoformat(),
                                tags=tags_to_use
                            )
                            self._log(f"📅 [Instagram Reach Scheduler] Queued Reel '{clean_title[:32]}' for {ig_target_dt.strftime('%I:%M %p')} (+{mins_away_ig}m) to maximize algorithmic distribution!")
                            try:
                                conn = get_db_connection()
                                cur = conn.cursor()
                                cur.execute("UPDATE clips SET published_instagram = 1 WHERE output_path = ?", (short_path,))
                                conn.commit()
                                conn.close()
                            except Exception:
                                pass
                        else:
                            self._log("ℹ️ [Instagram] @clipperwithout session reconnecting...")
                    except Exception as ige:
                        self._log(f"⚠️ Instagram scheduling note: {ige}")

                    # Brief pause between sequential uploads from the same slice
                    if clip_idx < len(clips):
                        await asyncio.sleep(8)

                self._log(f"Sleeping {sleep_between_cycles}s before capturing next live slice...")
                await asyncio.sleep(sleep_between_cycles)

        except asyncio.CancelledError:
            self._log("Continuous pipeline cancelled.")
        except Exception as e:
            self._log(f"Continuous pipeline encountered error: {e}")
        finally:
            self.continuous_running = False
            self.is_running = False
            self.current_state["status"] = "IDLE"
            self.current_state["step"] = "Continuous stream clipping finished."
            await state_manager.set_status(AssistantState.IDLE, "Continuous livestream clipping loop completed.")
            return {"success": True, "total_cycles": cycle, "uploaded": self.current_state.get("clips_uploaded", [])}


livestream_clipper = LivestreamClipperManager()

