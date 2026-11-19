"""Autonomous YouTube Shorts Queue & Scheduling Engine with Anti-Ban Protection.

Manages large-scale batch video imports (e.g., 1000+ Google Drive videos),
enforces humanized pacing (e.g. 1 hour interval with organic jitter),
maintains night-time rest intervals and daily upload safety caps,
and coordinates automated video downloading, publishing, and cleanup.
"""

import os
import re
import sys
import json
import uuid
import random
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
try:
    import gdown
except ImportError:
    gdown = None

from jarvis.backend.config.settings import WORKSPACE_ROOT
from jarvis.backend.database.db import get_db_connection
from jarvis.backend.social.youtube_browser import youtube_browser
from jarvis.backend.social.instagram_browser import instagram_browser
from jarvis.backend.security.permissions import security_guard

logger = logging.getLogger("JARVIS.SchedulerEngine")

TEMP_QUEUE_DIR = WORKSPACE_ROOT / "jarvis" / "output" / "queue_downloads"
TEMP_QUEUE_DIR.mkdir(parents=True, exist_ok=True)


class YouTubeSchedulerEngine:
    def __init__(self):
        self.is_paused = False
        self.worker_task: Optional[asyncio.Task] = None
        self._current_uploading_id: Optional[str] = None

    @staticmethod
    def extract_clean_metadata(raw_filename: str) -> Dict[str, Any]:
        """Convert raw video filename into clean, high-CTR viral title, tags, and caption."""
        name = Path(raw_filename).name
        # Remove leading timestamps and IDs like '20250413_.lucaae0_7492798674737663262_'
        clean = re.sub(r"^\d+_[^_]+_\d+_", "", name)
        clean = re.sub(r"\.(mp4|mov|avi|mkv)$", "", clean, flags=re.IGNORECASE)
        clean = clean.replace("_", " ").strip()

        if not clean:
            clean = "Epic Football Skills & Highlights"

        # Emojis and Hook styling
        football_emojis = ["⚽🔥", "⚽⚡", "👑⚽", "🥶⚽", "🤯⚽", "🏆⚡"]
        emoji = random.choice(football_emojis)

        title = f"{clean.title()} {emoji} #Shorts"
        if len(title) > 95:
            title = f"{clean[:80]}... {emoji} #Shorts"

        # Entity keyword extraction for tags
        tags = ["Shorts", "Football", "Soccer", "GHOST_OF_FOOTBALL", "Viral", "Trending"]
        lower_clean = clean.lower()
        if "mbappe" in lower_clean or "mbappé" in lower_clean:
            tags.extend(["Mbappe", "KylianMbappe", "RealMadrid", "France"])
        if "haaland" in lower_clean:
            tags.extend(["Haaland", "ErlingHaaland", "ManCity"])
        if "ronaldo" in lower_clean or "cr7" in lower_clean:
            tags.extend(["Ronaldo", "CR7", "AlNassr"])
        if "messi" in lower_clean:
            tags.extend(["Messi", "InterMiami", "Argentina"])
        if "yamal" in lower_clean:
            tags.extend(["LamineYamal", "Barcelona"])
        if "world cup" in lower_clean:
            tags.extend(["WorldCup", "FIFAWorldCup"])

        # Deduplicate tags
        tags = list(dict.fromkeys(tags))

        hashtags_str = " ".join([f"#{t}" for t in tags[:8]])
        caption = (
            f"{clean}!\n\n"
            f"Watch the best football moments daily on GHOST _OF_FOOTBALL.\n"
            f"👉 Hit Like and Subscribe for non-stop football edits!\n\n"
            f"{hashtags_str}"
        )

        return {
            "title": title,
            "description": caption,
            "tags": " ".join(tags)
        }

    def import_drive_folder(
        self,
        folder_url: str,
        interval_minutes: int = 60,
        daily_cap: int = 18,
        apply_jitter: bool = True,
        start_delay_minutes: int = 5
    ) -> Dict[str, Any]:
        """Scan Drive folder and build 1-hour interval schedule queue with anti-ban safeguards."""
        logger.info(f"Scanning Drive folder: {folder_url} for batch scheduling...")
        try:
            files = gdown.download_folder(url=folder_url, skip_download=True, quiet=True)
        except Exception as e:
            logger.error(f"Failed to scan Google Drive folder: {e}", exc_info=True)
            raise ValueError(f"Could not read Drive folder: {str(e)}")

        if not files:
            raise ValueError("No files found in the provided Google Drive folder.")

        # Filter for video files
        video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
        video_files = []
        for f in files:
            p = getattr(f, "path", None) or str(f)
            if any(p.lower().endswith(ext) for ext in video_extensions):
                video_files.append(f)

        if not video_files:
            raise ValueError(f"Found {len(files)} files, but none were recognized video formats (.mp4, .mov, etc.).")

        logger.info(f"Identified {len(video_files)} video files in folder. Generating schedule...")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check existing scheduled items to append after last scheduled time if any
        cursor.execute("SELECT MAX(scheduled_time) FROM youtube_schedule_queue WHERE status = 'QUEUED'")
        last_sched = cursor.fetchone()[0]

        if last_sched:
            try:
                current_time = datetime.fromisoformat(last_sched) + timedelta(minutes=interval_minutes)
            except Exception:
                current_time = datetime.now() + timedelta(minutes=start_delay_minutes)
        else:
            current_time = datetime.now() + timedelta(minutes=start_delay_minutes)

        queued_items = []
        daily_counter = 0

        for f in video_files:
            file_id = getattr(f, "id", None)
            file_path = getattr(f, "path", None) or str(f)
            file_name = Path(file_path).name

            if not file_id:
                continue

            # Anti-ban organic jitter (e.g. ±5 to 10 minutes variance)
            if apply_jitter:
                jitter_seconds = random.randint(-420, 480) # -7 to +8 minutes
            else:
                jitter_seconds = 0

            scheduled_dt = current_time + timedelta(seconds=jitter_seconds)
            # Ensure it never schedules in the past
            if scheduled_dt < datetime.now() + timedelta(minutes=2):
                scheduled_dt = datetime.now() + timedelta(minutes=5)

            meta = self.extract_clean_metadata(file_name)
            item_id = str(uuid.uuid4())

            queued_items.append((
                item_id,
                file_id,
                file_name,
                meta["title"],
                meta["description"],
                meta["tags"],
                scheduled_dt.isoformat(),
                "QUEUED"
            ))

            # Pacing increment
            current_time += timedelta(minutes=interval_minutes)
            daily_counter += 1

            # Anti-ban night rest window: Real humans sleep!
            # After reaching daily cap (e.g. 18 videos), pause for 7-8 hours
            if daily_counter >= daily_cap:
                current_time += timedelta(hours=7, minutes=random.randint(15, 45))
                daily_counter = 0

        # Bulk insert into database
        cursor.executemany("""
            INSERT INTO youtube_schedule_queue 
            (id, drive_file_id, file_name, title, description, tags, scheduled_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, queued_items)

        conn.commit()
        conn.close()

        first_time = queued_items[0][6] if queued_items else None
        last_time = queued_items[-1][6] if queued_items else None

        logger.info(f"Successfully queued {len(queued_items)} videos from Drive folder!")
        return {
            "success": True,
            "total_imported": len(queued_items),
            "interval_minutes": interval_minutes,
            "daily_cap": daily_cap,
            "first_scheduled": first_time,
            "last_scheduled": last_time,
            "anti_ban_jitter": apply_jitter,
            "message": f"Successfully queued {len(queued_items)} videos! Dispatches start at {first_time} spaced ~{interval_minutes}m apart with anti-ban safety cap."
        }

    def get_queue_stats(self) -> Dict[str, Any]:
        """Retrieve telemetry, counters, and anti-ban shield status."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM youtube_schedule_queue")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM youtube_schedule_queue WHERE status = 'QUEUED'")
        queued = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM youtube_schedule_queue WHERE status = 'PUBLISHED'")
        published = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM youtube_schedule_queue WHERE status = 'FAILED'")
        failed = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM youtube_schedule_queue WHERE status = 'QUEUED' ORDER BY scheduled_time ASC LIMIT 1")
        next_row = cursor.fetchone()
        next_item = dict(next_row) if next_row else None

        # Count published in last 24 hours
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM youtube_schedule_queue WHERE status = 'PUBLISHED' AND published_at >= ?", (yesterday,))
        published_today = cursor.fetchone()[0]

        conn.close()

        # Compute seconds until next
        seconds_until_next = None
        if next_item and next_item.get("scheduled_time"):
            try:
                next_dt = datetime.fromisoformat(next_item["scheduled_time"])
                seconds_until_next = max(0, int((next_dt - datetime.now()).total_seconds()))
            except Exception:
                pass

        return {
            "total": total,
            "queued": queued,
            "published": published,
            "failed": failed,
            "published_last_24h": published_today,
            "is_paused": self.is_paused,
            "current_uploading_id": self._current_uploading_id,
            "next_item": next_item,
            "seconds_until_next": seconds_until_next,
            "anti_ban_shield": {
                "active": True,
                "daily_safe_cap": 18,
                "current_daily_count": published_today,
                "pacing": "60m ± 8m jitter",
                "human_rest_cycles": "7h night window enabled"
            }
        }

    def get_instagram_queue_stats(self) -> Dict[str, Any]:
        """Retrieve telemetry, counters, and status for Instagram queue."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM instagram_schedule_queue")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM instagram_schedule_queue WHERE status = 'QUEUED'")
        queued = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM instagram_schedule_queue WHERE status = 'PUBLISHED'")
        published = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM instagram_schedule_queue WHERE status = 'FAILED'")
        failed = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM instagram_schedule_queue WHERE status = 'QUEUED' ORDER BY scheduled_time ASC LIMIT 1")
        next_row = cursor.fetchone()
        next_item = dict(next_row) if next_row else None

        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM instagram_schedule_queue WHERE status = 'PUBLISHED' AND published_at >= ?", (yesterday,))
        published_today = cursor.fetchone()[0]

        conn.close()

        seconds_until_next = None
        if next_item and next_item.get("scheduled_time"):
            try:
                next_dt = datetime.fromisoformat(next_item["scheduled_time"])
                seconds_until_next = max(0, int((next_dt - datetime.now()).total_seconds()))
            except Exception:
                pass

        return {
            "total": total,
            "queued": queued,
            "published": published,
            "failed": failed,
            "published_last_24h": published_today,
            "next_item": next_item,
            "seconds_until_next": seconds_until_next
        }

    def list_queue(self, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List queue items with pagination."""
        conn = get_db_connection()
        cursor = conn.cursor()

        if status:
            cursor.execute(
                "SELECT * FROM youtube_schedule_queue WHERE status = ? ORDER BY scheduled_time ASC LIMIT ? OFFSET ?",
                (status, limit, offset)
            )
        else:
            cursor.execute(
                "SELECT * FROM youtube_schedule_queue ORDER BY scheduled_time ASC LIMIT ? OFFSET ?",
                (limit, offset)
            )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def pause_queue(self) -> Dict[str, Any]:
        self.is_paused = True
        logger.info("YouTube schedule queue paused.")
        return {"success": True, "is_paused": True, "message": "Queue paused."}

    def resume_queue(self) -> Dict[str, Any]:
        self.is_paused = False
        logger.info("YouTube schedule queue resumed.")
        return {"success": True, "is_paused": False, "message": "Queue resumed."}

    def clear_queue(self) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM youtube_schedule_queue WHERE status = 'QUEUED'")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        logger.info(f"Cleared {count} queued items from database.")
        return {"success": True, "cleared_count": count}

    def delete_queue_item(self, item_id: str) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM youtube_schedule_queue WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        return {"success": True, "item_id": item_id}

    def enqueue_clip(
        self,
        clip_id: str,
        video_path: str,
        title: str,
        description: str,
        tags: Any,
        scheduled_time: Optional[str] = None,
        privacy: str = "public",
        interval_minutes: int = 45
    ) -> Dict[str, Any]:
        """Enqueue a local vertical short into the YouTube schedule queue."""
        conn = get_db_connection()
        cursor = conn.cursor()

        if not scheduled_time:
            # Query last scheduled QUEUED item to append after it
            cursor.execute("SELECT MAX(scheduled_time) FROM youtube_schedule_queue WHERE status = 'QUEUED'")
            last_sched = cursor.fetchone()[0]
            if last_sched:
                try:
                    next_dt = datetime.fromisoformat(last_sched) + timedelta(minutes=interval_minutes)
                except Exception:
                    next_dt = datetime.now() + timedelta(minutes=interval_minutes)
            else:
                next_dt = datetime.now() + timedelta(minutes=interval_minutes)
            scheduled_time = next_dt.isoformat()

        item_id = str(uuid.uuid4())
        file_name = Path(video_path).name
        tags_str = " ".join(tags) if isinstance(tags, list) else str(tags)

        cursor.execute("""
            INSERT INTO youtube_schedule_queue 
            (id, drive_file_id, file_name, title, description, tags, scheduled_time, privacy, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'QUEUED')
        """, (
            item_id,
            f"local:{video_path}",
            file_name,
            title,
            description,
            tags_str,
            scheduled_time,
            privacy
        ))

        # Update status in clips table
        cursor.execute("""
            UPDATE clips 
            SET published_youtube = 1, status = 'QUEUED_YOUTUBE' 
            WHERE id = ?
        """, (clip_id,))

        conn.commit()
        conn.close()

        logger.info(f"Enqueued local clip '{title}' for YouTube upload at {scheduled_time}")
        return {
            "success": True,
            "queue_id": item_id,
            "clip_id": clip_id,
            "title": title,
            "scheduled_time": scheduled_time
        }

    async def process_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Download or locate video, upload to YouTube Studio, record live URL, and manage cleanup."""
        item_id = item["id"]
        drive_file_id = item["drive_file_id"]
        title = item["title"]
        desc = item["description"]
        tags = item["tags"].split(" ") if item.get("tags") else []

        self._current_uploading_id = item_id
        is_local = False
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Check if this item is a local clip or a Drive file
            if drive_file_id.startswith("local:") or Path(drive_file_id).exists():
                local_path_str = drive_file_id.replace("local:", "")
                downloaded_path = Path(local_path_str).resolve()
                if not downloaded_path.exists():
                    raise FileNotFoundError(f"Local video file not found at: {downloaded_path}")
                is_local = True
                logger.info(f"Queue Worker: Using local video file at {downloaded_path} for '{title}'...")
            else:
                # 1. Update status to DOWNLOADING
                cursor.execute("UPDATE youtube_schedule_queue SET status = 'DOWNLOADING' WHERE id = ?", (item_id,))
                conn.commit()
                logger.info(f"Queue Worker: Downloading video {drive_file_id} for '{title}'...")

                temp_file = TEMP_QUEUE_DIR / f"queue_{drive_file_id[:10]}_{uuid.uuid4().hex[:4]}.mp4"
                loop = asyncio.get_event_loop()
                downloaded = await loop.run_in_executor(
                    None,
                    lambda: gdown.download(id=drive_file_id, output=str(temp_file), quiet=True)
                )

                if not downloaded or not Path(downloaded).exists():
                    raise FileNotFoundError(f"Failed to download Google Drive file {drive_file_id}")

                downloaded_path = Path(downloaded)

            # 2. Update status to UPLOADING
            cursor.execute("UPDATE youtube_schedule_queue SET status = 'UPLOADING' WHERE id = ?", (item_id,))
            conn.commit()
            logger.info(f"Queue Worker: Uploading {downloaded_path.name} to YouTube Studio...")

            # Format target date & time for native YouTube Studio scheduling
            sched_time_str = None
            sched_date_str = None
            scheduled_dt_str = item.get("scheduled_time")
            if scheduled_dt_str:
                try:
                    sdt = datetime.fromisoformat(scheduled_dt_str)
                    sched_time_str = sdt.strftime("%I:%M %p").lstrip("0")
                    sched_date_str = f"{sdt.strftime('%b')} {sdt.day}, {sdt.year}"
                except Exception:
                    pass

            target_privacy = item.get("privacy") or "public"
            upload_res = await youtube_browser.upload_video(
                video_path=str(downloaded_path),
                title=title,
                description=desc,
                tags=tags,
                privacy=target_privacy,
                schedule_time=sched_time_str if target_privacy == "schedule" else None,
                schedule_date=sched_date_str if target_privacy == "schedule" else None,
                headless=False,
                debate_comment=item.get("debate_comment")
            )

            if not upload_res.get("success"):
                raise RuntimeError(upload_res.get("error") or "Upload failed in Studio.")

            yt_url = upload_res.get("url")
            pub_time = datetime.now().isoformat()

            # 3. Update status to PUBLISHED
            cursor.execute("""
                UPDATE youtube_schedule_queue 
                SET status = 'PUBLISHED', youtube_url = ?, published_at = ?
                WHERE id = ?
            """, (yt_url, pub_time, item_id))
            conn.commit()
            logger.info(f"🎉 Queue Worker: Successfully published '{title}'! Live link: {yt_url}")

            # 4. Clean up downloaded temp file or local clip if not needed by other platforms
            try:
                from jarvis.backend.video.storage_cleaner import storage_cleaner
                storage_cleaner.cleanup_published_clip(str(downloaded_path))
            except Exception:
                pass

            return {"success": True, "youtube_url": yt_url, "title": title}

        except Exception as e:
            logger.error(f"Queue Worker: Error uploading item {item_id}: {e}", exc_info=True)
            err_str = str(e)
            if "daily upload limit" in err_str.lower():
                self.is_paused = True
                logger.warning("Pausing queue: YouTube daily upload limit reached.")

            cursor.execute("""
                UPDATE youtube_schedule_queue 
                SET status = 'FAILED', error_message = ?
                WHERE id = ?
            """, (err_str, item_id))
            conn.commit()
            # Clean up temp file on failure
            try:
                temp_file.unlink(missing_ok=True)
            except Exception:
                pass
            return {"success": False, "error": str(e)}

        finally:
            self._current_uploading_id = None
            conn.close()

    async def dispatch_next_now(self) -> Dict[str, Any]:
        """Manually trigger the next queued item immediately."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM youtube_schedule_queue WHERE status = 'QUEUED' ORDER BY scheduled_time ASC LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"success": False, "message": "No queued items available to dispatch."}

        item = dict(row)
        return await self.process_single_item(item)

    def reschedule_queue(
        self,
        interval_minutes: int = 45,
        start_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Reschedule all queued and failed items starting from start_time spaced interval_minutes apart."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch all non-published items in order
        cursor.execute("""
            SELECT id, title, scheduled_time, status 
            FROM youtube_schedule_queue 
            WHERE status IN ('FAILED', 'QUEUED')
            ORDER BY scheduled_time ASC
        """)
        rows = cursor.fetchall()

        if not rows:
            conn.close()
            return {"success": True, "count": 0, "message": "No queued or failed items to reschedule."}

        now = datetime.now()
        if start_time is None:
            # Round to next 15-minute slot at least 30 mins from now
            target = now + timedelta(minutes=interval_minutes)
            minute = ((target.minute // 15) + 1) * 15
            if minute >= 60:
                start_time = target.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            else:
                start_time = target.replace(minute=minute, second=0, microsecond=0)

        current_dt = start_time
        updates = []
        for r in rows:
            updates.append((current_dt.isoformat(), r["id"]))
            current_dt += timedelta(minutes=interval_minutes)

        cursor.executemany("""
            UPDATE youtube_schedule_queue 
            SET scheduled_time = ?, status = 'QUEUED', error_message = NULL
            WHERE id = ?
        """, updates)

        conn.commit()
        conn.close()

        first_iso = updates[0][0]
        last_iso = updates[-1][0]
        logger.info(f"Rescheduled {len(updates)} items with {interval_minutes}m spacing starting at {first_iso}")
        return {
            "success": True,
            "count": len(updates),
            "interval_minutes": interval_minutes,
            "first_scheduled": first_iso,
            "last_scheduled": last_iso
        }

    async def upload_today_batch_till_limit(self, interval_minutes: int = 45) -> Dict[str, Any]:
        """Upload videos sequentially for today, scheduling each 45 mins apart in YouTube Studio, until YouTube daily limit is reached."""
        logger.info(f"Starting batch YouTube dispatch till daily upload limit (spacing: {interval_minutes}m)...")
        self.is_paused = False

        # Only reschedule if no items are currently scheduled for today
        conn_check = get_db_connection()
        cur_check = conn_check.cursor()
        today_iso_prefix = f"{datetime.now().date().isoformat()}%"
        cur_check.execute("SELECT COUNT(*) FROM youtube_schedule_queue WHERE status = 'QUEUED' AND scheduled_time LIKE ?", (today_iso_prefix,))
        today_queued_count = cur_check.fetchone()[0]
        conn_check.close()

        if today_queued_count == 0:
            self.reschedule_queue(interval_minutes=interval_minutes)

        results = []
        limit_reached = False
        today_date = datetime.now().date()

        while True:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM youtube_schedule_queue 
                WHERE status = 'QUEUED'
                ORDER BY scheduled_time ASC LIMIT 1
            """)
            row = cur.fetchone()
            conn.close()

            if not row:
                logger.info("No more QUEUED items in database.")
                break

            item = dict(row)
            item_dt = datetime.fromisoformat(item["scheduled_time"])

            # If item is scheduled for tomorrow or later, and all of today's slots are done
            if item_dt.date() > today_date:
                logger.info(f"All items for today ({today_date}) have been processed! Next item is on {item_dt.date()}.")
                break

            logger.info(f"Batch Dispatcher: Processing '{item['title']}' scheduled for {item['scheduled_time']}...")
            res = await self.process_single_item(item)

            if res.get("success"):
                results.append({
                    "title": item["title"],
                    "scheduled_time": item["scheduled_time"],
                    "youtube_url": res.get("youtube_url")
                })
                logger.info(f"Batch Dispatcher: Successfully scheduled #{len(results)}: '{item['title']}' at {item['scheduled_time']}")
                # Brief organic pause between successive browser uploads
                await asyncio.sleep(15)
            else:
                err = res.get("error", "")
                if "daily upload limit" in err.lower():
                    logger.warning(f"YouTube Daily Upload Limit Reached on '{item['title']}'. Stopping batch today.")
                    limit_reached = True
                    break
                else:
                    logger.error(f"Upload failed for '{item['title']}': {err}")
                    # If it failed for another reason, stop so we don't loop endlessly
                    break

        return {
            "success": True,
            "uploaded_count": len(results),
            "limit_reached": limit_reached,
            "results": results,
            "message": (
                f"YouTube daily limit reached after scheduling {len(results)} videos."
                if limit_reached
                else f"Successfully scheduled all {len(results)} videos for today!"
            )
        }

    def calculate_adaptive_schedule_time(
        self,
        platform: str = "instagram",
        base_interval_minutes: int = 120,
        slot_index: int = 0
    ) -> datetime:
        """Dynamically compute the next publishing timestamp to maximize algorithmic reach and eliminate self-cannibalization.

        2026 Algorithmic Growth Pacing:
        - YouTube Shorts: Evaluates swipe-through rate (>75%) & retention (>100% APV) across seed cohorts (50-500 viewers).
          Requires a 2-3 hour (120-180m) evaluation window. Rapid posting cannibalizes impressions and triggers anti-spam throttling.
        - Instagram Reels: Primary discovery signal is DM Shares (Sends per Reach), completion, and saves.
          Requires 2-3 hour spacing to allow non-follower Explore page testing.
        - Cross-Platform Staggering: 30-45 minute offset between YouTube and Instagram to maximize cross-platform impressions.
        """
        table = "instagram_schedule_queue" if platform.lower() == "instagram" else "youtube_schedule_queue"
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(f"SELECT COUNT(*), MAX(scheduled_time) FROM {table} WHERE status = 'QUEUED'")
        row = cur.fetchone()
        queued_count = row[0] if row else 0
        last_queued_time_str = row[1] if row and row[1] else None

        cur.execute(f"SELECT MAX(published_at) FROM {table} WHERE status = 'PUBLISHED'")
        last_pub_row = cur.fetchone()
        last_pub_str = last_pub_row[0] if last_pub_row else None
        conn.close()

        now = datetime.now()

        # Establish reference anchor timestamp
        if last_queued_time_str:
            try:
                ref_dt = datetime.fromisoformat(last_queued_time_str)
                if ref_dt < now:
                    ref_dt = now
            except Exception:
                ref_dt = now
        elif last_pub_str:
            try:
                ref_dt = datetime.fromisoformat(last_pub_str)
                if ref_dt < now:
                    ref_dt = now
            except Exception:
                ref_dt = now
        else:
            ref_dt = now

        # Algorithm-Optimal 4-Slot Daily Windows (09:00 AM, 02:00 PM, 06:30 PM, 11:00 PM)
        from datetime import time as dt_time
        daily_times = [
            dt_time(9, 0),    # Morning Asia / US Late Night
            dt_time(14, 0),   # Midday Europe / Asia Afternoon
            dt_time(18, 30),  # Evening Europe Prime / US Morning
            dt_time(23, 0)    # Prime Night US Afternoon & Evening
        ]

        target_dt = None
        cur_date = ref_dt.date()
        for day_offset in range(45):
            d = cur_date + timedelta(days=day_offset)
            for t in daily_times:
                cand = datetime.combine(d, t)
                if platform.lower() == "instagram":
                    cand += timedelta(minutes=30)  # 30-minute cross-platform stagger
                if cand > ref_dt + timedelta(minutes=30) and cand > now + timedelta(minutes=15):
                    target_dt = cand
                    break
            if target_dt:
                break

        if not target_dt:
            target_dt = ref_dt + timedelta(hours=4)

        # Batch offset for multiple clips within the same cycle
        if slot_index > 0:
            cand2 = None
            cur_date2 = target_dt.date()
            for day_offset in range(45):
                d = cur_date2 + timedelta(days=day_offset)
                for t in daily_times:
                    cand = datetime.combine(d, t)
                    if platform.lower() == "instagram":
                        cand += timedelta(minutes=30)
                    if cand > target_dt + timedelta(minutes=30):
                        cand2 = cand
                        break
                if cand2:
                    break
            target_dt = cand2 or (target_dt + timedelta(hours=4))

        # Format YouTube Studio constraint (strictly 15-minute slot boundary)
        if platform.lower() == "youtube":
            remainder = target_dt.minute % 15
            if remainder != 0:
                target_dt += timedelta(minutes=(15 - remainder))
            target_dt = target_dt.replace(second=0, microsecond=0)
        else:
            target_dt = target_dt.replace(second=0, microsecond=0)

        return target_dt

    def schedule_month_algorithmic_cadence(self, days: int = 60) -> Dict[str, Any]:
        """Schedule all pending YouTube Shorts and Instagram Reels across the 4 daily global prime-time windows for the next 2 months."""
        from datetime import time as dt_time
        conn = get_db_connection()
        cur = conn.cursor()
        now = datetime.now()

        daily_times = [
            dt_time(9, 0),    # Morning Asia / US Late Night (09:00 AM)
            dt_time(14, 0),   # Midday Europe / Asia Afternoon (02:00 PM)
            dt_time(18, 30),  # Evening Europe Prime / US Morning (06:30 PM)
            dt_time(23, 0)    # Prime Night US Afternoon & Evening (11:00 PM)
        ]

        yt_slots = []
        ig_slots = []
        current_date = now.date()

        for day_offset in range(days + 30):
            day = current_date + timedelta(days=day_offset)
            for t in daily_times:
                slot_dt = datetime.combine(day, t)
                if slot_dt > now + timedelta(minutes=15):
                    yt_slots.append(slot_dt)
                    ig_slots.append(slot_dt + timedelta(minutes=30))

        # 1. Reschedule YouTube QUEUED items (excluding longform compilations)
        cur.execute("SELECT id FROM youtube_schedule_queue WHERE status = 'QUEUED' AND drive_file_id != 'LONG_FORM_COMPILATION' ORDER BY scheduled_time ASC")
        yt_rows = cur.fetchall()
        yt_updates = []
        for idx, r in enumerate(yt_rows):
            if idx < len(yt_slots):
                yt_updates.append((yt_slots[idx].isoformat(), r["id"]))

        if yt_updates:
            cur.executemany("UPDATE youtube_schedule_queue SET scheduled_time = ? WHERE id = ?", yt_updates)

        # 2. Reschedule Instagram QUEUED items
        cur.execute("SELECT id FROM instagram_schedule_queue WHERE status = 'QUEUED' ORDER BY scheduled_time ASC")
        ig_rows = cur.fetchall()
        ig_updates = []
        for idx, r in enumerate(ig_rows):
            if idx < len(ig_slots):
                ig_updates.append((ig_slots[idx].isoformat(), r["id"]))

        if ig_updates:
            cur.executemany("UPDATE instagram_schedule_queue SET scheduled_time = ? WHERE id = ?", ig_updates)

        conn.commit()
        conn.close()

        logger.info(f"1-Month Algorithmic Cadence: Scheduled {len(yt_updates)} YouTube Shorts and {len(ig_updates)} Instagram Reels into 4 prime daily windows.")
        return {
            "success": True,
            "youtube_count": len(yt_updates),
            "instagram_count": len(ig_updates),
            "youtube_first": yt_updates[0][0] if yt_updates else None,
            "youtube_last": yt_updates[-1][0] if yt_updates else None,
            "instagram_first": ig_updates[0][0] if ig_updates else None,
            "instagram_last": ig_updates[-1][0] if ig_updates else None,
            "daily_cadence": "4 slots/day (09:00 AM, 02:00 PM, 06:30 PM, 11:00 PM)"
        }

    def reschedule_all_queues_for_algorithm(
        self,
        interval_minutes: int = 120,
        yt_start_offset: int = 30,
        ig_start_offset: int = 75
    ) -> Dict[str, Any]:
        """Reschedule all pending QUEUED items in YouTube and Instagram with 2-hour (120m) algorithmic spacing to eliminate self-cannibalization."""
        conn = get_db_connection()
        cur = conn.cursor()
        now = datetime.now()

        # 1. Reschedule YouTube QUEUED items
        cur.execute("SELECT id FROM youtube_schedule_queue WHERE status = 'QUEUED' ORDER BY scheduled_time ASC")
        yt_rows = cur.fetchall()
        yt_updates = []
        cur_yt_dt = now + timedelta(minutes=yt_start_offset)
        rem = cur_yt_dt.minute % 15
        if rem != 0:
            cur_yt_dt += timedelta(minutes=(15 - rem))
        cur_yt_dt = cur_yt_dt.replace(second=0, microsecond=0)

        for r in yt_rows:
            yt_updates.append((cur_yt_dt.isoformat(), r["id"]))
            cur_yt_dt += timedelta(minutes=interval_minutes)

        if yt_updates:
            cur.executemany("UPDATE youtube_schedule_queue SET scheduled_time = ? WHERE id = ?", yt_updates)

        # 2. Reschedule Instagram QUEUED items
        cur.execute("SELECT id FROM instagram_schedule_queue WHERE status = 'QUEUED' ORDER BY scheduled_time ASC")
        ig_rows = cur.fetchall()
        ig_updates = []
        cur_ig_dt = now + timedelta(minutes=ig_start_offset)
        cur_ig_dt = cur_ig_dt.replace(second=0, microsecond=0)

        for r in ig_rows:
            ig_updates.append((cur_ig_dt.isoformat(), r["id"]))
            cur_ig_dt += timedelta(minutes=interval_minutes)

        if ig_updates:
            cur.executemany("UPDATE instagram_schedule_queue SET scheduled_time = ? WHERE id = ?", ig_updates)

        conn.commit()
        conn.close()

        logger.info(f"Algorithmic Reschedule: Spaced {len(yt_updates)} YouTube items and {len(ig_updates)} Instagram items {interval_minutes}m apart.")
        return {
            "success": True,
            "youtube_rescheduled": len(yt_updates),
            "instagram_rescheduled": len(ig_updates),
            "interval_minutes": interval_minutes,
            "youtube_next": yt_updates[0][0] if yt_updates else None,
            "instagram_next": ig_updates[0][0] if ig_updates else None
        }

    def schedule_instagram_reel(
        self,
        video_path: str,
        caption: str,
        scheduled_time: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Schedule a video to be posted as an Instagram Reel at a future time."""
        item_id = str(uuid.uuid4())
        file_name = Path(video_path).name
        tag_str = json.dumps(tags) if tags else "[]"

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO instagram_schedule_queue (id, video_path, file_name, caption, tags, scheduled_time, status)
            VALUES (?, ?, ?, ?, ?, ?, 'QUEUED')
        """, (item_id, video_path, file_name, caption, tag_str, scheduled_time))
        conn.commit()
        conn.close()

        logger.info(f"Queued Instagram Reel '{file_name}' for {scheduled_time} (ID: {item_id})")
        return {"success": True, "id": item_id, "scheduled_time": scheduled_time}

    def list_instagram_queue(self, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List queued Instagram items."""
        conn = get_db_connection()
        cur = conn.cursor()
        query = "SELECT * FROM instagram_schedule_queue"
        params: List[Any] = []
        if status and status != 'all':
            query += " WHERE status = ?"
            params.append(status.upper())
        query += " ORDER BY scheduled_time ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur.execute(query, tuple(params))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def delete_instagram_queue_item(self, item_id: str) -> Dict[str, Any]:
        """Delete an Instagram queue item."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM instagram_schedule_queue WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        return {"success": True, "deleted_id": item_id}

    async def process_single_instagram_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Publish due Instagram Reel from queue."""
        item_id = item["id"]
        video_path = item["video_path"]
        caption = item["caption"]
        tags = []
        try:
            tags = json.loads(item.get("tags") or "[]")
        except Exception:
            pass

        self._current_uploading_id = item_id
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE instagram_schedule_queue SET status = 'UPLOADING' WHERE id = ?", (item_id,))
        conn.commit()

        try:
            logger.info(f"Publishing queued Instagram Reel: {item['file_name']}")
            v_stem = Path(video_path).stem
            cand_thumb = WORKSPACE_ROOT / "jarvis" / "output" / "thumbnails" / f"{v_stem}_thumb.jpg"
            cover_path = str(cand_thumb) if cand_thumb.exists() else None

            res = await instagram_browser.upload_reel(
                video_path=video_path,
                caption=caption,
                tags=tags,
                cover_path=cover_path,
                headless=True
            )

            if res.get("success"):
                now_iso = datetime.now().isoformat()
                cur.execute(
                    "UPDATE instagram_schedule_queue SET status = 'PUBLISHED', published_at = ? WHERE id = ?",
                    (now_iso, item_id)
                )
                conn.commit()

                # Storage Guard: Auto-delete local video file and subtitles after successful publication
                try:
                    from jarvis.backend.video.storage_cleaner import storage_cleaner
                    storage_cleaner.cleanup_published_clip(video_path)
                except Exception as ce:
                    logger.warning(f"Storage cleanup notice after IG publish: {ce}")

                return {"success": True, "id": item_id}
            else:
                err = res.get("error", "Unknown Instagram upload failure")
                cur.execute("UPDATE instagram_schedule_queue SET status = 'FAILED', error_message = ? WHERE id = ?", (err, item_id))
                conn.commit()
                return {"success": False, "error": err}
        except Exception as e:
            cur.execute("UPDATE instagram_schedule_queue SET status = 'FAILED', error_message = ? WHERE id = ?", (str(e), item_id))
            conn.commit()
            return {"success": False, "error": str(e)}
        finally:
            self._current_uploading_id = None
            conn.close()

    async def run_worker_loop(self):
        """Continuous background worker that checks both YouTube and Instagram queues every 30 seconds."""
        logger.info("Autonomous Social Schedule Worker Loop started (YouTube & Instagram).")
        loop_counter = 0
        while True:
            try:
                loop_counter += 1
                now_iso = datetime.now().isoformat()
                conn = get_db_connection()
                cursor = conn.cursor()

                # 1. Check YouTube Queue (with Anti-Cannibalization Cooldown Guard)
                yt_row = None
                if not self.is_paused and not self._current_uploading_id:
                    cursor.execute("SELECT MAX(published_at) FROM youtube_schedule_queue WHERE status = 'PUBLISHED'")
                    last_yt_pub = cursor.fetchone()[0]
                    yt_cooldown_ok = True
                    if last_yt_pub:
                        try:
                            last_yt_dt = datetime.fromisoformat(last_yt_pub)
                            mins_since_pub = (datetime.now() - last_yt_dt).total_seconds() / 60.0
                            if mins_since_pub < 90:
                                yt_cooldown_ok = False
                                if loop_counter % 20 == 0:
                                    logger.info(f"⏳ YouTube Algorithmic Cooldown: Last Short published {mins_since_pub:.1f}m ago. Maintaining 90m+ seed audience runway to prevent self-cannibalization.")
                        except Exception:
                            pass

                    if yt_cooldown_ok:
                        cursor.execute("""
                            SELECT * FROM youtube_schedule_queue 
                            WHERE status = 'QUEUED' AND scheduled_time <= ?
                            ORDER BY scheduled_time ASC LIMIT 1
                        """, (now_iso,))
                        yt_row = cursor.fetchone()

                # 2. Check Instagram Queue (with Anti-Cannibalization Cooldown Guard)
                ig_row = None
                if not self._current_uploading_id:
                    cursor.execute("SELECT MAX(published_at) FROM instagram_schedule_queue WHERE status = 'PUBLISHED'")
                    last_ig_pub = cursor.fetchone()[0]
                    ig_cooldown_ok = True
                    if last_ig_pub:
                        try:
                            last_ig_dt = datetime.fromisoformat(last_ig_pub)
                            mins_since_ig = (datetime.now() - last_ig_dt).total_seconds() / 60.0
                            if mins_since_ig < 90:
                                ig_cooldown_ok = False
                                if loop_counter % 20 == 0:
                                    logger.info(f"⏳ Instagram Algorithmic Cooldown: Last Reel published {mins_since_ig:.1f}m ago. Protecting DM share velocity & explore seeding runway.")
                        except Exception:
                            pass

                    if ig_cooldown_ok:
                        cursor.execute("""
                            SELECT * FROM instagram_schedule_queue
                            WHERE status = 'QUEUED' AND scheduled_time <= ?
                            ORDER BY scheduled_time ASC LIMIT 1
                        """, (now_iso,))
                        ig_row = cursor.fetchone()

                conn.close()

                if yt_row:
                    item = dict(yt_row)
                    logger.info(f"Queue Worker: Found due YouTube item: '{item['title']}' (scheduled: {item['scheduled_time']})")
                    await self.process_single_item(item)
                elif ig_row and not self._current_uploading_id:
                    item = dict(ig_row)
                    logger.info(f"Queue Worker: Found due Instagram Reel: '{item['file_name']}' (scheduled: {item['scheduled_time']})")
                    await self.process_single_instagram_item(item)

                # 3. Periodic Background Storage Maintenance Sweep (Every ~15 minutes)
                if loop_counter % 30 == 0:
                    try:
                        from jarvis.backend.video.storage_cleaner import storage_cleaner
                        storage_cleaner.run_full_storage_maintenance()
                    except Exception as ce:
                        logger.debug(f"Periodic storage cleanup error: {ce}")

                # 4. Strict 8-Hour Long-Form Compilation Span Check (Only at span of 8 hours)
                if loop_counter % 60 == 0:  # Check every ~30 minutes
                    try:
                        from jarvis.backend.video.compilation_builder import compilation_builder
                        span_check = compilation_builder.can_produce_next_longform()
                        if span_check["can_produce"] and not self.is_paused and not self._current_uploading_id:
                            next_slot = compilation_builder.calculate_next_8h_slot()
                            logger.info(
                                f"🎬 Long-Form Engine: 8-hour span reached ({span_check['hours_elapsed']}h elapsed). "
                                f"Producing and scheduling next long-form video from published clips for {next_slot['schedule_time']} ({next_slot['schedule_date']})..."
                            )
                            asyncio.create_task(compilation_builder.build_and_schedule_8h_compilation(limit=10, only_published=True))
                        else:
                            logger.debug(
                                f"⏳ Long-Form Engine: 8-hour cooldown active. Continuing short clipping. "
                                f"Remaining until next 8h span: {span_check['hours_remaining']}h | Future scheduled drops: {span_check['future_scheduled_count']}"
                            )
                    except Exception as lfe:
                        logger.debug(f"Periodic long-form 8h scheduler notice: {lfe}")

            except Exception as e:
                logger.error(f"Error in queue worker loop: {e}", exc_info=True)

            await asyncio.sleep(30)


scheduler_engine = YouTubeSchedulerEngine()

