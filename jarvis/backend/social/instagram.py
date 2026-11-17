"""Instagram Professional Account Manager & Reels Publisher.

Supports:
1. Browser-Assisted Workflow (Zero-API quota, direct session publishing, recommended)
2. Official Meta Graph API (Instagram Content Publishing API for Professional/Creator accounts)
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from jarvis.backend.config.settings import WORKSPACE_ROOT
from jarvis.backend.security.permissions import security_guard
from jarvis.backend.social.instagram_browser import instagram_browser

logger = logging.getLogger("JARVIS.Instagram")

INSTA_TOKEN_FILE = WORKSPACE_ROOT / "jarvis" / "instagram_token.json"


class InstagramManager:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.ig_user_id: Optional[str] = None
        self._load_cached_token()

    def _load_cached_token(self):
        if INSTA_TOKEN_FILE.exists():
            try:
                with open(INSTA_TOKEN_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    self.ig_user_id = data.get("ig_user_id")
            except Exception as e:
                logger.warning(f"Could not load Instagram credentials: {e}")

    async def get_auth_status(self) -> Dict[str, Any]:
        """Check connection state across both Browser Session and Meta Graph API."""
        browser_info = await instagram_browser.check_login_status()

        graph_configured = bool(self.access_token and self.ig_user_id)

        # Decide primary status
        is_connected = browser_info.get("logged_in") or graph_configured

        return {
            "connected": is_connected,
            "browser": browser_info,
            "graph": {
                "configured": graph_configured,
                "ig_user_id": self.ig_user_id
            },
            "active_method": "Browser Session (Zero Quota)" if browser_info.get("logged_in") else ("Meta Graph API" if graph_configured else "Disconnected"),
            "username": browser_info.get("username") or (f"ID: {self.ig_user_id}" if graph_configured else None)
        }

    def open_login_window(self) -> Dict[str, Any]:
        """Open Chrome for one-time Instagram sign-in."""
        return instagram_browser.open_login_window()

    def save_access_token(self, access_token: str, ig_user_id: str):
        """Store valid Meta Graph API user credentials."""
        self.access_token = access_token
        self.ig_user_id = ig_user_id
        with open(INSTA_TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump({"access_token": access_token, "ig_user_id": ig_user_id}, f)
        security_guard.log_event("INSTA_AUTH", "Saved Instagram Professional API token", "SUCCESS")

    async def publish_reel(
        self,
        video_path: str,
        caption: str,
        tags: Optional[List[str]] = None,
        method: str = "browser",
        headless: bool = False
    ) -> Dict[str, Any]:
        """Publish Reel using either Browser Automation or Meta Graph API."""
        if method == "browser" or not (self.access_token and self.ig_user_id):
            # Default to Browser Automation
            return await instagram_browser.upload_reel(
                video_path=video_path,
                caption=caption,
                tags=tags,
                headless=headless
            )

        # Meta Graph API fallback (requires public HTTPS video_url)
        return await self._publish_via_graph(video_url=video_path, caption=caption)

    async def _publish_via_graph(self, video_url: str, caption: str) -> Dict[str, Any]:
        """Publish Reel using Meta Content Publishing API."""
        if not self.access_token or not self.ig_user_id:
            raise PermissionError("Instagram account not connected. Please connect your Professional account.")

        if not security_guard.is_safe_to_proceed("instagram_publish", {"caption": caption[:50]}):
            raise PermissionError("Action blocked by safety gate or emergency stop.")

        async with httpx.AsyncClient(timeout=30.0) as client:
            container_url = f"https://graph.facebook.com/v19.0/{self.ig_user_id}/media"
            container_params = {
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": self.access_token
            }
            res = await client.post(container_url, data=container_params)
            res_data = res.json()

            if "id" not in res_data:
                raise RuntimeError(f"Failed to create Instagram Reel container: {res_data}")

            creation_id = res_data["id"]

            publish_url = f"https://graph.facebook.com/v19.0/{self.ig_user_id}/media_publish"
            publish_params = {
                "creation_id": creation_id,
                "access_token": self.access_token
            }
            pub_res = await client.post(publish_url, data=publish_params)
            pub_data = pub_res.json()

            security_guard.log_event("INSTA_PUBLISH", f"Published Reel: {caption[:40]}...", "SUCCESS")
            return {
                "success": True,
                "media_id": pub_data.get("id"),
                "creation_id": creation_id
            }


instagram_manager = InstagramManager()
