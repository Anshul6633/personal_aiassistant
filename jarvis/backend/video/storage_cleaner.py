"""Storage Maintenance & Auto-Deletion Engine.

Automatically purges video files, temporary raw live stream slices, demuxed audio,
and subtitle artifacts after successful publication to YouTube and Instagram.
Keeps disk usage minimal and prevents storage exhaustion during 24/7 continuous clipping.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Set
from jarvis.backend.config.settings import OUTPUT_DIR
from jarvis.backend.database.db import get_db_connection

logger = logging.getLogger("JARVIS.StorageCleaner")

REELS_DIR = OUTPUT_DIR / "reels"
LIVESTREAMS_DIR = OUTPUT_DIR / "livestreams"
TEMP_AUDIO_DIR = OUTPUT_DIR / "temp_audio"
SUBTITLES_DIR = OUTPUT_DIR / "subtitles"
QUEUE_DOWNLOADS_DIR = OUTPUT_DIR / "queue_downloads"


class StorageCleaner:
    @staticmethod
    def get_protected_filenames() -> Set[str]:
        """Fetch all filenames that are currently QUEUED or UPLOADING in any platform queue.
        
        These files MUST NOT be deleted.
        """
        protected = set()
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Instagram queue
            cur.execute("SELECT file_name, video_path FROM instagram_schedule_queue WHERE status IN ('QUEUED', 'UPLOADING')")
            for row in cur.fetchall():
                if row[0]:
                    protected.add(Path(row[0]).name)
                if row[1]:
                    protected.add(Path(row[1]).name)

            # YouTube queue
            cur.execute("SELECT file_name, drive_file_id FROM youtube_schedule_queue WHERE status IN ('QUEUED', 'UPLOADING', 'DOWNLOADING')")
            for row in cur.fetchall():
                if row[0]:
                    protected.add(Path(row[0]).name)
                if row[1] and row[1].startswith("local:"):
                    protected.add(Path(row[1].replace("local:", "")).name)

            conn.close()
        except Exception as e:
            logger.warning(f"Error fetching protected queue files: {e}")

        return protected

    @classmethod
    def delete_file_safely(cls, file_path: Path) -> int:
        """Delete a file and return the number of bytes freed."""
        try:
            if file_path.exists() and file_path.is_file():
                size = file_path.stat().st_size
                file_path.unlink(missing_ok=True)
                return size
        except Exception as e:
            logger.warning(f"Could not delete {file_path.name}: {e}")
        return 0

    @classmethod
    def cleanup_published_clip(cls, video_path_str: str) -> bool:
        """Delete a specific published video file and its associated subtitle file."""
        try:
            v_path = Path(video_path_str)
            protected = cls.get_protected_filenames()

            # Ensure the file is not currently queued in another platform
            if v_path.name in protected:
                logger.info(f"Skipping deletion: '{v_path.name}' is still queued for another platform.")
                return False

            freed = 0
            if v_path.exists():
                freed += cls.delete_file_safely(v_path)
                logger.info(f"🗑️ Storage Guard: Deleted published video file: {v_path.name} ({freed / (1024*1024):.1f} MB freed)")

            # Also clean up matching .ass subtitle file
            ass_path = SUBTITLES_DIR / f"{v_path.stem}.ass"
            if ass_path.exists():
                cls.delete_file_safely(ass_path)

            return True
        except Exception as e:
            logger.error(f"Error in cleanup_published_clip: {e}")
            return False

    @classmethod
    def cleanup_raw_slice(cls, slice_path_str: str) -> bool:
        """Delete raw 180s live stream recording slice once clipping is finished."""
        try:
            s_path = Path(slice_path_str)
            if s_path.exists():
                freed = cls.delete_file_safely(s_path)
                logger.info(f"🧹 Storage Guard: Purged temporary stream recording slice: {s_path.name} ({freed / (1024*1024):.1f} MB freed)")
                return True
        except Exception as e:
            logger.warning(f"Error purging raw slice: {e}")
        return False

    @classmethod
    def cleanup_temp_audio(cls, wav_path_str: str) -> bool:
        """Delete temporary demuxed whisper audio file."""
        try:
            w_path = Path(wav_path_str)
            if w_path.exists():
                cls.delete_file_safely(w_path)
                return True
        except Exception:
            pass
        return False

    @classmethod
    def run_full_storage_maintenance(cls) -> Dict[str, Any]:
        """Comprehensive sweep to purge published reels, old stream slices, and intermediate files."""
        freed_bytes = 0
        deleted_files: List[str] = []
        protected = cls.get_protected_filenames()
        now = time.time()

        # 1. Purge published reels from disk
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT video_path, file_name FROM instagram_schedule_queue WHERE status = 'PUBLISHED'")
            published_ig = cur.fetchall()
            conn.close()

            for row in published_ig:
                vpath = row[0]
                fname = row[1]
                if fname not in protected and vpath:
                    p = Path(vpath)
                    if p.exists():
                        size = cls.delete_file_safely(p)
                        if size > 0:
                            freed_bytes += size
                            deleted_files.append(p.name)
                            # Remove subtitle
                            sub = SUBTITLES_DIR / f"{p.stem}.ass"
                            cls.delete_file_safely(sub)
        except Exception as e:
            logger.warning(f"Error purging published IG reels: {e}")

        # 2. Purge raw livestream slices older than 5 minutes
        if LIVESTREAMS_DIR.exists():
            for f in LIVESTREAMS_DIR.glob("*.mp4"):
                try:
                    # If file is older than 5 minutes (300s)
                    if (now - f.stat().st_mtime) > 300:
                        size = cls.delete_file_safely(f)
                        if size > 0:
                            freed_bytes += size
                            deleted_files.append(f.name)
                except Exception:
                    pass

        # 3. Purge temp audio WAV files older than 3 minutes
        if TEMP_AUDIO_DIR.exists():
            for f in TEMP_AUDIO_DIR.glob("*.wav"):
                try:
                    if (now - f.stat().st_mtime) > 180:
                        size = cls.delete_file_safely(f)
                        if size > 0:
                            freed_bytes += size
                            deleted_files.append(f.name)
                except Exception:
                    pass

        # 4. Purge temporary queue downloads older than 10 minutes
        if QUEUE_DOWNLOADS_DIR.exists():
            for f in QUEUE_DOWNLOADS_DIR.glob("*.*"):
                try:
                    if (now - f.stat().st_mtime) > 600:
                        size = cls.delete_file_safely(f)
                        if size > 0:
                            freed_bytes += size
                            deleted_files.append(f.name)
                except Exception:
                    pass

        mb_freed = round(freed_bytes / (1024 * 1024), 2)
        logger.info(f"✨ Storage Maintenance Complete: Freed {mb_freed} MB across {len(deleted_files)} files.")
        return {
            "success": True,
            "freed_mb": mb_freed,
            "deleted_count": len(deleted_files),
            "deleted_files": deleted_files[:20]
        }


storage_cleaner = StorageCleaner()
