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


class InstagramBrowserUploader:
    def __init__(self):
        self.profile_dir = str(BROWSER_PROFILE_DIR)

    async def check_login_status(self) -> Dict[str, Any]:
        """Fast, non-blocking check if the user is authenticated on Instagram.

        Inspects the persistent SQLite cookie jar directly in under 10ms
        without launching a browser process or locking files.
        """
        profile_path = Path(self.profile_dir)
        cookies_db = profile_path / "Default" / "Network" / "Cookies"
        if not cookies_db.exists():
            cookies_db = profile_path / "Default" / "Cookies"

        if not cookies_db.exists():
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
            shutil.copy2(cookies_db, tmp_db)
            conn = sqlite3.connect(tmp_db)
            cur = conn.cursor()
            cur.execute("SELECT name, value FROM cookies WHERE host_key LIKE '%instagram.com%'")
            rows = dict(cur.fetchall())
            conn.close()

            # Core Instagram authentication tokens
            has_session = bool(rows.get("sessionid"))
            user_id = rows.get("ds_user_id")
            logged_in = has_session and bool(user_id)
        except Exception as e:
            logger.debug(f"Instagram cookie check error: {e}")
        finally:
            try:
                Path(tmp_db).unlink(missing_ok=True)
            except Exception:
                pass

        # Try to extract username or last logged-in account from Chrome Preferences
        pref_file = profile_path / "Default" / "Preferences"
        if pref_file.exists():
            try:
                with open(pref_file, "r", encoding="utf-8", errors="ignore") as f:
                    pref = json.load(f)
                    # Check autofill or signin data
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
            "method": "Browser Session (Zero-API Quota)"
        }

    def open_login_window(self) -> Dict[str, Any]:
        """Launch native Google Chrome for one-time Instagram sign-in without any bot detection."""
        logger.info("Opening native Google Chrome for Instagram sign-in...")
        self._cleanup_profile_locks()

        chrome_paths = [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path(os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")),
        ]
        chrome_exe = None
        for p in chrome_paths:
            if p.exists():
                chrome_exe = p
                break

        try:
            if chrome_exe:
                cmd = f'start "" "{chrome_exe}" --user-data-dir="{self.profile_dir}" "https://www.instagram.com"'
                subprocess.Popen(cmd, shell=True)
                return {
                    "success": True,
                    "message": "Native Google Chrome opened! Sign in to Instagram directly in the browser window."
                }
            else:
                # Fallback to Playwright-launched Chromium
                cmd = f'start "" python -m jarvis.backend.social.login_helper'
                subprocess.Popen(cmd, shell=True)
                return {
                    "success": True,
                    "message": "Login window launched! Sign in to Instagram in the opened browser window."
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
        headless: bool = False
    ) -> Dict[str, Any]:
        """Automate full upload workflow for an Instagram Reel in a dedicated Proactor loop thread."""
        return await asyncio.to_thread(
            self._run_in_proactor_loop,
            self._upload_reel_impl,
            video_path,
            caption,
            tags,
            share_to_feed,
            headless
        )

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

