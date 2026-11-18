"""Centralized, hardened yt-dlp options and extraction utilities for JARVIS.

Designed for robust execution across both local Windows workstations and
cloud container environments (such as Render, Docker, AWS) without bot-detection /
sign-in blocks.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional
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
    client_sequence: Optional[list] = None
) -> Dict[str, Any]:
    """Generate resilient yt-dlp options bypassing datacenter IP bot detection."""
    clients = client_sequence or ["tv_simply", "ios", "mweb", "default"]
    node_path = shutil.which("node")

    opts: Dict[str, Any] = {
        "quiet": quiet,
        "no_warnings": True,
        "skip_download": not download,
        "remote_components": ["ejs:github"],
        "http_headers": {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
        },
        "extractor_args": {
            "youtube": {
                "player_client": clients,
            }
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
        # Local Windows workstation: Chrome profile cookie support
        browser_profile = WORKSPACE_ROOT / "jarvis" / "browser_profile"
        if browser_profile.exists() and (browser_profile / "Default").exists():
            opts["cookiesfrombrowser"] = ("chrome", str(browser_profile.resolve()), None, None)

    return opts


def get_ytdlp_download_opts(
    out_template: str,
    ffmpeg_location: Optional[str] = None,
    client_sequence: Optional[list] = None
) -> Dict[str, Any]:
    """Generate options specifically for 1080p MP4 downloading."""
    opts = get_ytdlp_base_opts(download=True, quiet=True, client_sequence=client_sequence)
    opts.update({
        "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[ext=mp4]/best",
        "outtmpl": out_template,
        "merge_output_format": "mp4",
    })

    if ffmpeg_location and Path(ffmpeg_location).exists():
        opts["ffmpeg_location"] = str(ffmpeg_location)

    return opts


def safe_extract_info(
    url_or_query: str,
    download: bool = False,
    extra_opts: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Extract metadata or download with automatic fallback cascades if bot-challenged."""
    primary_opts = get_ytdlp_base_opts(download=download, quiet=True)
    if extra_opts:
        primary_opts.update(extra_opts)

    # Cascading client strategies in case of aggressive IP rate limits
    strategies = [
        ["tv_simply", "ios", "mweb", "default"],
        ["ios", "tv_simply", "mweb"],
        ["mweb", "ios"],
        ["default"]
    ]

    last_error = None
    for strategy in strategies:
        attempt_opts = dict(primary_opts)
        attempt_opts["extractor_args"] = {
            "youtube": {
                "player_client": strategy
            }
        }

        try:
            with yt_dlp.YoutubeDL(attempt_opts) as ydl:
                return ydl.extract_info(url_or_query, download=download)
        except Exception as e:
            last_error = e
            err_str = str(e).lower()

            # If it's a cookie sqlite lock issue on desktop, strip cookiesfrombrowser and retry immediately
            if ("cookie" in err_str or "sqlite" in err_str) and "cookiesfrombrowser" in attempt_opts:
                try:
                    attempt_opts.pop("cookiesfrombrowser", None)
                    with yt_dlp.YoutubeDL(attempt_opts) as ydl_nobrowser:
                        return ydl_nobrowser.extract_info(url_or_query, download=download)
                except Exception as ex2:
                    last_error = ex2

            logger.warning(f"yt-dlp strategy {strategy} encounter: {e}. Trying next client profile...")

    raise last_error or RuntimeError(f"Failed to extract info from {url_or_query}")
