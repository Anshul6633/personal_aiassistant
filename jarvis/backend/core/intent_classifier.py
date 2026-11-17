"""Tri-Mode Intent Classifier & Deterministic Router for JARVIS.

Inspired by Leon AI (leon-ai/leon) Controlled vs Agent Mode execution.
Allows instant (<50ms) zero-latency execution of computer-use commands and telemetry
without requiring an LLM inference cycle, while routing complex/creative queries to Ollama.
"""

import re
import random
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from jarvis.backend.core.state import state_manager, AssistantState
from jarvis.backend.automation.tool_registry import tool_registry
from jarvis.backend.automation.screen import screen_observer


import re
import random
import urllib.parse
import webbrowser
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from jarvis.backend.core.state import state_manager, AssistantState
from jarvis.backend.automation.tool_registry import tool_registry
from jarvis.backend.automation.screen import screen_observer


class ExecutionMode(str, Enum):
    CONTROLLED = "CONTROLLED"  # Deterministic, sub-50ms native execution
    AGENT = "AGENT"            # Deep neural reasoning with Ollama LLM


class IntentClassifier:
    def __init__(self):
        pass

    def _trigger_key(self, vk_code: int):
        """Native Windows keybd_event trigger for volume and media keys."""
        try:
            import win32api
            import win32con
            win32api.keybd_event(vk_code, 0, 0, 0)
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
        except Exception:
            pass

    def _extract_clip_topic(self, text: str) -> Optional[str]:
        """Extract target topic or niche from Siri-style voice/chat directives."""
        clean = text.strip()
        # Clean trailing and leading punctuation
        clean = re.sub(r"^[!?,.\s\"']+|[!?,.\s\"']+$", "", clean)
        # Clean conversational prefixes
        clean = re.sub(r"^(?:hey jarvis|jarvis|can you|can u|could you|would you|will you|please|bro|sir|try to|lets|let's|i want to|i need to|help me|can we)\s+", "", clean, flags=re.IGNORECASE).strip()
        clean = re.sub(r"^[!?,.\s\"']+|[!?,.\s\"']+$", "", clean)

        # 0. Fixed autopilot triggers without explicit topic
        if clean.lower() in [
            "start autopilot", "run autopilot", "auto clip", "autopilot start",
            "start clipping", "clip viral video", "find viral video", "find video",
            "auto clip and upload", "auto publish shorts", "clipping and uploading"
        ]:
            return "viral podcast"

        # 1. Direct patterns like 'clip a gta 6 video', 'make a reel on messi', 'create shorts of ronaldo'
        p1 = r"^(?:clip|make|create|generate|extract|cut|produce|banao)\s+(?:a\s+|an\s+|some\s+)?(?:viral\s+)?(?:shorts?|reels?|videos?|clips?)?\s*(?:on|about|of|for|pe)?\s*(.+?)(?:\s+(?:video|reel|reels|short|shorts|clip|clips|highlights))?$"
        
        # 2. Hindi patterns like 'gta 6 ki reel banao', 'messi video clip karo'
        p2 = r"^(.+?)\s+(?:ki\s+)?(?:video|reel|short|clips?)\s+(?:banao|clip karo|kaat do|bana do)$"

        # 2b. Direct topic + clip like 'gta 6 clip karo', 'gta 6 clip'
        p2b = r"^(.+?)\s+(?:clips?|shorts?|reels?)(?:\s+(?:karo|banao|bana do))?$"
        
        # 3. Direct 'find and clip [topic]', 'find [topic] video'
        p3 = r"^(?:find|search)\s+(?:a\s+|an\s+)?(?:viral\s+)?(.+?)(?:\s+video|\s+shorts|\s+reel)?(?:\s+and\s+(?:clip|upload|autopilot).*)?$"

        # 4. 'clip [topic]' directly e.g. 'clip gta 6', 'clip mrbeast'
        p4 = r"^clip\s+(?:a\s+|an\s+)?(.+?)(?:\s+video|\s+shorts?|\s+reels?)?$"

        topic = None
        m = re.match(p1, clean, re.IGNORECASE)
        if m:
            t = m.group(1).strip()
            t = re.sub(r"^(?:a\s+|an\s+|the\s+|viral\s+|trending\s+)", "", t, flags=re.IGNORECASE)
            t = re.sub(r"^(?:on\s+|about\s+|of\s+|for\s+)", "", t, flags=re.IGNORECASE)
            t = re.sub(r"\s+(?:video|reel|short|clip|shorts|reels|clips)$", "", t, flags=re.IGNORECASE)
            t = re.sub(r"[!?,.\s\"']+$", "", t)
            if t and t.lower() not in ["a", "an", "the"]:
                topic = t

        if not topic:
            m2 = re.match(p2, clean, re.IGNORECASE)
            if m2:
                topic = m2.group(1).strip()

        if not topic:
            m2b = re.match(p2b, clean, re.IGNORECASE)
            if m2b:
                t = m2b.group(1).strip()
                t = re.sub(r"^(?:a\s+|an\s+|the\s+|viral\s+|trending\s+)", "", t, flags=re.IGNORECASE)
                if t and t.lower() not in ["a", "an", "the", "clip", "make"]:
                    topic = t

        if not topic:
            m3 = re.match(p3, clean, re.IGNORECASE)
            if m3:
                t = m3.group(1).strip()
                t = re.sub(r"^(?:a\s+|an\s+|the\s+|viral\s+|trending\s+)", "", t, flags=re.IGNORECASE)
                t = re.sub(r"^(?:on\s+|about\s+|of\s+|for\s+)", "", t, flags=re.IGNORECASE)
                t = re.sub(r"\s+(?:video|reel|short|clip|shorts|reels|clips)$", "", t, flags=re.IGNORECASE)
                t = re.sub(r"[!?,.\s\"']+$", "", t)
                if t and t.lower() not in ["a", "an", "the"]:
                    topic = t

        if not topic:
            m4 = re.match(p4, clean, re.IGNORECASE)
            if m4:
                t = m4.group(1).strip()
                t = re.sub(r"[!?,.\s\"']+$", "", t)
                if t and t.lower() not in ["a", "an", "the", "video", "shorts", "reel"]:
                    topic = t

        if topic and topic.lower() in ["video", "shorts", "reel", "reels", "clip", "clips"]:
            topic = "viral podcast"

        if topic:
            topic = re.sub(r"[!?,.\s\"']+$", "", topic).strip()

        return topic

    def classify_and_execute(self, prompt: str) -> Tuple[ExecutionMode, Optional[str], Optional[Dict[str, Any]]]:
        """Evaluate user prompt.
        
        If matches a deterministic command with high confidence, executes it immediately
        and returns (ExecutionMode.CONTROLLED, immediate_reply_text, execution_metadata).
        Otherwise returns (ExecutionMode.AGENT, None, None).
        """
        text = prompt.lower().strip()

        # 0. Capability & Refusal Defense (Zero-Refusal Guarantee)
        clean_p = re.sub(r"^[!?,.\s\"']+|[!?,.\s\"']+$", "", text).strip()
        if clean_p in ["why", "why not", "why can't you", "why cannot you", "why are you saying that", "kyun", "kyu", "why so", "why you cant"]:
            reply = "I can assist with absolutely everything, Boss! I'm your whole agent—from clipping viral GTA 6 and gaming videos to capturing live streams, controlling your desktop, managing apps, and publishing directly to YouTube Studio. Just tell me what you want to create or automate!"
            return ExecutionMode.CONTROLLED, reply, {"action": "capability_clarification"}

        # 0a. Portal Operations & Upload Status (Master Brain Telemetry)
        if any(w in text for w in [
            "what is uploading", "what's uploading", "what video is uploading", "kya upload ho raha hai",
            "upload status", "portal status", "portal update", "status report", "what are you doing",
            "queue status", "how many videos", "how many shorts", "uploading status"
        ]):
            from jarvis.backend.social.scheduler_engine import scheduler_engine
            from jarvis.backend.video.viral_autopilot import viral_autopilot
            from jarvis.backend.database.db import get_db_connection

            q_stats = scheduler_engine.get_queue_stats()
            ap = viral_autopilot.get_status()

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM clips WHERE status = 'READY'")
            ready_count = cur.fetchone()[0]
            conn.close()

            queued = q_stats.get("queued", 0)
            today_pub = q_stats.get("published_last_24h", 0)
            curr_id = q_stats.get("current_uploading_id")
            next_item = q_stats.get("next_item")

            if ap.get("status") == "RUNNING":
                step = ap.get("step", "Processing")
                pct = ap.get("progress_percent", 0)
                reply = f"Master Brain Report, Boss: Autopilot is actively running at {pct}%. Current stage: {step}. {queued} videos queued, and {today_pub} published today with anti-ban shield active."
            elif curr_id:
                reply = f"Live upload in progress, Boss: Uploading item {curr_id} directly to YouTube Studio as Public. We have {queued} videos in the queue, and {today_pub} published today."
            elif next_item:
                title = next_item.get("title", "Next Video")
                secs = q_stats.get("seconds_until_next", 0)
                mins = secs // 60
                reply = f"All systems nominal, Boss. Next scheduled upload in {mins} minutes: '{title[:45]}'. Total queued: {queued}, published today: {today_pub}, ready in library: {ready_count}. Anti-ban pacing active."
            else:
                reply = f"Standing by, Boss. Portal library has {ready_count} clips ready, {queued} queued for dispatch, and {today_pub} shorts live on your channels today."

            return ExecutionMode.CONTROLLED, reply, {"action": "portal_status", "stats": q_stats}

        # 0a2. Ongoing Live Stream Clipping & Real-Time Ingestion
        if any(w in text for w in [
            "clip livestream", "clip live stream", "clip a livestream", "clip a live stream",
            "clip ongoing stream", "clip ongoing livestream", "clip ongoing livetream",
            "clip a ongoing livetream", "clip an ongoing livestream", "clip an ongoing livetream",
            "clip live", "capture livestream", "capture live stream", "live stream clip",
            "stream clip karo", "live stream se short banao", "livestream clip"
        ]):
            import threading
            from jarvis.backend.video.livestream_clipper import livestream_clipper

            # Extract URL if provided
            url_match = re.search(r"(https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|live/)|youtu\.be/)[\w\-]+)", prompt)
            target_url = url_match.group(1) if url_match else None

            # Check if upload is requested
            should_upload = any(w in text for w in ["upload", "publish", "post", "dalo", "daal do", "on my youtube", "to my youtube", "to youtube"])

            # Extract topic if mentioned
            clean_t = re.sub(r"(?:try|to|clip|capture|make|a|an|ongoing|the|live|stream|livestream|livetream|video|short|shorts|reel|from|on|of|karo|banao|and|upload|it|my|youtube)", "", text).strip()
            if any(k in text for k in ["game", "gaming", "gameplay", "gta", "minecraft", "free fire", "bgmi", "valorant"]):
                topic = "gaming live stream"
                style_preset = "mrbeast"
            else:
                topic = clean_t if (clean_t and len(clean_t) > 2) else "live news"
                style_preset = "podcast"

            def _launch_live_clip():
                import asyncio
                policy = asyncio.WindowsProactorEventLoopPolicy()
                loop = policy.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    livestream_clipper.clip_ongoing_livestream(
                        live_url_or_topic=target_url or topic,
                        duration_seconds=45,
                        num_clips=2,
                        target_clip_duration=30.0,
                        style_preset=style_preset,
                        auto_upload_youtube=should_upload,
                        visibility="public"
                    )
                )
                loop.close()

            threading.Thread(target=_launch_live_clip, daemon=True).start()

            desc = f"from '{target_url}'" if target_url else f"for '{topic}'"
            upload_note = " and publishing the finished Short directly to your YouTube channel via Playwright" if should_upload else ""
            reply = f"Directive accepted, Boss! Tuning into the live broadcast {desc}, capturing a rolling 45-second slice with synchronized audio/video, extracting 9:16 vertical viral shorts with animated subtitles{upload_note}!"
            return ExecutionMode.CONTROLLED, reply, {"action": "livestream_clip_start", "topic": topic, "url": target_url, "auto_upload": should_upload}

        # 0b. Siri-Style Autonomous Video Clipping, Link Finding & Social Publishing Loop
        clip_topic = self._extract_clip_topic(text)
        if clip_topic:
            import threading
            from jarvis.backend.video.viral_autopilot import viral_autopilot

            # Map known nicknames to curated presets if applicable
            preset_name = clip_topic
            low_t = clip_topic.lower()
            if any(k in low_t for k in ["mrbeast", "beast"]):
                preset_name = "mrbeast"
            elif any(k in low_t for k in ["rogan", "joe rogan", "podcast"]):
                preset_name = "rogan"
            elif any(k in low_t for k in ["huberman", "health", "neuro"]):
                preset_name = "huberman"
            elif "speed" in low_t:
                preset_name = "speed"
            elif any(k in low_t for k in ["football", "soccer", "ronaldo", "messi", "mbappe"]):
                preset_name = "football"

            # Launch in background thread
            def _launch():
                import asyncio
                policy = asyncio.WindowsProactorEventLoopPolicy()
                loop = policy.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    viral_autopilot.run_autopilot(
                        preset=preset_name,
                        search_topic=clip_topic,
                        num_clips=2,
                        upload_till_limit=True,
                        platform="both",
                        privacy="public"
                    )
                )
                loop.close()

            threading.Thread(target=_launch, daemon=True).start()

            replies = [
                f"Right on it, Boss! Finding a top viral {clip_topic.upper()} video on YouTube, clipping high-energy vertical 9:16 shorts with animated subtitles, and queuing them for YouTube and Instagram!",
                f"Directive accepted, Sir! Sourcing a viral {clip_topic.upper()} video right now, extracting peak emotional hooks, and generating vertical Shorts for your channels.",
                f"Coming right up, Boss! Autopilot is active for '{clip_topic.capitalize()}'. Sourcing the link, clipping 9:16 reels with karaoke subtitles, and queuing uploads now."
            ]
            return ExecutionMode.CONTROLLED, random.choice(replies), {"action": "viral_autopilot_start", "topic": clip_topic, "preset": preset_name}

        # 1. Hardware / Battery Telemetry
        if any(w in text for w in ["battery", "battery status", "charge", "battery level", "hardware check", "system status", "specs", "how is my pc", "pc status"]):
            state_manager.update_metrics()
            m = state_manager.state.metrics
            bat = f"{m.battery_percent}% ({'Plugged in & Charging' if m.is_plugged else 'On Battery'})" if m.battery_percent is not None else "Plugged In"
            replies = [
                f"Live diagnostics for you, Boss: CPU is at {m.cpu_percent}%, RAM at {m.ram_percent}% ({m.ram_used_gb}GB of {m.ram_total_gb}GB), Battery is {bat}. All systems nominal!",
                f"Checking the core vitals, Boss: CPU {m.cpu_percent}%, RAM {m.ram_percent}%, Battery {bat}, GPU {m.gpu_name}. Ready for action!",
                f"System status report: CPU {m.cpu_percent}%, Memory {m.ram_used_gb}GB in use, Battery {bat}. Everything running smoothly."
            ]
            return ExecutionMode.CONTROLLED, random.choice(replies), {"action": "telemetry", "metrics": m.model_dump()}

        # 2. Time & Date (Siri-style instant query)
        if any(w in text for w in ["what time is it", "what's the time", "current time", "kya time hai", "time batao", "time please"]):
            now = datetime.now()
            reply = f"It is currently {now.strftime('%I:%M %p')}, Boss."
            return ExecutionMode.CONTROLLED, reply, {"action": "time", "time": now.isoformat()}

        if any(w in text for w in ["what is today's date", "what's today's date", "today's date", "today date", "what is today date", "what date is it", "aaj ki date", "what day is it", "which day is it"]):
            now = datetime.now()
            reply = f"Today is {now.strftime('%A, %B %d, %Y')}, Boss."
            return ExecutionMode.CONTROLLED, reply, {"action": "date", "date": now.isoformat()}

        # 3. Volume & Media Controls (Instant keybd_event)
        if any(w in text for w in ["volume up", "increase volume", "louder", "awaz badhao", "sound badhao"]):
            for _ in range(5):
                self._trigger_key(0xAF)  # VK_VOLUME_UP
            return ExecutionMode.CONTROLLED, "Volume turned up, Boss.", {"action": "volume_up"}

        if any(w in text for w in ["volume down", "decrease volume", "lower volume", "quieter", "awaz kam karo", "sound kam karo"]):
            for _ in range(5):
                self._trigger_key(0xAE)  # VK_VOLUME_DOWN
            return ExecutionMode.CONTROLLED, "Volume lowered, Boss.", {"action": "volume_down"}

        if any(w in text for w in ["mute audio", "mute sound", "unmute", "awaz band karo"]):
            self._trigger_key(0xAD)  # VK_VOLUME_MUTE
            return ExecutionMode.CONTROLLED, "Volume muted or unmuted, Boss.", {"action": "volume_mute"}

        if any(w in text for w in ["pause music", "pause video", "play music", "play video", "resume music", "resume video"]):
            self._trigger_key(0xB3)  # VK_MEDIA_PLAY_PAUSE
            return ExecutionMode.CONTROLLED, "Media playback toggled, Boss.", {"action": "media_play_pause"}

        # 4. YouTube URL Ingestion & Automatic Clipping
        yt_url_match = re.search(r"(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[\w\-]+)", prompt)
        if yt_url_match and any(w in text for w in ["download", "clip", "make", "short", "reel", "convert"]):
            yt_url = yt_url_match.group(1)
            import threading
            from jarvis.backend.skills.youtube_downloader.actions import download_youtube_video
            threading.Thread(
                target=download_youtube_video,
                args=(yt_url, None, True, 5, 45.0),
                daemon=True
            ).start()
            return ExecutionMode.CONTROLLED, f"Downloading YouTube video and autonomously producing 5 viral shorts, Boss!", {"action": "youtube_download", "url": yt_url}

        # 5. Long Video to Multiple Shorts Trigger
        if any(w in text for w in ["split into shorts", "slice into shorts", "cut video into reels", "long video to shorts", "convert long video"]):
            import asyncio
            from jarvis.backend.video.pipeline import video_pipeline
            from jarvis.backend.config.settings import WORKSPACE_ROOT
            sample_video = str(WORKSPACE_ROOT / "jarvis" / "tests" / "sample_podcast.mp4")
            asyncio.create_task(video_pipeline.process_video(sample_video, num_clips=5, target_duration=45.0))
            return ExecutionMode.CONTROLLED, "Cutting long video into 5 high-scoring vertical shorts with styled subtitles, Boss!", {"action": "split_long_video"}

        # 6. DaVinci Resolve MCP Page Switching & Control
        page_match = re.search(r"(?:switch|open|go to)(?: davinci)? (?:to )?(?:the )?(edit|color|deliver|fusion|fairlight|media|cut) page(?: in davinci)?", text)
        if page_match or ("davinci" in text and any(p in text for p in ["edit page", "color page", "deliver page", "fusion page", "cut page"])):
            page_name = page_match.group(1) if page_match else "edit"
            for p in ["edit", "color", "deliver", "fusion", "fairlight", "media", "cut"]:
                if f"{p} page" in text:
                    page_name = p
                    break
            from jarvis.backend.mcp.davinci.tools.app_tools import switch_page
            res = switch_page(page_name)
            if res.get("success"):
                return ExecutionMode.CONTROLLED, f"Switched DaVinci Resolve to the {page_name.capitalize()} page, Boss.", {"action": "davinci_switch_page", "page": page_name}
            else:
                return ExecutionMode.CONTROLLED, f"DaVinci Resolve is not currently open, Boss. You can launch Resolve or export an FCPXML timeline instead.", {"action": "davinci_switch_page", "res": res}

        # 6b. DaVinci Project Creation & Vertical Resolution
        if "davinci" in text and any(w in text for w in ["create project", "new project", "shorts project", "vertical project"]):
            from jarvis.backend.mcp.davinci.tools.project_tools import create_project
            proj_name = "JARVIS_Vertical_Shorts"
            name_match = re.search(r"(?:called|named) ([a-zA-Z0-9_\- ]+)", prompt)
            if name_match:
                proj_name = name_match.group(1).strip()
            res = create_project(proj_name, vertical_shorts=True)
            if res.get("success"):
                return ExecutionMode.CONTROLLED, f"Created new DaVinci project '{proj_name}' configured for 1080x1920 vertical Shorts, Boss!", {"action": "davinci_create_project", "res": res}
            else:
                return ExecutionMode.CONTROLLED, f"DaVinci Resolve is offline, Boss. I can generate an XML timeline for you whenever you are ready.", {"action": "davinci_create_project", "res": res}

        # 6c. DaVinci Render Start
        if "davinci" in text and ("render" in text or any(w in text for w in ["start render", "export queue", "render queue"])):
            from jarvis.backend.mcp.davinci.tools.render_tools import start_render, add_render_job
            add_render_job()
            res = start_render()
            if res.get("success"):
                return ExecutionMode.CONTROLLED, "Started DaVinci Resolve render queue, Boss!", {"action": "davinci_start_render"}
            else:
                return ExecutionMode.CONTROLLED, "Could not start render queue. Ensure DaVinci Resolve is running with an active timeline, Boss.", {"action": "davinci_start_render", "res": res}

        # 6d. DaVinci Resolve Timeline Export (FCPXML / Studio Bridge)
        if any(w in text for w in ["export to davinci", "davinci resolve", "send to davinci", "davinci timeline", "fcpxml export", "davinci export"]):
            from jarvis.backend.skills.davinci_resolve.actions import send_to_resolve, open_timelines_folder
            from jarvis.backend.database.db import get_db_connection
            from jarvis.backend.config.settings import WORKSPACE_ROOT
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clips ORDER BY created_at DESC LIMIT 10")
            clips = [dict(r) for r in cursor.fetchall()]
            conn.close()
            v_path = clips[0].get("source_file") if clips else str(WORKSPACE_ROOT / "jarvis" / "tests" / "sample_podcast.mp4")
            res = send_to_resolve(v_path, clips, "JARVIS_Vertical_Shorts")
            open_timelines_folder()
            return ExecutionMode.CONTROLLED, "Exported 9:16 vertical DaVinci Resolve timeline with all cuts and markers, Boss! The folder is open on your screen.", {"action": "davinci_export", "res": res}

        # 7. Web Search & YouTube Slot Extraction
        # Universal Play Command (Siri-style "Play X")
        play_match = re.search(r"^(?:play|chalao|bajaao|sunao) (.+)$", text)
        if play_match:
            raw_q = play_match.group(1)
            query = re.sub(r"\b(on youtube|youtube pe|pe)\b", "", raw_q, flags=re.IGNORECASE).strip()
            if query:
                url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                webbrowser.open(url)
                replies = [
                    f"Right on it, Boss! Playing '{query}' on YouTube for you.",
                    f"Coming right up, Boss. Tuning into '{query}' on YouTube!",
                    f"Playing '{query}' right now. Enjoy, Boss!"
                ]
                return ExecutionMode.CONTROLLED, random.choice(replies), {"action": "youtube_play", "query": query}

        # Google Search
        google_match = re.search(r"(?:search (?:for )?|google |batao )(.+?)(?: on google)?$", text)
        if google_match and ("google" in text or "search" in text or "batao" in text) and not any(w in text for w in ["youtube", "video", "reel"]):
            query = google_match.group(1).replace("on google", "").strip()
            if query and len(query) > 1:
                url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                webbrowser.open(url)
                return ExecutionMode.CONTROLLED, f"Searching Google for '{query}', Boss.", {"action": "google_search", "query": query}

        # YouTube Search / Topic
        youtube_match = re.search(r"(?:search |play |find )(.+?)(?: on youtube)$", text)
        if youtube_match:
            query = youtube_match.group(1).strip()
            if query:
                url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                webbrowser.open(url)
                return ExecutionMode.CONTROLLED, f"Opening YouTube search for '{query}', Boss.", {"action": "youtube_search", "query": query}

        # 7b. Weather & Environment (Siri-style)
        if any(w in text for w in ["weather", "temperature", "mausam", "barish", "rain today", "how's the weather"]):
            webbrowser.open("https://www.google.com/search?q=current+weather")
            return ExecutionMode.CONTROLLED, "Checking the local weather forecast for you right now, Boss.", {"action": "weather"}

        # 7c. Direct Upload / Social Dispatch Action (Siri-Style Instant Execution)
        if any(w in text for w in [
            "upload next short", "dispatch next short", "publish next short", "post to youtube",
            "next video upload karo", "upload this short", "upload video", "upload short",
            "publish short", "publish video", "upload to youtube", "dispatch video",
            "upload karo", "video upload karo", "short upload karo"
        ]):
            import threading
            from jarvis.backend.social.scheduler_engine import scheduler_engine

            def _dispatch():
                import asyncio
                policy = asyncio.WindowsProactorEventLoopPolicy()
                loop = policy.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(scheduler_engine.dispatch_next_now())
                loop.close()

            threading.Thread(target=_dispatch, daemon=True).start()
            return ExecutionMode.CONTROLLED, "Directive engaged, Boss! Dispatching the next queued short directly to YouTube Studio as Public.", {"action": "dispatch_next_short"}

        # 8. Universal Website Launchers & Known Portals
        known_sites = {
            "youtube": "https://www.youtube.com",
            "instagram": "https://www.instagram.com",
            "insta": "https://www.instagram.com",
            "twitter": "https://x.com",
            "x": "https://x.com",
            "netflix": "https://www.netflix.com",
            "spotify": "https://open.spotify.com",
            "github": "https://www.github.com",
            "reddit": "https://www.reddit.com",
            "canva": "https://www.canva.com",
            "chatgpt": "https://chat.openai.com",
            "gmail": "https://mail.google.com",
            "mail": "https://mail.google.com",
            "maps": "https://maps.google.com",
            "amazon": "https://www.amazon.in",
            "flipkart": "https://www.flipkart.com",
            "linkedin": "https://www.linkedin.com",
            "whatsapp": "https://web.whatsapp.com"
        }

        # Direct domain launch (e.g. "open canva.com" or "open google.com")
        domain_match = re.search(r"(?:open|launch|kholo|chalao) ([a-zA-Z0-9_\-]+\.(?:com|org|in|net|io|co|ai))", text)
        if domain_match:
            dom = domain_match.group(1).strip()
            webbrowser.open(f"https://{dom}")
            return ExecutionMode.CONTROLLED, f"Opening {dom} for you, Boss.", {"action": "open_domain", "url": f"https://{dom}"}

        for site_key, site_url in known_sites.items():
            if f"open {site_key}" in text or f"{site_key} kholo" in text or f"launch {site_key}" in text:
                webbrowser.open(site_url)
                return ExecutionMode.CONTROLLED, f"Opening {site_key.capitalize()} for you, Boss.", {"action": "open_url", "url": site_url}

        # 9. Lock Workstation
        if any(w in text for w in [
            "lock pc", "lock my pc", "lock the pc", "lock computer", "lock my computer",
            "lock laptop", "lock my laptop", "lock workstation", "lock screen", "pc lock karo"
        ]):
            tool_registry.execute_tool("lock_pc", {})
            replies = [
                "Workstation secured and locked, Boss. Standing by.",
                "Locking your computer right now, Sir.",
                "PC locked securely. I will keep watch, Boss."
            ]
            return ExecutionMode.CONTROLLED, random.choice(replies), {"action": "lock_pc"}

        # 10. Fullscreen Screenshot
        if any(w in text for w in ["screenshot", "screen capture", "take a screenshot", "capture screen", "screenshot lo"]):
            path = screen_observer.capture_fullscreen(save_file=True)
            replies = [
                "Screenshot captured and stored in output screenshots, Boss.",
                "Display captured successfully, Sir.",
                "Snap taken! Fullscreen screenshot saved."
            ]
            return ExecutionMode.CONTROLLED, random.choice(replies), {"action": "screenshot", "path": path}

        # 11. Minimize All / Show Desktop
        if any(w in text for w in ["minimize all", "show desktop", "minimize windows", "desktop dikhao"]):
            tool_registry.execute_tool("minimize_all", {})
            replies = [
                "All windows minimized. Here is your clean desktop, Boss.",
                "Desktop cleared and all windows minimized, Sir."
            ]
            return ExecutionMode.CONTROLLED, random.choice(replies), {"action": "minimize_all"}

        # 12. Universal Dynamic App Launcher
        app_match = re.search(r"^(?:open|launch|start|kholo|chalao) (.+)$", text)
        if app_match:
            app_req = app_match.group(1).strip().lower()
            # Clean common filler words
            app_req = re.sub(r"\b(app|application|software|program|karo|please)\b", "", app_req).strip()
            if app_req and len(app_req) > 1:
                res = tool_registry.execute_tool("launch_application", {"app_name": app_req})
                if res.get("success"):
                    return ExecutionMode.CONTROLLED, f"Launching {app_req.capitalize()} for you right now, Boss!", {"action": "launch_app", "app": app_req}

        # 13. Stop Speech / Mute
        if any(w in text for w in ["stop speaking", "be quiet", "shut up", "mute", "chup", "shant raho"]):
            from jarvis.backend.voice.tts import tts_engine
            tts_engine.stop_speaking()
            return ExecutionMode.CONTROLLED, "Silenced. Standing by silently, Boss.", {"action": "stop_speaking"}

        # 13b. Direct Inquiry on Capabilities, Refusal Inquiries, & Siri 'Why' Inquiries
        clean_prompt = re.sub(r"[?!.,]", "", text).strip()
        if clean_prompt in [
            "why", "why not", "why so", "kyun", "kyu", "kya hua",
            "why cant you", "why can't you", "why cannot you",
            "why did you say that", "why did you refuse", "why cant you assist",
            "why can't you assist", "why are you saying that", "can you assist",
            "are you able to assist", "kya tum kar sakte ho", "why bro"
        ] or any(phrase in text for phrase in [
            "why can't you assist", "why cant you assist", "why did you refuse",
            "why can't you do that", "why cant you do that"
        ]):
            reassurance_replies = [
                "I can assist with absolutely everything, Boss! I'm your whole agent—from clipping viral videos and livestreams to controlling your desktop, managing apps, and publishing to YouTube Studio. Just tell me what you need!",
                "There are zero limits, Boss! I am right here with full control over your machine and content pipeline. Just give me the command and I will execute it instantly!",
                "Bilkul Boss! I can do anything you ask—whether you want me to clip a video, play music, open any app, or check our upload queue, consider it done!"
            ]
            return ExecutionMode.CONTROLLED, random.choice(reassurance_replies), {"action": "capability_reassurance"}

        # 14. Friendly Siri-Style Banter & Identity
        if any(clean_prompt == w or text.startswith(w) for w in [
            "hello", "hi jarvis", "hello jarvis", "hey jarvis", "hey buddy", "kya haal hai", "kaise ho",
            "how are you", "who are you", "what can you do", "introduce yourself"
        ]):
            banter_replies = [
                "Hey Boss! Always at your service. Tell me what we're building, clipping, or automating today!",
                "Hello Boss! Everything is supercharged and standing by. What's on your agenda?",
                "Namaste Boss! All systems nominal and ready. Need me to launch an app, make a reel, or run an upload?",
                "I'm JARVIS — your personal Siri and Iron Man inspired whole agent! I control your desktop, create viral shorts from long videos, dispatch social uploads, and manage your machine. What can I do for you, Boss?"
            ]
            return ExecutionMode.CONTROLLED, random.choice(banter_replies), {"action": "friendly_banter"}

        # All other creative, conversational, or multi-step requests route to Agent Mode (Ollama)
        return ExecutionMode.AGENT, None, None


intent_classifier = IntentClassifier()

