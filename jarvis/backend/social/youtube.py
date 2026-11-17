"""YouTube Channel Manager & Shorts Publisher.

Uses official Google OAuth 2.0 and YouTube Data API v3.
Supports channel authorization, Shorts and video uploads, scheduling, and analytics tracking.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from jarvis.backend.config.settings import WORKSPACE_ROOT, settings
from jarvis.backend.database.db import get_db_connection
from jarvis.backend.security.permissions import security_guard

logger = logging.getLogger("JARVIS.YouTube")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

TOKEN_FILE = WORKSPACE_ROOT / "jarvis" / "youtube_token.json"
CLIENT_SECRETS_FILE = WORKSPACE_ROOT / "client_secret.json"


class YouTubeManager:
    def __init__(self):
        self.credentials: Optional[Credentials] = None
        self._load_cached_credentials()

    def _load_cached_credentials(self):
        if TOKEN_FILE.exists():
            try:
                self.credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            except Exception as e:
                logger.warning(f"Could not load cached YouTube credentials: {e}")

    def get_auth_status(self) -> Dict[str, Any]:
        """Check if YouTube is connected and return channel details if authorized."""
        if self.credentials and self.credentials.valid:
            try:
                youtube = build("youtube", "v3", credentials=self.credentials)
                res = youtube.channels().list(part="snippet,statistics", mine=True).execute()
                items = res.get("items", [])
                if items:
                    channel = items[0]
                    return {
                        "connected": True,
                        "channel_id": channel["id"],
                        "channel_title": channel["snippet"]["title"],
                        "subscribers": channel["statistics"].get("subscriberCount", "0"),
                        "video_count": channel["statistics"].get("videoCount", "0"),
                        "avatar_url": channel["snippet"]["thumbnails"]["default"]["url"]
                    }
            except Exception as e:
                logger.warning(f"Error checking YouTube channel info: {e}")

        client_secrets_exists = CLIENT_SECRETS_FILE.exists()
        return {
            "connected": False,
            "has_client_secrets": client_secrets_exists,
            "instructions": "Place your official Google Cloud OAuth client_secret.json in the project root to authenticate."
        }

    def initiate_oauth_flow(self, redirect_uri: str = "http://localhost:8000/api/auth/google/callback") -> str:
        """Generate Google OAuth authorization URL for user browser sign-in."""
        if not CLIENT_SECRETS_FILE.exists():
            raise FileNotFoundError(
                "client_secret.json not found in workspace root. "
                "Download your OAuth Client ID credentials from Google Cloud Console."
            )

        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
        flow.redirect_uri = redirect_uri
        auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
        return auth_url

    def complete_oauth_flow(self, auth_code: str, redirect_uri: str = "http://localhost:8000/api/auth/google/callback") -> bool:
        """Exchange authorization code for OAuth tokens and persist safely."""
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
        flow.redirect_uri = redirect_uri
        flow.fetch_token(code=auth_code)
        self.credentials = flow.credentials

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(self.credentials.to_json())

        security_guard.log_event("YOUTUBE_AUTH", "Successfully authorized YouTube channel via OAuth2", "SUCCESS")
        return True

    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        privacy_status: str = "private"
    ) -> Dict[str, Any]:
        """Upload a 9:16 vertical video as a YouTube Short via official YouTube Data API."""
        if not self.credentials or not self.credentials.valid:
            raise PermissionError("YouTube account is not authorized. Please connect via OAuth first.")

        if not security_guard.is_safe_to_proceed("youtube_upload", {"title": title, "path": video_path}):
            raise PermissionError("Action blocked by security permissions or emergency stop.")

        youtube = build("youtube", "v3", credentials=self.credentials)

        # Include #Shorts in title and description as required by YouTube algorithm
        if "#Shorts" not in title and "#shorts" not in title:
            title = f"{title} #Shorts"
        if "#Shorts" not in description:
            description = f"{description}\n\n#Shorts #YouTubeShorts #Trending"

        body = {
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": tags or ["Shorts", "Viral", "Reels"],
                "categoryId": "28"  # Science & Technology (or 24 for Entertainment)
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(video_path, chunksize=1024*1024*2, resumable=True, mimetype="video/mp4")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        logger.info(f"Starting upload of YouTube Short: {title}...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"YouTube Upload progress: {int(status.progress() * 100)}%")

        video_id = response.get("id")
        video_url = f"https://youtube.com/shorts/{video_id}"
        logger.info(f"Successfully uploaded YouTube Short: {video_url}")

        security_guard.log_event("YOUTUBE_UPLOAD", f"Uploaded Short: {title} ({video_url})", "SUCCESS")
        return {
            "video_id": video_id,
            "url": video_url,
            "title": title,
            "status": privacy_status
        }


youtube_manager = YouTubeManager()

