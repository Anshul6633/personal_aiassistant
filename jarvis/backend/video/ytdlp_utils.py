"""Centralized, hardened yt-dlp options and extraction utilities for JARVIS.

Designed for robust execution across both local Windows workstations and
cloud container environments (such as Render, Docker, AWS) without bot-detection /
sign-in blocks.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import yt_dlp

from jarvis.backend.config.settings import WORKSPACE_ROOT

logger = logging.getLogger("JARVIS.Video.YtDlpUtils")

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def get_cookie_file() -> Optional[Path]:
    """Locate or materialize YouTube cookies in Netscape format."""
    # 1. Environment variable with raw Netscape cookie content
    raw_cookies = os.getenv("YOUTUBE_COOKIES_TEXT") or os.getenv("YOUTUBE_COOKIES_DATA")
    if raw_cookies and len(raw_cookies.strip()) > 10:
        target_dir = WORKSPACE_ROOT / "jarvis" / "browser_profile"
        target_dir.mkdir(parents=True, exist_ok=True)
        cookie_path = target_dir / "cookies.txt"
        try:
            cookie_path.write_text(raw_cookies.strip(), encoding="utf-8")
            logger.info(f"Loaded YouTube cookies from environment variable into {cookie_path}")
            return cookie_path
        except Exception as e:
            logger.warning(f"Failed to persist env cookies: {e}")

    # 2. Environment variable pointing directly to a cookie file
    env_file = os.getenv("YOUTUBE_COOKIES_FILE")
    if env_file:
        p = Path(env_file)
        if p.exists() and p.stat().st_size > 10:
            return p

    # 3. Known project locations
    candidates = [
        WORKSPACE_ROOT / "jarvis" / "browser_profile" / "cookies.txt",
        WORKSPACE_ROOT / "cookies.txt",
        WORKSPACE_ROOT / "jarvis" / "cookies.txt",
        Path("/app/jarvis/browser_profile/cookies.txt"),
    ]

    for cand in candidates:
        if cand.exists() and cand.is_file() and cand.stat().st_size > 10:
            return cand

    return None


def save_cookies_text(cookies_text: str) -> Path:
    """Save user-supplied Netscape cookies to browser_profile/cookies.txt."""
    target_dir = WORKSPACE_ROOT / "jarvis" / "browser_profile"
    target_dir.mkdir(parents=True, exist_ok=True)
    cookie_path = target_dir / "cookies.txt"
    cookie_path.write_text(cookies_text.strip(), encoding="utf-8")
    logger.info(f"Saved {len(cookies_text)} bytes of YouTube cookies to {cookie_path}")
    return cookie_path


def get_ytdlp_base_opts(
    download: bool = False,
    quiet: bool = True,
    client_sequence: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Generate clean, hardened yt-dlp options with Node.js runtime and cookie support."""
    node_path = shutil.which("node")

    opts: Dict[str, Any] = {
        "quiet": quiet,
        "no_warnings": True,
        "skip_download": not download,
        "remote_components": ["ejs:github"],
        "http_headers": {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        }
    }

    if client_sequence:
        opts["extractor_args"] = {
            "youtube": {
                "player_client": client_sequence
            }
        }

    if node_path:
        opts["js_runtimes"] = {"node": {"path": node_path}}

    # Check for authenticated cookies file
    cookie_file = get_cookie_file()
    if cookie_file:
        opts["cookiefile"] = str(cookie_file.resolve())
        logger.debug(f"yt-dlp using cookie file: {cookie_file}")
    elif not os.getenv("HEADLESS") and os.name == "nt":
        browser_profile = WORKSPACE_ROOT / "jarvis" / "browser_profile"
        cookies_db = browser_profile / "Default" / "Network" / "Cookies"
        if not cookies_db.exists():
            cookies_db = browser_profile / "Default" / "Cookies"
        if cookies_db.exists():
            try:
                # Test if SQLite file is unlocked before letting yt-dlp copy it
                with open(cookies_db, "rb") as f:
                    pass
                opts["cookiesfrombrowser"] = ("chrome", str(browser_profile.resolve()), None, None)
            except Exception:
                # Chrome process currently holding lock, skip to avoid stderr noise
                pass

    return opts


def get_ytdlp_download_opts(
    out_template: str,
    ffmpeg_location: Optional[str] = None,
    client_sequence: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Generate options specifically for 1080p/720p/best MP4 downloading."""
    opts = get_ytdlp_base_opts(download=True, quiet=True, client_sequence=client_sequence)
    is_cloud = bool(os.getenv("HEADLESS") or os.getenv("RENDER") or os.getenv("RAILWAY_STATIC_URL"))
    if is_cloud:
        # On cloud (Render free tier), prioritize fast download & compact footprint to prevent OOM
        format_str = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=480][ext=mp4]/best[ext=mp4]/best"
    else:
        format_str = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[ext=mp4]/best"

    opts.update({
        "format": format_str,
        "outtmpl": out_template,
        "merge_output_format": "mp4",
        "socket_timeout": 30,
        "retries": 3,
    })

    if ffmpeg_location and Path(ffmpeg_location).exists():
        opts["ffmpeg_location"] = str(ffmpeg_location)

    return opts


def fetch_oembed_metadata(url: str) -> Dict[str, Any]:
    """Lightweight, resilient fallback that never triggers bot challenges on datacenter IPs."""
    import urllib.request
    import json
    import re

    vid_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    vid_id = vid_match.group(1) if vid_match else "unknown"
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid_id}&format=json"

    data = {}
    try:
        req = urllib.request.Request(oembed_url, headers={"User-Agent": DEFAULT_USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        logger.warning(f"oEmbed fetch error for {vid_id}: {e}")

    duration = 0
    try:
        h_req = urllib.request.Request(
            f"https://www.youtube.com/watch?v={vid_id}",
            headers={"User-Agent": DEFAULT_USER_AGENT}
        )
        with urllib.request.urlopen(h_req, timeout=8) as h_resp:
            html = h_resp.read().decode("utf-8", errors="ignore")
            dur_match = re.search(r'"approxDurationMs":"([0-9]+)"', html)
            if dur_match:
                duration = int(dur_match.group(1)) // 1000
    except Exception:
        pass

    return {
        "id": vid_id,
        "title": data.get("title", "YouTube Video"),
        "duration": duration,
        "uploader": data.get("author_name", "YouTube Creator"),
        "view_count": 0,
        "thumbnail": data.get("thumbnail_url", f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"),
        "description": f"Video by {data.get('author_name', 'YouTube Creator')}"
    }


def safe_extract_info(
    url_or_query: str,
    download: bool = False,
    extra_opts: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Extract metadata or download with automatic fallback cascades if bot-challenged."""
    base_opts = get_ytdlp_base_opts(download=download, quiet=True)
    if extra_opts:
        base_opts.update(extra_opts)

    try:
        with yt_dlp.YoutubeDL(base_opts) as ydl:
            return ydl.extract_info(url_or_query, download=download)
    except Exception as e:
        err_str = str(e).lower()
        logger.warning(f"Standard yt-dlp extraction note: {e}")

        # If locked by browser sqlite, strip cookiesfrombrowser and retry
        if ("cookie" in err_str or "sqlite" in err_str) and "cookiesfrombrowser" in base_opts:
            try:
                nobrowser_opts = dict(base_opts)
                nobrowser_opts.pop("cookiesfrombrowser", None)
                with yt_dlp.YoutubeDL(nobrowser_opts) as ydl_nb:
                    return ydl_nb.extract_info(url_or_query, download=download)
            except Exception as ex2:
                logger.warning(f"Fallback without browser cookies: {ex2}")

        # If bot challenge or player error on cloud IP, retry with mobile/tv clients
        fallback_clients = [
            ["tv_simply", "ios", "mweb"],
            ["ios", "android"]
        ]
        for clients in fallback_clients:
            try:
                attempt_opts = dict(base_opts)
                attempt_opts["extractor_args"] = {"youtube": {"player_client": clients}}
                attempt_opts.pop("cookiesfrombrowser", None)
                with yt_dlp.YoutubeDL(attempt_opts) as ydl_fb:
                    return ydl_fb.extract_info(url_or_query, download=download)
            except Exception as fb_err:
                logger.warning(f"Fallback client {clients} error: {fb_err}")

        # If all fail and not downloading, use oEmbed fallback
        if not download and "http" in url_or_query:
            logger.info("Engaging zero-fail oEmbed fallback engine...")
            return fetch_oembed_metadata(url_or_query)

        raise e
