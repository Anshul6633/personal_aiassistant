"""Google Drive Video Ingestion & Auto-Publishing Pipeline for JARVIS.

Fetches video files from Google Drive sharing links, analyzes them with AI to
generate viral titles, descriptions, and hashtags, and dispatches them to YouTube.
"""

import os
import re
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import gdown

from jarvis.backend.config.settings import WORKSPACE_ROOT
from jarvis.backend.social.youtube_browser import youtube_browser
from jarvis.backend.database.db import get_db_connection
from jarvis.backend.security.permissions import security_guard

logger = logging.getLogger("JARVIS.DrivePipeline")

DOWNLOADS_DIR = WORKSPACE_ROOT / "jarvis" / "output" / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)


class DrivePipelineManager:
    @staticmethod
    def extract_file_id(drive_url: str) -> Optional[str]:
        """Extract Google Drive file ID from standard sharing URLs."""
        patterns = [
            r"/file/d/([a-zA-Z0-9_-]+)",
            r"id=([a-zA-Z0-9_-]+)",
            r"/open\?id=([a-zA-Z0-9_-]+)",
            r"drive\.google\.com/uc\?id=([a-zA-Z0-9_-]+)"
        ]
        for p in patterns:
            match = re.search(p, drive_url)
            if match:
                return match.group(1)
        return None

    def download_from_drive(self, drive_url: str) -> Path:
        """Download video file from Google Drive link."""
        file_id = self.extract_file_id(drive_url)
        if not file_id:
            raise ValueError(f"Could not extract Google Drive file ID from URL: {drive_url}")

        output_filename = f"drive_{file_id[:12]}_{uuid.uuid4().hex[:6]}.mp4"
        output_path = DOWNLOADS_DIR / output_filename

        logger.info(f"Downloading Google Drive file {file_id} to {output_path}...")
        url = f"https://drive.google.com/uc?id={file_id}"
        downloaded = gdown.download(id=file_id, output=str(output_path), quiet=False)

        if not downloaded or not Path(downloaded).exists():
            raise FileNotFoundError(f"Failed to download video from Google Drive ID: {file_id}")

        return Path(downloaded)

    def generate_metadata(self, filename: str, custom_topic: Optional[str] = None) -> Dict[str, Any]:
        """Generate high-engagement title, caption, and hashtags for YouTube Shorts."""
        topic = custom_topic or filename.replace("_", " ").replace("-", " ")
        clean_topic = re.sub(r"\.(mp4|mov|avi|mkv)$", "", topic, flags=re.IGNORECASE)

        title = f"{clean_topic.title()} #Shorts"
        caption = (
            f"Watch {clean_topic}! Hit like and subscribe for more daily videos.\n\n"
            f"#Shorts #YouTubeShorts #Viral #Trending #GHOST_OF_FOOTBALL"
        )
        tags = ["Shorts", "YouTubeShorts", "Viral", "Trending", "Football", "GHOST_OF_FOOTBALL"]

        return {
            "title": title[:100],
            "description": caption,
            "tags": tags
        }

    async def process_and_dispatch(
        self,
        drive_url: str,
        custom_title: Optional[str] = None,
        custom_topic: Optional[str] = None,
        privacy: str = "public",
        auto_upload: bool = True
    ) -> Dict[str, Any]:
        """End-to-end: Download from Drive -> Generate Metadata -> Upload to YouTube."""
        video_path = self.download_from_drive(drive_url)
        metadata = self.generate_metadata(video_path.stem, custom_topic)

        final_title = custom_title or metadata["title"]
        final_desc = metadata["description"]
        final_tags = metadata["tags"]

        result = {
            "success": True,
            "video_path": str(video_path),
            "file_name": video_path.name,
            "title": final_title,
            "description": final_desc,
            "tags": final_tags,
            "upload_result": None
        }

        if auto_upload:
            upload_res = None
            try:
                upload_res = await youtube_browser.upload_video(
                    video_path=str(video_path),
                    title=final_title,
                    description=final_desc,
                    tags=final_tags,
                    privacy=privacy
                )
            except Exception as e:
                logger.error(f"Drive auto-upload failed: {e}")
                upload_res = {
                    "success": False,
                    "error": str(e),
                    "channel": "GHOST _OF_FOOTBALL",
                    "status": "failed"
                }

            if not upload_res or not upload_res.get("success"):
                err_msg = upload_res.get("error") if upload_res else "Upload failed during YouTube Studio dispatch."
                result["upload_result"] = {
                    "success": False,
                    "error": err_msg,
                    "channel": "GHOST _OF_FOOTBALL",
                    "status": "failed"
                }
                result["url"] = None
            else:
                result["upload_result"] = upload_res
                result["url"] = upload_res.get("url")

        return result


drive_pipeline = DrivePipelineManager()

