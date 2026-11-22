"""Instagram Web Browser Automation Uploader & Reels Manager.

Uploads Reels to Instagram via Playwright browser automation with persistent session.
Bypasses Meta Graph API token restrictions, business verification, and public URL requirements.
Uses a persistent user data profile (jarvis/browser_profile) so you only need to sign in once.
"""

import os
import sys
import asyncio
import sqlite3
import shutil
import tempfile
import json
import threading
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright, BrowserContext, Page
from jarvis.backend.config.settings import WORKSPACE_ROOT
from jarvis.backend.security.permissions import security_guard
from jarvis.backend.database.db import get_db_connection

logger = logging.getLogger("JARVIS.InstagramBrowser")

BROWSER_PROFILE_DIR = WORKSPACE_ROOT / "jarvis" / "browser_profile"
BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
INSTAGRAM_PROFILE_DIR = WORKSPACE_ROOT / "jarvis" / "browser_profile_instagram"
INSTAGRAM_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
INSTAGRAM_SESSION_PATH = WORKSPACE_ROOT / "jarvis" / "instagram_session.json"


class InstagramBrowserUploader:
    _instagram_lock = threading.Lock()

    def __init__(self):
        # Dedicated browser profile isolated from YouTube to prevent lock conflicts
        self.profile_dir = str(INSTAGRAM_PROFILE_DIR)

    async def check_login_status(self) -> Dict[str, Any]:
        """Fast check if the user is authenticated on Instagram.

        1. Inspects the Mobile Private API session settings directly.
        2. Falls back to inspecting the persistent SQLite cookie jar.
        """
        # 1. Check Mobile Private API active session
        if INSTAGRAM_SESSION_PATH.exists():
            try:
                with open(INSTAGRAM_SESSION_PATH, "r", encoding="utf-8") as f:
                    sess_data = json.load(f)
                auth_data = sess_data.get("authorization_data", {})
                user_id = auth_data.get("ds_user_id")
                if user_id:
                    return {
                        "logged_in": True,
                        "username": "clipperwithout",
                        "user_id": str(user_id),
                        "profile_dir": self.profile_dir,
                        "method": "Mobile Private API (Connected & Active)",
                        "message": "Authenticated as @clipperwithout (Native Reels API Ready)"
                    }
            except Exception as e:
                logger.debug(f"Instagram session JSON check error: {e}")

        # 2. Check primary instagram profile, fallback to shared browser_profile if synced
        profile_candidates = [Path(self.profile_dir), BROWSER_PROFILE_DIR]
        found_db = None
        for p in profile_candidates:
            cdb = p / "Default" / "Network" / "Cookies"
            if not cdb.exists():
                cdb = p / "Default" / "Cookies"
            if cdb.exists():
                found_db = cdb
                break

        if not found_db or not found_db.exists():
            return {
                "logged_in": False,
                "username": None,
                "profile_dir": self.profile_dir,
                "message": "No browser profile exists yet. Click 'Open Instagram Sign-In'."
            }

        tmp_db = tempfile.mktemp(suffix=".sqlite")
        logged_in = False
        username = None
        user_id = None

        try:
            shutil.copy2(found_db, tmp_db)
            conn = sqlite3.connect(tmp_db)
            cur = conn.cursor()
            cur.execute("SELECT name, value FROM cookies WHERE host_key LIKE '%instagram.com%'")
            rows = dict(cur.fetchall())
            conn.close()

            # Core Instagram authentication tokens
            has_session = bool(rows.get("sessionid"))
            user_id = rows.get("ds_user_id")
            logged_in = has_session and bool(user_id)

            # If logged in on secondary profile, copy to primary instagram profile
            if logged_in and found_db.parent.parent != Path(self.profile_dir):
                try:
                    dest_cookie_dir = Path(self.profile_dir) / "Default" / "Network"
                    dest_cookie_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(found_db, dest_cookie_dir / "Cookies")
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Instagram cookie check error: {e}")
        finally:
            try:
                Path(tmp_db).unlink(missing_ok=True)
            except Exception:
                pass

        # Try to extract username or last logged-in account from Chrome Preferences
        profile_path = Path(self.profile_dir)
        pref_file = profile_path / "Default" / "Preferences"
        if not pref_file.exists():
            pref_file = BROWSER_PROFILE_DIR / "Default" / "Preferences"
        if pref_file.exists():
            try:
                with open(pref_file, "r", encoding="utf-8", errors="ignore") as f:
                    pref = json.load(f)
                    autofill = pref.get("autofill", {}).get("profile_names", [])
                    if autofill and isinstance(autofill, list):
                        username = autofill[0]
            except Exception:
                pass

        if logged_in and not username:
            username = f"Instagram User ({user_id})" if user_id else "Authenticated Creator"

        return {
            "logged_in": logged_in,
            "username": username,
            "user_id": user_id,
            "profile_dir": self.profile_dir,
            "method": "Browser Session (Zero-API Quota, Anti-Ban Protected)"
        }

    def open_login_window(self) -> Dict[str, Any]:
        """Launch visible Chrome authentication window for Instagram."""
        logger.info("Opening Chrome authentication window for Instagram sign-in...")
        self._cleanup_profile_locks()

        try:
            cmd = f'start "" python -m jarvis.backend.social.instagram_login_helper'
            subprocess.Popen(cmd, shell=True)
            return {
                "success": True,
                "message": "Instagram login window opened! Please sign in or complete verification in the opened Chrome window. JARVIS will auto-detect your session."
            }
        except Exception as e:
            logger.error(f"Failed to open Instagram login window: {e}")
            return {"success": False, "error": str(e)}

    def bring_window_to_front(self):
        """Bring the Chrome browser window to the absolute front of the user desktop."""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            EnumWindows = ctypes.windll.user32.EnumWindows
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
            GetWindowTextW = ctypes.windll.user32.GetWindowTextW
            GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
            IsWindowVisible = ctypes.windll.user32.IsWindowVisible
            SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow
            ShowWindow = ctypes.windll.user32.ShowWindow

            def foreach_window(hwnd, lParam):
                if IsWindowVisible(hwnd):
                    length = GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        GetWindowTextW(hwnd, buff, length + 1)
                        title = buff.value.lower()
                        if "instagram" in title or "chrome" in title:
                            ShowWindow(hwnd, 9)  # SW_RESTORE
                            SetForegroundWindow(hwnd)
                            return False
                return True

            EnumWindows(EnumWindowsProc(foreach_window), 0)
        except Exception:
            pass

    def _cleanup_profile_locks(self):
        """Clean up orphaned lockfiles before launching Playwright."""
        profile_path = Path(self.profile_dir)
        for lock_name in ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket"]:
            try:
                (profile_path / lock_name).unlink(missing_ok=True)
            except Exception:
                pass

    def _run_in_proactor_loop(self, coro_fn, *args, **kwargs):
        with self._instagram_lock:
            if sys.platform == "win32":
                policy = asyncio.WindowsProactorEventLoopPolicy()
                loop = policy.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(coro_fn(*args, **kwargs))
                finally:
                    loop.close()
            else:
                return asyncio.run(coro_fn(*args, **kwargs))

    async def upload_reel(
        self,
        video_path: str,
        caption: str,
        tags: Optional[List[str]] = None,
        share_to_feed: bool = True,
        headless: bool = False,
        cover_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload an Instagram Reel prioritizing high-speed Native Mobile API, with Playwright browser fallback."""
        video_file = Path(video_path).resolve()
        if not video_file.exists():
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        # 1. Primary Engine: Native Mobile Private API (instagrapi)
        if INSTAGRAM_SESSION_PATH.exists():
            try:
                res = await self._upload_via_mobile_api(video_file, caption, tags, cover_path)
                if res.get("success"):
                    return res
            except Exception as e:
                logger.warning(f"Native Mobile API Reel upload failed ({e}); falling back to browser automation...")

        # 2. Fallback Engine: Dedicated Playwright browser session
        return await asyncio.to_thread(
            self._run_in_proactor_loop,
            self._upload_reel_impl,
            str(video_file),
            caption,
            tags,
            share_to_feed,
            headless
        )

    async def _upload_via_mobile_api(
        self,
        video_file: Path,
        caption: str,
        tags: Optional[List[str]] = None,
        cover_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload Reel using instagrapi Mobile Private API with zero browser lock contention."""
        def _sync_worker():
            from instagrapi import Client
            cl = Client()
            cl.delay_range = [1, 2]
            cl.load_settings(str(INSTAGRAM_SESSION_PATH))

            # Pre-Upload Shadowban & Spam Sanitization
            from jarvis.backend.social.anti_ban_guard import anti_ban_guard
            health = anti_ban_guard.check_instagram_shadowban_health()
            if not health.get("healthy", True):
                logger.warning(f"⚠️ Instagram Health Warning before upload: {health.get('reason')}")
            if health.get("shadowbanned"):
                logger.warning(f"🚨 Algorithmic Suppression Flag: {health.get('suppression_warning')}")

            # Assemble caption & clean hashtags using Anti-Ban Sanitizer
            full_caption = caption.strip()
            clean_tags = anti_ban_guard.sanitize_hashtags(tags or [])
            if clean_tags:
                full_caption += "\n\n" + " ".join(clean_tags)

            # Determine thumbnail
            thumb = None
            if cover_path and Path(cover_path).exists():
                thumb = Path(cover_path)
            else:
                v_stem = video_file.stem
                cand_thumb = WORKSPACE_ROOT / "jarvis" / "output" / "thumbnails" / f"{v_stem}_thumb.jpg"
                if cand_thumb.exists():
                    thumb = cand_thumb

            logger.info(f"Uploading Reel via Mobile Private API (@clipperwithout): {video_file.name}")
            try:
                media = cl.clip_upload(path=video_file, caption=full_caption, thumbnail=thumb)
            except Exception as up_err:
                # If session expired or challenge needed, attempt fast re-login
                if "login_required" in str(up_err).lower() or "challenge" in str(up_err).lower():
                    logger.info("Session expired; refreshing login credentials for @clipperwithout...")
                    cl.login("clipperwithout", "Akhatri@777")
                    cl.dump_settings(str(INSTAGRAM_SESSION_PATH))
                    media = cl.clip_upload(path=video_file, caption=full_caption, thumbnail=thumb)
                else:
                    raise up_err

            reel_url = f"https://www.instagram.com/reel/{media.code}/"
            logger.info(f"🎉 Instagram Reel successfully published! {reel_url}")

            # Anti-Shadowban Guard: Disable robotic instant self-commenting to protect account trust score
            # In 2026, instant API comments from the uploader account trigger Instagram spam classifiers
            logger.info("🛡️ [Anti-Shadowban] Bypassing immediate API self-comment to protect account trust score.")

            # Update Anti-Ban Guard
            try:
                from jarvis.backend.social.anti_ban_guard import anti_ban_guard
                anti_ban_guard.record_instagram_post(media.code)
            except Exception:
                pass

            # Record in SQLite database
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO instagram_schedule_queue (video_path, caption, hashtags, status, published_at, post_id, post_url) VALUES (?, ?, ?, 'PUBLISHED', CURRENT_TIMESTAMP, ?, ?)",
                    (str(video_file), caption, json.dumps(tags or []), str(media.pk), reel_url)
                )
                conn.commit()
                conn.close()
            except Exception as dbe:
                logger.debug(f"DB insert social post notice: {dbe}")

            return {
                "success": True,
                "url": reel_url,
                "code": media.code,
                "media_id": media.pk,
                "account": "clipperwithout",
                "engine": "Mobile Private API (Instant, No Captcha)",
                "message": f"Successfully published Reel to @clipperwithout: {reel_url}"
            }

        return await asyncio.to_thread(_sync_worker)

    async def _upload_reel_impl(
        self,
        video_path: str,
        caption: str,
        tags: Optional[List[str]] = None,
        share_to_feed: bool = True,
        headless: bool = False
    ) -> Dict[str, Any]:
        """Automate full upload workflow for an Instagram Reel using Playwright.

        Handles:
        1. Navigation to https://www.instagram.com/
        2. Detection of sign-in state
        3. Triggering the "+ Create" modal
        4. Ingesting vertical video file (9:16)
        5. Setting 9:16 aspect ratio so it isn't cropped square
        6. Stepping through Next -> Edit -> Next -> Details
        7. Typing caption and hashtags with human-like keystroke delays
        8. Clicking 'Share' and waiting for upload confirmation
        9. Capturing verification screenshot
        """
        video_file = Path(video_path).resolve()
        if not video_file.exists():
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        if not security_guard.is_safe_to_proceed("instagram_browser_upload", {"caption": caption[:60], "path": str(video_file)}):
            raise PermissionError("Upload blocked by security permissions or emergency stop.")

        # Clean hashtags
        clean_tags = []
        if tags:
            for t in tags:
                clean_t = t.strip().lstrip("#")
                if clean_t:
                    clean_tags.append(f"#{clean_t}")

        # Assemble full caption
        full_caption = caption.strip()
        if clean_tags:
            tag_str = " ".join(clean_tags)
            if tag_str not in full_caption:
                full_caption = f"{full_caption}\n\n{tag_str}"

        # Default viral reels hashtags if none provided
        if "#" not in full_caption:
            full_caption += "\n\n#reels #viral #explorepage #trending #creator"

        logger.info(f"Starting Instagram browser automation upload for: {video_file.name}")
        self._cleanup_profile_locks()

        async with async_playwright() as p:
            launch_kwargs = {
                "user_data_dir": self.profile_dir,
                "headless": headless,
                "viewport": {"width": 1280, "height": 850},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--start-maximized"
                ],
                "ignore_default_args": ["--enable-automation"]
            }

            try:
                context = await p.chromium.launch_persistent_context(**launch_kwargs, channel="chrome")
            except Exception:
                context = await p.chromium.launch_persistent_context(**launch_kwargs)

            page = context.pages[0] if context.pages else await context.new_page()
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

            try:
                # 1. Navigate to Instagram
                logger.info("Navigating to https://www.instagram.com/...")
                await page.goto("https://www.instagram.com/", timeout=60000, wait_until="domcontentloaded")
                await asyncio.sleep(3.0)

                # 2. Check if user is signed in
                if "login" in page.url or await page.locator("input[name='username']").first.is_visible():
                    logger.info("User is not signed in to Instagram. Prompting login...")
                    self.bring_window_to_front()

                    authenticated = False
                    for _ in range(120):  # Wait up to 240s for user to complete sign-in
                        await asyncio.sleep(2.0)
                        if "login" not in page.url and not (await page.locator("input[name='username']").first.is_visible()):
                            authenticated = True
                            logger.info("User completed Instagram sign-in!")
                            break

                    if not authenticated:
                        await context.close()
                        return {
                            "success": False,
                            "error": "Sign-in timed out. Please click 'Open Instagram Sign-In', log in once, and retry."
                        }

                # 3. Dismiss typical initial popups ('Save your login info', 'Turn on Notifications')
                for btn_text in ["Not Now", "Not now", "Save info", "Cancel"]:
                    try:
                        dismiss_btn = page.locator(f"button:has-text('{btn_text}')").first
                        if await dismiss_btn.is_visible(timeout=1500):
                            await dismiss_btn.click()
                            await asyncio.sleep(1.0)
                    except Exception:
                        pass

                # 4. Trigger '+ Create' modal
                logger.info("Locating 'Create' / 'New post' button...")
                create_selectors = [
                    "svg[aria-label='New post']",
                    "svg[aria-label='Create']",
                    "a[href='#']:has-text('Create')",
                    "span:has-text('Create')",
                    "div[role='button']:has(svg[aria-label='New post'])",
                    "div[role='button']:has(svg[aria-label='Create'])"
                ]

                create_clicked = False
                for sel in create_selectors:
                    try:
                        elem = page.locator(sel).first
                        if await elem.is_visible(timeout=2000):
                            await elem.click()
                            await asyncio.sleep(1.5)
                            create_clicked = True
                            break
                    except Exception:
                        continue

                # In case of sub-menu ('Post', 'Live video'), click 'Post'
                post_menu_item = page.locator("span:text-is('Post'), div[role='button']:has-text('Post')").first
                if await post_menu_item.is_visible(timeout=2000):
                    await post_menu_item.click()
                    await asyncio.sleep(1.5)

                # 5. Ingest video file via input[type='file']
                logger.info(f"Injecting video file into Instagram create modal: {video_file}...")
                file_input = page.locator("input[type='file']").first
                await file_input.wait_for(state="attached", timeout=25000)
                await file_input.set_input_files(str(video_file))
                await asyncio.sleep(3.5)

                # Dismiss 'Video posts are now shared as reels' info banner if present
                ok_btn = page.locator("button:has-text('OK'), button:has-text('Continue')").first
                if await ok_btn.is_visible(timeout=2500):
                    await ok_btn.click()
                    await asyncio.sleep(1.0)

                # 6. Aspect Ratio Selection (Set 9:16 vertical Reel crop)
                logger.info("Setting vertical 9:16 aspect ratio...")
                try:
                    crop_btn = page.locator("button:has(svg[aria-label='Select crop']), svg[aria-label='Select crop']").first
                    if await crop_btn.is_visible(timeout=3000):
                        await crop_btn.click()
                        await asyncio.sleep(1.0)
                        # Select 9:16 or Original
                        ratio_916 = page.locator("button:has-text('9:16'), div[role='button']:has-text('9:16')").first
                        if await ratio_916.is_visible(timeout=2000):
                            await ratio_916.click()
                            await asyncio.sleep(1.0)
                except Exception as e:
                    logger.debug(f"Crop adjustment skipped or auto-detected: {e}")

                # 7. Click 'Next' to move to Filter / Cover Edit step
                logger.info("Navigating to editing step...")
                next_btn = page.locator("div[role='dialog'] div[role='button']:has-text('Next'), button:has-text('Next')").first
                await next_btn.wait_for(timeout=20000)
                await next_btn.click()
                await asyncio.sleep(2.0)

                # 8. Click 'Next' to move to Caption & Details step
                logger.info("Navigating to caption & details step...")
                next_btn_2 = page.locator("div[role='dialog'] div[role='button']:has-text('Next'), button:has-text('Next')").first
                if await next_btn_2.is_visible(timeout=10000):
                    await next_btn_2.click()
                    await asyncio.sleep(2.0)

                # 9. Type Caption and Hashtags with human-like cadence
                logger.info("Writing caption and hashtags...")
                caption_box = page.locator("div[role='dialog'] div[aria-label*='caption' i], div[role='dialog'] div[role='textbox'], div[role='dialog'] div[contenteditable='true']").first
                await caption_box.wait_for(timeout=20000)
                await caption_box.click()
                await asyncio.sleep(0.5)

                # Human-like typing delay
                await caption_box.type(full_caption[:2200], delay=25)
                await asyncio.sleep(1.5)

                # 10. Click 'Share' button
                logger.info("Publishing Reel! Clicking 'Share'...")
                share_btn = page.locator("div[role='dialog'] div[role='button']:has-text('Share'), button:has-text('Share')").first
                await share_btn.wait_for(timeout=15000)
                await share_btn.click()
                await asyncio.sleep(3.0)

                # 11. Wait for post completion confirmation
                logger.info("Waiting for Instagram to finish uploading and processing Reel...")
                success = False
                shared_indicators = [
                    "*:has-text('Your reel has been shared')",
                    "*:has-text('Your post has been shared')",
                    "img[alt='Animated checkmark']",
                    "span:has-text('Your reel has been shared')",
                    "span:has-text('Your post has been shared')"
                ]

                # Wait up to 180 seconds for upload & transcode to complete
                for step in range(90):
                    await asyncio.sleep(2.0)
                    for ind in shared_indicators:
                        if await page.locator(ind).first.is_visible():
                            success = True
                            break
                    if success:
                        break

                    # Also check if modal closed and we are back to feed
                    if not (await page.locator("div[role='dialog']").first.is_visible()):
                        success = True
                        break

                # 12. Save verification screenshot
                screenshot_path = WORKSPACE_ROOT / "jarvis" / "output" / "exports" / f"instagram_upload_{int(asyncio.get_event_loop().time())}.png"
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    await page.screenshot(path=str(screenshot_path))
                except Exception:
                    pass

                await context.close()

                if success:
                    logger.info("🎉 SUCCESS! Reel has been published to Instagram!")
                    try:
                        from jarvis.backend.social.anti_ban_guard import anti_ban_guard
                        anti_ban_guard.record_instagram_post(True)
                    except Exception:
                        pass
                    # Update database audit logs
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO audit_logs (action_type, details, status, user_approved) VALUES (?, ?, ?, ?)",
                        ("INSTAGRAM_REEL_PUBLISH", f"Published Reel: {full_caption[:50]}...", "SUCCESS", 1)
                    )
                    conn.commit()
                    conn.close()

                    return {
                        "success": True,
                        "message": "Reel published successfully to Instagram Profile!",
                        "screenshot": str(screenshot_path),
                        "caption": full_caption[:100]
                    }
                else:
                    return {
                        "success": False,
                        "error": "Upload may still be processing in the background, or Instagram took longer than 3 minutes to encode."
                    }

            except Exception as e:
                logger.error(f"Instagram automation error: {e}", exc_info=True)
                err_str = str(e).lower()
                if "try again later" in err_str or "action blocked" in err_str or "we limit how often" in err_str:
                    try:
                        from jarvis.backend.social.anti_ban_guard import anti_ban_guard
                        anti_ban_guard.record_action_block(cooldown_hours=2.0)
                    except Exception:
                        pass
                # Try saving error screenshot
                err_shot = WORKSPACE_ROOT / "jarvis" / "output" / "exports" / "instagram_error.png"
                try:
                    await page.screenshot(path=str(err_shot))
                except Exception:
                    pass
                await context.close()
                return {
                    "success": False,
                    "error": str(e),
                    "error_screenshot": str(err_shot) if err_shot.exists() else None
                }


instagram_browser = InstagramBrowserUploader()

