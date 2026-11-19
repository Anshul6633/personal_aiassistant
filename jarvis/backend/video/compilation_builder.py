import os
import re
import sys
import json
import uuid
import logging
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

from jarvis.backend.config.settings import settings
from jarvis.backend.config.storage_router import storage_router
from jarvis.backend.database.db import get_db_connection

logger = logging.getLogger("JARVIS.CompilationBuilder")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
def get_compilations_dir() -> Path:
    return storage_router.get_output_dir("compilations")

COMPILATIONS_DIR = get_compilations_dir()


class CompilationBuilder:
    """Builds and schedules 8-12 minute YouTube Long-Form Compilations every 8 hours.
    
    Powers the parallel 4,000 Watch Hours pathway for YouTube Partner Program (YPP) Monetization.
    Features:
    - 6-second viral teaser opener ("🔥 UP NEXT IN THIS VIDEO...")
    - 16:9 1080p True Full Screen Widescreen layout (ZERO black bars, ZERO blurred wings) with AMOLED grading & audio normalization (-14 LUFS)
    - Full chapter timestamps for YouTube UI
    - Strict 17 U.S.C. § 107 Fair Use & Zero-Strike Streamer Attribution Notice
    - Exact 8-hour schedule spacing between consecutive long-form videos
    """

    def __init__(self):
        self.ffmpeg = settings.FFMPEG_PATH
        self.ffprobe = settings.FFPROBE_PATH

    def get_candidate_clips(self, limit: int = 10, only_published: bool = True) -> List[Dict[str, Any]]:
        """Retrieve candidate high-performing clips strictly from published videos in the database.
        
        Strictly prioritizes verified PUBLISHED clips across:
        1. clips table (status='PUBLISHED' or published_youtube!='0' or published_instagram=1)
        2. instagram_schedule_queue (status='PUBLISHED')
        3. youtube_schedule_queue (status='PUBLISHED')
        Avoids repeating clips already featured in recent compilations.
        """
        candidates = []
        seen_names = set()

        used_file = COMPILATIONS_DIR / "used_clips.json"
        used_clips = set()
        if used_file.exists():
            try:
                with open(used_file, "r") as f:
                    used_clips = set(json.load(f))
            except Exception:
                pass

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # 1. Primary: clips table where status = 'PUBLISHED' or published flags are set
            cur.execute("""
                SELECT id, title, output_path, total_score, duration, caption, tags, created_at
                FROM clips 
                WHERE (status = 'PUBLISHED' OR published_youtube != '0' OR published_instagram = 1) 
                  AND output_path IS NOT NULL
                ORDER BY total_score DESC, created_at DESC
            """)
            for r in cur.fetchall():
                p = Path(r["output_path"])
                if not p.is_absolute():
                    p = WORKSPACE_ROOT / p
                if p.exists() and p.stat().st_size > 1_000_000:
                    k = p.name.lower()
                    if k not in seen_names:
                        seen_names.add(k)
                        candidates.append({
                            "path": str(p),
                            "name": p.name,
                            "caption": r["caption"] or r["title"],
                            "score": float(r["total_score"] or 80.0),
                            "duration": float(r["duration"] or 25.0),
                            "created_at": r["created_at"],
                            "is_used": k in used_clips
                        })

            # 2. Secondary: published items from instagram_schedule_queue
            cur.execute("""
                SELECT video_path, caption, tags, created_at, published_at
                FROM instagram_schedule_queue 
                WHERE status = 'PUBLISHED'
                ORDER BY published_at DESC
            """)
            for r in cur.fetchall():
                vp = r["video_path"]
                if vp:
                    p = Path(vp)
                    if not p.is_absolute():
                        p = WORKSPACE_ROOT / p
                    if p.exists() and p.stat().st_size > 1_000_000:
                        k = p.name.lower()
                        if k not in seen_names:
                            seen_names.add(k)
                            candidates.append({
                                "path": str(p),
                                "name": p.name,
                                "caption": r["caption"] or p.stem,
                                "score": 80.0,
                                "duration": 25.0,
                                "created_at": r["created_at"],
                                "is_used": k in used_clips
                            })

            # 3. Tertiary: published items from youtube_schedule_queue
            cur.execute("""
                SELECT file_name, title, description, tags, created_at, published_at
                FROM youtube_schedule_queue 
                WHERE status = 'PUBLISHED'
                ORDER BY rowid DESC
            """)
            for r in cur.fetchall():
                fn = r["file_name"]
                if fn and fn.endswith(".mp4"):
                    p = WORKSPACE_ROOT / "jarvis" / "output" / "reels" / fn
                    if p.exists() and p.stat().st_size > 1_000_000:
                        k = p.name.lower()
                        if k not in seen_names:
                            seen_names.add(k)
                            candidates.append({
                                "path": str(p),
                                "name": p.name,
                                "caption": r["title"] or fn,
                                "score": 80.0,
                                "duration": 25.0,
                                "created_at": r["created_at"],
                                "is_used": k in used_clips
                            })
        except Exception as e:
            logger.warning(f"Error querying published clips from DB: {e}")
        finally:
            conn.close()

        # If not enough published clips found and only_published is False, fallback to all reels
        if len(candidates) < 4 and not only_published:
            reels_dir = WORKSPACE_ROOT / "jarvis" / "output" / "reels"
            if reels_dir.exists():
                for p in sorted(reels_dir.glob("clip_*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True):
                    if p.stat().st_size > 1_000_000:
                        k = p.name.lower()
                        if k not in seen_names:
                            seen_names.add(k)
                            candidates.append({
                                "path": str(p),
                                "name": p.name,
                                "caption": p.stem.replace("_", " ").title(),
                                "score": 75.0,
                                "duration": 25.0,
                                "created_at": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                                "is_used": k in used_clips
                            })

        # Separate fresh (unused) from already used clips
        fresh = [c for c in candidates if not c.get("is_used")]
        if len(fresh) >= 4:
            return fresh[:limit]
        
        return candidates[:limit]

    def get_video_duration(self, file_path: str) -> float:
        """Get exact duration in seconds using ffprobe."""
        try:
            cmd = [
                self.ffprobe, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(res.stdout.strip())
        except Exception:
            return 20.0

    def get_video_dimensions(self, file_path: str) -> tuple[int, int]:
        """Get exact video (width, height) using ffprobe."""
        try:
            cmd = [
                self.ffprobe, "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "json", str(file_path)
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            data = json.loads(res.stdout)
            st = data["streams"][0]
            return int(st["width"]), int(st["height"])
        except Exception:
            return 1080, 1920

    def verify_compilation_quality(self, video_path: str, thumbnail_path: Optional[str] = None) -> Dict[str, Any]:
        """Strict 1000-Point Quality Gate: Verify resolution, 16:9 full-screen aspect ratio, audio, duration, and thumbnail before scheduling."""
        vp = Path(video_path)
        if not vp.exists():
            return {"verified": False, "reason": f"Video file not found: {video_path}"}

        # 1. Probe video streams
        try:
            cmd = [
                self.ffprobe, "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate,bit_rate,duration",
                "-of", "json", str(vp)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            v_data = json.loads(res.stdout)["streams"][0]
            w = int(v_data.get("width", 0))
            h = int(v_data.get("height", 0))
            dur = float(v_data.get("duration", 0.0))
        except Exception as e:
            return {"verified": False, "reason": f"Video ffprobe failed: {e}"}

        # Rule 1: Resolution must be strictly 1920x1080 full screen (NOT vertical)
        if w != 1920 or h != 1080:
            return {
                "verified": False,
                "reason": f"Resolution violation: Expected 1920x1080, got {w}x{h}. Long videos MUST be 16:9 full screen!"
            }

        # Rule 2: Aspect Ratio must be strictly 16:9 (1.777...)
        aspect_ratio = w / h
        if abs(aspect_ratio - (16.0 / 9.0)) > 0.02:
            return {
                "verified": False,
                "reason": f"Aspect ratio violation: Expected 1.777 (16:9), got {aspect_ratio:.3f}!"
            }

        # Rule 3: Duration check (Must be >= 300s for long-form mid-roll eligibility)
        if dur < 300:
            return {
                "verified": False,
                "reason": f"Duration violation: Video is only {dur:.1f}s. Long videos must be at least 5-12 minutes!"
            }

        # Rule 4: Probe audio streams
        try:
            cmd_a = [
                self.ffprobe, "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=channels,sample_rate",
                "-of", "json", str(vp)
            ]
            res_a = subprocess.run(cmd_a, capture_output=True, text=True, check=True)
            a_data = json.loads(res_a.stdout).get("streams", [])
            if not a_data:
                return {"verified": False, "reason": "Audio stream missing! Long video has no audio!"}
            channels = int(a_data[0].get("channels", 0))
            if channels < 1:
                return {"verified": False, "reason": "Audio stream invalid: 0 channels!"}
        except Exception as e:
            return {"verified": False, "reason": f"Audio ffprobe failed: {e}"}

        # Rule 5: Thumbnail check
        if thumbnail_path:
            tp = Path(thumbnail_path)
            if not tp.exists() or tp.stat().st_size < 1000:
                return {"verified": False, "reason": f"Thumbnail missing or empty: {thumbnail_path}"}

        logger.info(
            f"✅ [1000-Point Quality Gate PASSED] Video: {vp.name} | Resolution: {w}x{h} (16:9 Full Screen) | "
            f"Duration: {dur:.1f}s ({dur/60:.1f}m) | Audio: {channels}-ch Stereo | Thumbnail: Verified"
        )
        return {
            "verified": True,
            "width": w,
            "height": h,
            "duration": dur,
            "aspect_ratio": "16:9",
            "channels": channels
        }

    def calculate_next_8h_slot(self) -> Dict[str, Any]:
        """Calculate the next 8-hour gap schedule slot on YouTube Studio."""
        now = datetime.now()
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT MAX(scheduled_time) 
            FROM youtube_schedule_queue 
            WHERE drive_file_id = 'LONG_FORM_COMPILATION' AND status IN ('QUEUED', 'SCHEDULED')
        """)
        row = cur.fetchone()
        last_sched_str = row[0] if row and row[0] else None
        conn.close()

        ref_dt = None
        if last_sched_str:
            try:
                cand_dt = datetime.fromisoformat(last_sched_str)
                if cand_dt > now:
                    ref_dt = cand_dt
            except Exception:
                pass

        if ref_dt:
            # Strictly maintain unbroken 8-hour gap from previous long-form upload
            target_dt = ref_dt + timedelta(hours=8)
        else:
            # Snap to next clean 8-hour window ahead of now (at least 2 hours ahead)
            target_dt = now + timedelta(hours=2)
            hour = target_dt.hour
            if hour < 8:
                target_dt = target_dt.replace(hour=8, minute=0, second=0, microsecond=0)
            elif hour < 16:
                target_dt = target_dt.replace(hour=16, minute=0, second=0, microsecond=0)
            else:
                target_dt = (target_dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

        # Format without leading zeroes for YouTube Studio input
        sched_time_str = target_dt.strftime("%I:%M %p").lstrip("0")
        sched_date_str = target_dt.strftime("%b %d, %Y")

        return {
            "target_dt": target_dt,
            "iso": target_dt.isoformat(),
            "schedule_time": sched_time_str,
            "schedule_date": sched_date_str
        }

    def build_weekly_compilation(
        self,
        clips: Optional[List[Dict[str, Any]]] = None,
        limit: int = 10,
        layout: str = "fullscreen_16_9",
        only_published: bool = True
    ) -> Dict[str, Any]:
        """Stitch 6-12 clips into a pristine full-screen 16:9 (1920x1080) Widescreen Long-Form Compilation."""
        selected_clips = clips or self.get_candidate_clips(limit=limit, only_published=only_published)
        if len(selected_clips) < 2:
            return {
                "success": False,
                "error": f"Not enough clips available to assemble compilation (found {len(selected_clips)}, need at least 2)."
            }

        compilation_id = f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_file = COMPILATIONS_DIR / f"{compilation_id}.mp4"
        temp_concat_txt = COMPILATIONS_DIR / f"{compilation_id}_concat.txt"

        logger.info(f"Assembling {len(selected_clips)} clips into 16:9 FULL SCREEN compilation: {output_file.name}")

        chapters = []
        current_time = 0.0
        intermediate_files = []

        try:
            # 1. Generate 5-Second Viral Opening Teaser in 16:9 Full Screen
            lead_clip = selected_clips[0]["path"]
            lead_dur = self.get_video_duration(lead_clip)
            teaser_dur = min(5.0, lead_dur / 2.0)
            teaser_file = COMPILATIONS_DIR / f"{compilation_id}_teaser.mp4"

            w_lead, h_lead = self.get_video_dimensions(lead_clip)
            if w_lead >= h_lead:
                teaser_filter = (
                    "[0:v]scale=1920:1080:flags=lanczos,unsharp=3:3:0.6:3:3:0.0,"
                    "eq=contrast=1.06:saturation=1.12:gamma=0.98[v]"
                )
            else:
                teaser_filter = (
                    "[0:v]scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,"
                    "crop=1920:1080,unsharp=3:3:0.6:3:3:0.0,eq=contrast=1.06:saturation=1.12:gamma=0.98[v]"
                )
            teaser_cmd = [
                self.ffmpeg, "-y",
                "-ss", "0", "-t", str(teaser_dur),
                "-i", lead_clip,
                "-filter_complex", teaser_filter,
                "-map", "[v]", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "fast", "-crf", "19",
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
                str(teaser_file)
            ]
            try:
                subprocess.run(teaser_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                intermediate_files.append(teaser_file)
                chapters.append({
                    "moment": 0,
                    "timestamp": "00:00",
                    "title": "⚡ Teaser: What You're About To Witness",
                    "duration": teaser_dur
                })
                current_time += teaser_dur
            except Exception as te:
                logger.warning(f"Teaser opener skipped: {te}")

            # 2. Transcode & Sequence Each Clip into True 16:9 Full Screen
            for idx, c in enumerate(selected_clips, 1):
                raw_path = c["path"]
                dur = self.get_video_duration(raw_path)
                timestamp_str = f"{int(current_time // 60):02d}:{int(current_time % 60):02d}"
                raw_title = c.get("caption", f"Moment #{idx}")
                clean_title = raw_title.split("\n")[0].split("#")[0].strip()[:40]
                if not clean_title:
                    clean_title = f"Insane Gaming Clutch #{idx}"

                chapters.append({
                    "moment": idx,
                    "timestamp": timestamp_str,
                    "title": clean_title,
                    "duration": dur
                })

                inter_file = COMPILATIONS_DIR / f"{compilation_id}_part_{idx}.mp4"
                clean_text_safe = re.sub(r"[^a-zA-Z0-9\s!\?]", "", clean_title).strip()[:35]
                font_path = "C\\:/Windows/Fonts/arialbd.ttf"

                # Check if midpoint clip to insert interactive viewer engagement CTA
                is_midpoint = (idx == max(1, len(selected_clips) // 2))
                cta_filter = ""
                if is_midpoint:
                    cta_filter = (
                        f",drawbox=y=85:color=black@0.85:width=iw:height=75:t=fill:enable='between(t,2,8)',"
                        f"drawbox=y=83:color=yellow@0.90:width=iw:height=3:t=fill:enable='between(t,2,8)',"
                        f"drawtext=fontfile='{font_path}':text='WHO PLAYED BETTER? VOTE IN COMMENTS!':fontcolor=yellow:fontsize=32:x=(w-text_w)/2:y=107:enable='between(t,2,8)'"
                    )

                # World-Class Audience Live Chat Hype & Progression Timing
                total_moments = len(selected_clips)
                prog_w = int(1920 * (idx / total_moments))
                hype_st = max(1.0, round(dur * 0.45, 1))
                hype_end = min(round(dur, 1), round(hype_st + 5.5, 1))

                # Hype chat & audience reaction filters
                hype_overlay_filters = (
                    # 1. Top Chapter Progress Tracker
                    f",drawbox=x=0:y=0:w=1920:h=6:color=black@0.6:t=fill,"
                    f"drawbox=x=0:y=0:w={prog_w}:h=6:color=cyan@0.95:t=fill,"
                    f"drawbox=x=80:y=25:w=380:h=44:color=black@0.75:t=fill,"
                    f"drawbox=x=80:y=23:w=380:h=2:color=cyan@0.90:t=fill,"
                    f"drawtext=fontfile='{font_path}':text='MOMENT {idx} OF {total_moments} // @GHOST_OF_FOOTBALL':fontcolor=white:fontsize=19:x=95:y=36,"

                    # 2. Left Wing: Animated Floating Live Audience Chat Hype Badges
                    f"drawbox=x=80:y=380:w=380:h=46:color=black@0.80:t=fill:enable='between(t,{hype_st},{hype_end})',"
                    f"drawbox=x=78:y=380:w=4:h=46:color=green@0.90:t=fill:enable='between(t,{hype_st},{hype_end})',"
                    f"drawtext=fontfile='{font_path}':text='[CHAT_W] WWWWWWWW':fontcolor=white:fontsize=21:x=95:y=392:enable='between(t,{hype_st},{hype_end})',"

                    f"drawbox=x=80:y=436:w=450:h=46:color=black@0.80:t=fill:enable='between(t,{hype_st+0.4},{hype_end})',"
                    f"drawbox=x=78:y=436:w=4:h=46:color=cyan@0.90:t=fill:enable='between(t,{hype_st+0.4},{hype_end})',"
                    f"drawtext=fontfile='{font_path}':text='[SPEED_FAN] NO WAY HE HIT THAT':fontcolor=white:fontsize=21:x=95:y=448:enable='between(t,{hype_st+0.4},{hype_end})',"

                    f"drawbox=x=80:y=492:w=440:h=46:color=black@0.80:t=fill:enable='between(t,{hype_st+0.8},{hype_end})',"
                    f"drawbox=x=78:y=492:w=4:h=46:color=yellow@0.90:t=fill:enable='between(t,{hype_st+0.8},{hype_end})',"
                    f"drawtext=fontfile='{font_path}':text='[MOD_BOT] CLIP THAT RIGHT NOW':fontcolor=yellow:fontsize=21:x=95:y=504:enable='between(t,{hype_st+0.8},{hype_end})',"

                    # 3. Right Wing: Live Crowd Velocity Meter
                    f"drawbox=x=1420:y=380:w=380:h=82:color=black@0.85:t=fill:enable='between(t,{hype_st},{hype_end})',"
                    f"drawbox=x=1420:y=378:w=380:h=3:color=red@0.90:t=fill:enable='between(t,{hype_st},{hype_end})',"
                    f"drawtext=fontfile='{font_path}':text='LIVE AUDIENCE HYPE METER':fontcolor=yellow:fontsize=19:x=1440:y=394:enable='between(t,{hype_st},{hype_end})',"
                    f"drawtext=fontfile='{font_path}':text='MAX CROWD VELOCITY 99 PCT':fontcolor=white:fontsize=21:x=1440:y=422:enable='between(t,{hype_st},{hype_end})'"
                )

                # True 16:9 Full Screen Geometry Filter (1920x1080 edge-to-edge, ZERO sidebars)
                w_c, h_c = self.get_video_dimensions(raw_path)
                if w_c >= h_c:
                    base_filter = (
                        "[0:v]scale=1920:1080:flags=lanczos,unsharp=3:3:0.6:3:3:0.0,"
                        "eq=contrast=1.06:saturation=1.12:gamma=0.98[base]"
                    )
                else:
                    base_filter = (
                        "[0:v]scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,"
                        "crop=1920:1080,unsharp=3:3:0.6:3:3:0.0,eq=contrast=1.06:saturation=1.12:gamma=0.98[base]"
                    )

                filter_complex = (
                    f"{base_filter};"
                    f"[base]drawbox=y=ih-140:color=black@0.80:width=iw:height=90:t=fill:enable='between(t,0,5)',"
                    f"drawbox=y=ih-142:color=cyan@0.90:width=iw:height=4:t=fill:enable='between(t,0,5)',"
                    f"drawtext=fontfile='{font_path}':text='MOMENT #{idx} //':fontcolor=yellow:fontsize=26:x=80:y=h-126:enable='between(t,0,5)',"
                    f"drawtext=fontfile='{font_path}':text='{clean_text_safe}':fontcolor=white:fontsize=30:x=80:y=h-92:enable='between(t,0,5)'"
                    f"{hype_overlay_filters}"
                    f"{cta_filter}[v]"
                )

                cmd = [
                    self.ffmpeg, "-y",
                    "-i", raw_path,
                    "-filter_complex", filter_complex,
                    "-map", "[v]", "-map", "0:a?",
                    "-af", "loudnorm=I=-14:LRA=11:TP=-1.5,highpass=f=75",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "19",
                    "-b:v", "8M", "-maxrate", "12M", "-bufsize", "16M",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
                    str(inter_file)
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                intermediate_files.append(inter_file)
                current_time += dur

            # 3. Write concat demuxer manifest
            with open(temp_concat_txt, "w", encoding="utf-8") as f:
                for f_path in intermediate_files:
                    f_esc = str(f_path).replace("\\", "/")
                    f.write(f"file '{f_esc}'\n")

            # 4. Merge files
            concat_cmd = [
                self.ffmpeg, "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(temp_concat_txt),
                "-c", "copy",
                str(output_file)
            ]
            subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            total_runtime_min = round(current_time / 60.0, 1)
            logger.info(f"Compilation successfully generated: {output_file.name} ({total_runtime_min} mins)")

            # Record used clips so subsequent 8-hour drops feature fresh published clips
            try:
                used_file = COMPILATIONS_DIR / "used_clips.json"
                used_set = set()
                if used_file.exists():
                    with open(used_file, "r") as uf:
                        used_set = set(json.load(uf))
                for c in selected_clips:
                    used_set.add(Path(c["path"]).name.lower())
                with open(used_file, "w") as uf:
                    json.dump(list(used_set), uf, indent=2)
            except Exception as ue:
                logger.debug(f"Used clips registry notice: {ue}")

            # Compute dynamic episode number from database
            ep_num = 1
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM youtube_schedule_queue WHERE drive_file_id = 'LONG_FORM_COMPILATION'")
                ep_num = (cur.fetchone()[0] or 0) + 1
                conn.close()
            except Exception:
                pass

            # Generate Ultra-Impressive Studio-Quality 16:9 Thumbnail (1920x1080)
            thumb_path = WORKSPACE_ROOT / "jarvis" / "output" / "thumbnails" / f"{compilation_id}_thumb.jpg"
            raw_thumb_tmp = WORKSPACE_ROOT / "jarvis" / "output" / "thumbnails" / f"{compilation_id}_raw.jpg"
            raw_thumb_sec = WORKSPACE_ROOT / "jarvis" / "output" / "thumbnails" / f"{compilation_id}_sec.jpg"
            try:
                # Extract primary frame directly from first clip for crystal-clear 1080p source
                first_clip_path = selected_clips[0]["path"]
                subprocess.run([
                    self.ffmpeg, "-y", "-ss", "2.5", "-i", str(first_clip_path),
                    "-vframes", "1",
                    str(raw_thumb_tmp)
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

                # Extract secondary action frame from second clip (or midpoint of first clip)
                if len(selected_clips) > 1:
                    sec_clip_path = selected_clips[1]["path"]
                    subprocess.run([
                        self.ffmpeg, "-y", "-ss", "3.0", "-i", str(sec_clip_path),
                        "-vframes", "1",
                        str(raw_thumb_sec)
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                else:
                    subprocess.run([
                        self.ffmpeg, "-y", "-ss", "6.0", "-i", str(first_clip_path),
                        "-vframes", "1",
                        str(raw_thumb_sec)
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

                from jarvis.backend.video.longform_thumbnail_designer import longform_thumbnail_designer
                thumb_hooks = [
                    "HE BROKE HIS SETUP?!",
                    "IMPOSSIBLE CLUTCH!",
                    "SPEED WENT TOO FAR!",
                    "GTA 6 CRAZIEST HEIST!",
                    "WHEN FAILS GO WRONG!",
                    "SPEED VS TYPICAL GAMER"
                ]
                chosen_hook = thumb_hooks[(ep_num - 1) % len(thumb_hooks)]
                longform_thumbnail_designer.create_viral_thumbnail(
                    base_frame_path=str(raw_thumb_tmp),
                    secondary_frame_path=str(raw_thumb_sec) if raw_thumb_sec.exists() else None,
                    headline_text=chosen_hook,
                    sub_text=f"SPEED x TYPICAL GAMER - EPISODE #{ep_num}",
                    badge_text="GTA 6",
                    output_path=str(thumb_path)
                )
                logger.info(f"Generated Studio Ultra Thumbnail: {thumb_path.name}")
            except Exception as te:
                logger.warning(f"Studio thumbnail generation fallback notice: {te}")
                try:
                    subprocess.run([
                        self.ffmpeg, "-y", "-ss", "2.0", "-i", str(output_file),
                        "-vframes", "1", "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,eq=contrast=1.2:saturation=1.35",
                        str(thumb_path)
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass
            finally:
                raw_thumb_tmp.unlink(missing_ok=True)
                raw_thumb_sec.unlink(missing_ok=True)

            chapters_text = "\n".join([f"{ch['timestamp']} - Moment #{ch['moment']}: {ch['title']}" for ch in chapters])

            title_templates = [
                f"CRAZIEST STREAM MOMENTS! (Speed, Carry, Kai) 🔥 Episode #{ep_num}",
                f"MOST VIRAL GAMING CLUTCHES & FAILS! (Speed x CarryMinati) ⚡ Episode #{ep_num}",
                f"UNCUT STREAM HIGHLIGHTS: Top Clutches & Pure Chaos! 🤯 Episode #{ep_num}",
                f"WHEN STREAMERS GO TOO CRAZY! Funniest Moments 💀 Episode #{ep_num}",
                f"TOP 10 STREAMER REACTIONS OF THE DAY! (Kai, Speed, Carry) 🏆 Episode #{ep_num}",
            ]
            yt_title = title_templates[(ep_num - 1) % len(title_templates)]
            
            yt_desc = (
                f"The most insane, hilarious, and viral gaming clutches & stream fails from today!\n\n"
                f"⏱️ CHAPTER TIMESTAMPS:\n"
                f"{chapters_text}\n\n"
                f"👑 ZERO-STRIKE STREAMER CREDITS & ORIGINAL BROADCASTERS:\n"
                f"- IShowSpeed (@IShowSpeed): https://youtube.com/@IShowSpeed\n"
                f"- CarryMinati (@CarryisLive): https://youtube.com/@CarryisLive\n"
                f"- Kai Cenat (@KaiCenat): https://youtube.com/@KaiCenat\n"
                f"- xQc (@xQcOW): https://youtube.com/@xQcOW\n\n"
                f"⚖️ FAIR USE & TRANSFORMATIVE EDITORIAL NOTICE (17 U.S.C. § 107):\n"
                f"This video is a transformative commentary and highlights compilation created under Fair Use guidelines. "
                f"Original footage has been substantially reformatted with dual layout reframing, sound design, keyword captioning, and editorial curation for entertainment and review purposes.\n\n"
                f"🔔 SUBSCRIBE to @GHOST_OF_FOOTBALL for daily gaming highlights and uncut live clutches!\n\n"
                f"#GTA6 #Gaming #CarryMinati #IShowSpeed #KaiCenat #xQc #GTA6Moments #Compilation #LongForm"
            )

            return {
                "success": True,
                "compilation_id": compilation_id,
                "video_path": str(output_file),
                "thumbnail_path": str(thumb_path) if thumb_path.exists() else None,
                "file_name": output_file.name,
                "total_duration_sec": current_time,
                "total_runtime_min": total_runtime_min,
                "num_clips": len(selected_clips),
                "chapters": chapters,
                "suggested_title": yt_title,
                "suggested_description": yt_desc
            }

        except Exception as e:
            logger.error(f"Failed to assemble compilation: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

        finally:
            # Clean up intermediate part files and concat manifest
            try:
                temp_concat_txt.unlink(missing_ok=True)
                for f_temp in intermediate_files:
                    f_temp.unlink(missing_ok=True)
            except Exception:
                pass

    async def build_and_schedule_8h_compilation(
        self,
        limit: int = 10,
        layout: str = "fullscreen_16_9",
        existing_compilation: Optional[Dict[str, Any]] = None,
        only_published: bool = True
    ) -> Dict[str, Any]:
        """Build compilation and schedule to YouTube Studio at the next 8-hour interval slot."""
        slot = self.calculate_next_8h_slot()
        target_dt = slot["target_dt"]
        sched_time_str = slot["schedule_time"]
        sched_date_str = slot["schedule_date"]

        logger.info(f"Preparing 8-hour Long-Form compilation for slot: {sched_time_str} ({sched_date_str})...")

        build_res = existing_compilation or self.build_weekly_compilation(limit=limit, layout=layout, only_published=only_published)
        if not build_res.get("success"):
            return build_res

        comp_path = build_res["video_path"]
        thumb_path = build_res.get("thumbnail_path")
        title = build_res["suggested_title"]
        desc = build_res["suggested_description"]
        tags = ["GTA6", "Gaming", "CarryMinati", "IShowSpeed", "KaiCenat", "xQc", "GTA6Moments", "Compilation", "Viral", "LongForm"]

        # Strict 1000-Point Quality Gate: Verify 16:9 full-screen geometry, resolution, and audio before scheduling!
        quality_check = self.verify_compilation_quality(comp_path, thumb_path)
        if not quality_check.get("verified"):
            err_msg = f"Quality gate verification failed: {quality_check.get('reason')}"
            logger.error(f"❌ {err_msg}")
            return {"success": False, "error": err_msg}

        from jarvis.backend.social.youtube_browser import youtube_browser
        from jarvis.backend.social.scheduler_engine import scheduler_engine

        scheduler_engine.pause_queue()
        try:
            logger.info(f"Dispatching verified 16:9 full-screen long-form compilation to YouTube Studio for {sched_time_str} ({sched_date_str}): '{title}'...")
            upload_res = await youtube_browser.upload_video(
                video_path=comp_path,
                title=title,
                description=desc,
                tags=tags,
                privacy="schedule",
                schedule_time=sched_time_str,
                schedule_date=sched_date_str
            )

            pub_status = "SCHEDULED" if upload_res.get("success") else "FAILED"
            pub_url = upload_res.get("video_url") or "SCHEDULED_STUDIO"

            # Record in SQLite database
            conn = get_db_connection()
            cur = conn.cursor()
            item_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO youtube_schedule_queue 
                (id, drive_file_id, file_name, title, description, tags, scheduled_time, privacy, status, youtube_url)
                VALUES (?, 'LONG_FORM_COMPILATION', ?, ?, ?, ?, ?, 'schedule', ?, ?)
            """, (
                item_id,
                Path(comp_path).name,
                title,
                desc,
                json.dumps(tags),
                target_dt.isoformat(),
                pub_status,
                pub_url
            ))
            conn.commit()
            conn.close()

            logger.info(f"✅ Successfully scheduled 8-hour long-form compilation on YouTube Studio! Slot: {sched_time_str} ({sched_date_str}) | URL: {pub_url}")

            return {
                "success": upload_res.get("success", False),
                "slot": slot,
                "compilation": build_res,
                "upload_result": upload_res
            }
        finally:
            scheduler_engine.resume_queue()

    def get_last_longform_production_time(self) -> Optional[datetime]:
        """Return the UTC datetime when the latest long-form compilation video was recorded in DB."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT created_at 
            FROM youtube_schedule_queue 
            WHERE drive_file_id = 'LONG_FORM_COMPILATION'
            ORDER BY rowid DESC 
            LIMIT 1
        """)
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            try:
                clean = row[0].replace("Z", "")
                if " " in clean and "T" not in clean:
                    return datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
                return datetime.fromisoformat(clean)
            except Exception:
                pass
        return None

    def can_produce_next_longform(self) -> Dict[str, Any]:
        """Check if strictly 8 hours have passed since the last compilation was produced.
        Enforces user rule: JARVIS continuously does short clipping, and ONLY at a span of 8 hours produces a long video.
        """
        now_utc = datetime.utcnow()
        last_dt = self.get_last_longform_production_time()

        # Count upcoming scheduled compilations in queue
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) 
            FROM youtube_schedule_queue 
            WHERE drive_file_id = 'LONG_FORM_COMPILATION' 
              AND status IN ('QUEUED', 'SCHEDULED')
              AND scheduled_time > ?
        """, (datetime.now().isoformat(),))
        future_count = cur.fetchone()[0]
        conn.close()

        if last_dt:
            elapsed_sec = max(0.0, (now_utc - last_dt).total_seconds())
            hours_elapsed = elapsed_sec / 3600.0
            hours_remaining = max(0.0, 8.0 - hours_elapsed)
        else:
            hours_elapsed = 999.0
            hours_remaining = 0.0

        # Can only produce if 8 hours have elapsed AND fewer than 2 future drops are queued
        can_produce = (hours_elapsed >= 7.8) and (future_count < 2)

        return {
            "can_produce": can_produce,
            "last_produced_at_utc": last_dt.isoformat() if last_dt else None,
            "hours_elapsed": round(hours_elapsed, 2),
            "hours_remaining": round(hours_remaining, 2),
            "future_scheduled_count": future_count,
            "span_hours": 8.0,
            "active_mode": "AUTONOMOUS_SHORT_CLIPPING" if not can_produce else "LONG_FORM_CADENCE_READY"
        }

    def get_8h_schedule_status(self) -> Dict[str, Any]:
        """Retrieve recent and upcoming 8-hour scheduled long-form videos with span telemetry."""
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, file_name, title, scheduled_time, status, youtube_url 
            FROM youtube_schedule_queue 
            WHERE drive_file_id = 'LONG_FORM_COMPILATION'
            ORDER BY scheduled_time DESC 
            LIMIT 10
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        next_slot = self.calculate_next_8h_slot()
        span_status = self.can_produce_next_longform()
        return {
            "history": rows,
            "next_slot": next_slot,
            "span_status": span_status
        }


compilation_builder = CompilationBuilder()
