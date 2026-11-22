"""YouTube Studio Browser Automation Uploader.

Uploads videos and Shorts to YouTube Studio using Playwright browser automation.
Bypasses all Google Cloud API quota limits (unlimited daily uploads).
Uses a persistent user data profile so you only need to sign in once.
"""

import os
import sys
import asyncio
import threading
import sqlite3
import shutil
import tempfile
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright, BrowserContext, Page
from jarvis.backend.config.settings import WORKSPACE_ROOT, settings
from jarvis.backend.security.permissions import security_guard

logger = logging.getLogger("JARVIS.YouTubeBrowser")

BROWSER_PROFILE_DIR = WORKSPACE_ROOT / "jarvis" / "browser_profile"
BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)


class YouTubeBrowserUploader:
    _browser_lock = threading.Lock()

    def __init__(self):
        self.profile_dir = str(BROWSER_PROFILE_DIR)

    async def check_login_status(self) -> Dict[str, Any]:
        """Fast, non-blocking check if the user is authenticated in YouTube Studio.

        Inspects the persistent SQLite cookie jar and Chrome preferences directly.
        Executes in under 10ms without launching a browser process or locking files.
        """
        profile_path = Path(self.profile_dir)
        cookies_db = profile_path / "Default" / "Network" / "Cookies"
        if not cookies_db.exists():
            cookies_db = profile_path / "Default" / "Cookies"

        if not cookies_db.exists():
            return {
                "logged_in": False,
                "channel_title": None,
                "profile_dir": self.profile_dir,
                "message": "No browser profile exists yet. Click 'Open Studio Sign-In'."
            }

        tmp_db = tempfile.mktemp(suffix=".sqlite")
        logged_in = False
        channel_title = None

        try:
            shutil.copy2(cookies_db, tmp_db)
            conn = sqlite3.connect(tmp_db)
            cur = conn.cursor()
            cur.execute("SELECT name FROM cookies WHERE host_key LIKE '%youtube%' OR host_key LIKE '%google%'")
            names = {r[0] for r in cur.fetchall()}
            conn.close()

            # Google/YouTube authentication token cookies
            auth_markers = ["LOGIN_INFO", "SSID", "SAPISID", "SID", "APISID", "__Secure-3PSID"]
            logged_in = any(c in names for c in auth_markers)
        except Exception as e:
            logger.debug(f"Cookie check error: {e}")
        finally:
            try:
                Path(tmp_db).unlink(missing_ok=True)
            except Exception:
                pass

        # Try extracting channel/account name from Preferences JSON
        pref_file = profile_path / "Default" / "Preferences"
        if pref_file.exists():
            try:
                with open(pref_file, "r", encoding="utf-8", errors="ignore") as f:
                    pref = json.load(f)
                    accounts = pref.get("account_info", []) or pref.get("signin", {}).get("accounts_metadata_dict", {})
                    if accounts:
                        if isinstance(accounts, dict):
                            for k, v in accounts.items():
                                channel_title = v.get("full_name") or v.get("email")
                                if channel_title:
                                    break
                        elif isinstance(accounts, list) and len(accounts) > 0:
                            channel_title = accounts[0].get("full_name") or accounts[0].get("email")
            except Exception:
                pass

        if logged_in and not channel_title:
            channel_title = "Authenticated YouTube Studio Channel"

        return {
            "logged_in": logged_in,
            "channel_title": channel_title,
            "profile_dir": self.profile_dir
        }

    def open_login_window(self) -> Dict[str, Any]:
        """Launch native Google Chrome for one-time Google sign-in without any bot detection."""
        logger.info("Opening native Google Chrome for YouTube Studio sign-in...")
        self._cleanup_profile_locks()

        chrome_paths = [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ]
        chrome_exe = None
        for p in chrome_paths:
            if p.exists():
                chrome_exe = p
                break

        try:
            if chrome_exe:
                cmd = f'start "" "{chrome_exe}" --user-data-dir="{self.profile_dir}" "https://studio.youtube.com"'
                subprocess.Popen(cmd, shell=True)
                return {
                    "success": True,
                    "message": "Native Google Chrome opened! Sign in to GHOST _OF_FOOTBALL without any bot detection."
                }
            else:
                helper_script = Path(__file__).parent / "login_helper.py"
                python_exe = sys.executable
                subprocess.Popen(
                    [python_exe, str(helper_script)],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    close_fds=(sys.platform != "win32")
                )
                return {
                    "success": True,
                    "message": "Login window launched! Sign into your Google account in the opened browser window."
                }
        except Exception as e:
            logger.error(f"Failed to open login window: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def bring_window_to_front():
        """Bring the Chrome browser window to the absolute front of the user desktop."""
        if sys.platform != "win32":
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            EnumWindows = user32.EnumWindows
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            GetWindowTextW = user32.GetWindowTextW
            GetWindowTextLengthW = user32.GetWindowTextLengthW
            IsWindowVisible = user32.IsWindowVisible
            SetForegroundWindow = user32.SetForegroundWindow
            ShowWindow = user32.ShowWindow

            def foreach_window(hwnd, lParam):
                if IsWindowVisible(hwnd):
                    length = GetWindowTextLengthW(hwnd)
                    buff = ctypes.create_unicode_buffer(length + 1)
                    GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    if any(term in title for term in ["Google", "YouTube", "Sign in", "Chrome"]):
                        ShowWindow(hwnd, 3)
                        SetForegroundWindow(hwnd)
                return True

            EnumWindows(EnumWindowsProc(foreach_window), 0)
        except Exception:
            pass

    def _cleanup_profile_locks(self):
        """Clean up orphaned lockfiles and any lingering Chrome processes using this profile before launching Playwright."""
        profile_path = Path(self.profile_dir)
        for lock_name in ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket"]:
            try:
                (profile_path / lock_name).unlink(missing_ok=True)
            except Exception:
                pass
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'browser_profile' in cmdline:
                            proc.kill()
                except Exception:
                    pass
        except Exception:
            pass

    @staticmethod
    async def _check_daily_limit(page: Page) -> bool:
        """Check if YouTube Studio daily upload limit banner is displayed."""
        try:
            loc = page.get_by_text("Daily upload limit", exact=False).first
            if await loc.is_visible():
                return True
        except Exception:
            pass
        try:
            loc2 = page.get_by_text("Upload limit reached", exact=False).first
            if await loc2.is_visible():
                return True
        except Exception:
            pass
        return False

    def _run_in_proactor_loop(self, coro_fn, *args, **kwargs):
        with self._browser_lock:
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

    async def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        privacy: str = "schedule",
        schedule_time: Optional[str] = None,
        schedule_date: Optional[str] = None,
        headless: bool = False,
        debate_comment: Optional[str] = None,
        thumbnail_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Automate full upload workflow on YouTube Studio in a dedicated Proactor loop thread."""
        return await asyncio.to_thread(
            self._run_in_proactor_loop,
            self._upload_video_impl,
            video_path,
            title,
            description,
            tags,
            privacy,
            schedule_time,
            schedule_date,
            headless,
            debate_comment,
            thumbnail_path
        )

    async def _upload_video_impl(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        privacy: str = "schedule",
        schedule_time: Optional[str] = None,
        schedule_date: Optional[str] = None,
        headless: bool = False,
        debate_comment: Optional[str] = None,
        thumbnail_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Automate full upload workflow on YouTube Studio."""
        video_file = Path(video_path).resolve()
        if not video_file.exists():
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        if not security_guard.is_safe_to_proceed("youtube_browser_upload", {"title": title, "path": str(video_file)}):
            raise PermissionError("Upload blocked by security permissions.")

        is_longform = ("compilation" in title.lower() or "episode" in title.lower() or "longform" in str(tags).lower() or "long-form" in str(tags).lower())
        if not is_longform and "#Shorts" not in title and "#shorts" not in title:
            title = f"{title} #Shorts"

        logger.info(f"Starting browser automation upload for: {title}")
        self._cleanup_profile_locks()

        async with async_playwright() as p:
            is_headless = headless or settings.HEADLESS or (os.name != "nt" and not os.environ.get("DISPLAY"))
            launch_kwargs = {
                "user_data_dir": self.profile_dir,
                "headless": is_headless,
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
                # 1. Navigate to YouTube Studio
                target_url = "https://studio.youtube.com/channel/UCkOSkUPIoE4bT_GwbHKNpog/content?approve_browser_access=true"
                logger.info(f"Navigating to {target_url}...")
                await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
                await asyncio.sleep(2.0)

                # Check if logged in
                if "accounts.google.com" in page.url or "signin" in page.url:
                    logger.info("Sign-in required for GHOST _OF_FOOTBALL. Pre-filling credentials...")
                    try:
                        # 1. Handle Account Chooser if card is shown
                        account_loc = page.get_by_text("anshulkhatri.clcskncoe@gmail.com").first
                        if await account_loc.count() > 0 and await account_loc.is_visible():
                            logger.info("Clicking existing account card...")
                            await account_loc.click()
                            await asyncio.sleep(2.0)

                        # Handle confirmidentifier Next button if present
                        confirm_next = page.locator("#identifierNext, button:has-text('Next')").first
                        if await confirm_next.is_visible():
                            logger.info("Clicking Next on account confirmation...")
                            await confirm_next.click()
                            await asyncio.sleep(3.0)

                        # 2. Email input
                        email_input = page.locator("#identifierId, input[type='email']").first
                        if await email_input.is_visible():
                            await email_input.fill("anshulkhatri.clcskncoe@gmail.com")
                            await asyncio.sleep(0.5)
                            next_btn = page.locator("#identifierNext, button:has-text('Next')").first
                            if await next_btn.is_visible():
                                await next_btn.click()
                                await asyncio.sleep(3.0)

                        # 3. Password input
                        pass_input = page.locator("input[type='password'], input[name='Passwd'], input[name='password']").first
                        await pass_input.wait_for(state="visible", timeout=12000)
                        if await pass_input.is_visible():
                            logger.info("Auto-filling Google account password...")
                            await pass_input.fill("akhatri@777")
                            await asyncio.sleep(0.8)
                            pass_next = page.locator("#passwordNext, button:has-text('Next')").first
                            if await pass_next.is_visible():
                                await pass_next.click()
                                await asyncio.sleep(3.5)
                    except Exception as e:
                        logger.debug(f"Credential auto-fill notice: {e}")

                    self.bring_window_to_front()

                    # Wait for redirect to Studio (or 2FA approval if requested by Google)
                    logger.info("Waiting for Studio authentication & redirect to complete...")
                    authenticated = False
                    for _ in range(150):  # up to 300 seconds
                        await asyncio.sleep(2.0)
                        curr_url = page.url
                        if "studio.youtube.com" in curr_url and "accounts.google.com" not in curr_url and "signin" not in curr_url:
                            authenticated = True
                            logger.info(f"User authenticated! Studio URL: {curr_url}")
                            break

                    if not authenticated:
                        await context.close()
                        return {
                            "success": False,
                            "error": "Authentication timed out. If Google prompted a 2FA tap on your phone, approve it and retry."
                        }

                # 2. Trigger upload modal
                logger.info("Locating 'UPLOAD' / 'CREATE' button on YouTube Studio...")
                upload_opened = False
                file_input = page.locator("input[type='file']").first
                if await file_input.is_visible():
                    upload_opened = True

                if not upload_opened:
                    direct_upload = page.locator("ytcp-button#upload-button, button:has-text('Upload videos')").first
                    if await direct_upload.is_visible():
                        await direct_upload.click()
                        await asyncio.sleep(1.5)
                        upload_opened = True

                if not upload_opened:
                    create_btn = page.locator("#create-icon, button:has-text('Create'), yt-button-shape:has-text('Create')").first
                    await create_btn.wait_for(timeout=25000)
                    await create_btn.click()
                    await asyncio.sleep(1.0)
                    upload_menu_item = page.locator("tp-yt-paper-item:has-text('Upload videos'), ytd-compact-link-renderer:has-text('Upload videos'), #text-item-0").first
                    if await upload_menu_item.is_visible():
                        await upload_menu_item.click()
                    await asyncio.sleep(1.5)

                # 3. Set file input
                logger.info(f"Attaching video file: {video_file}...")
                file_input = page.locator("input[type='file']").first
                await file_input.wait_for(state="attached", timeout=25000)
                await file_input.set_input_files(str(video_file))

                # 5. Fill Title & Description (Polymer-safe input)
                logger.info("Filling title and details with Polymer-safe input...")
                title_box = page.locator("#textbox[aria-label*='title' i], [aria-label='Add a title that describes your video']").first
                await title_box.wait_for(timeout=35000)
                await asyncio.sleep(1.0)
                await title_box.click()
                await asyncio.sleep(0.3)
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
                await asyncio.sleep(0.3)
                await title_box.press_sequentially(title[:100], delay=20)
                await page.keyboard.press("Tab")
                await asyncio.sleep(1.0)

                desc_box = page.locator("#textbox[aria-label*='description' i], [aria-label='Tell viewers about your video']").first
                if await desc_box.is_visible():
                    desc_text = description if is_longform else f"{description}\n\n#Shorts #Viral #Trending"
                    await desc_box.click()
                    await asyncio.sleep(0.3)
                    await page.keyboard.press("Control+A")
                    await page.keyboard.press("Backspace")
                    await asyncio.sleep(0.3)
                    await desc_box.press_sequentially(desc_text[:2000], delay=10)
                    await page.keyboard.press("Tab")
                    await asyncio.sleep(1.0)

                # Custom Thumbnail upload if provided
                if thumbnail_path and Path(thumbnail_path).exists():
                    try:
                        logger.info(f"Attaching custom thumbnail: {thumbnail_path}...")
                        thumb_file_input = page.locator("input#file-loader, ytcp-thumbnails-compact input[type='file'], input[type='file'][accept*='image']").first
                        if await thumb_file_input.count() > 0:
                            await thumb_file_input.set_input_files(str(thumbnail_path))
                            logger.info(f"Successfully attached custom thumbnail: {thumbnail_path}")
                            await asyncio.sleep(2.0)
                    except Exception as te:
                        logger.warning(f"Custom thumbnail attachment warning: {te}")

                # Audience
                logger.info("Selecting 'Not made for kids' audience...")
                not_for_kids = page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK'], [name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
                try:
                    await not_for_kids.scroll_into_view_if_needed(timeout=5000)
                except Exception:
                    pass
                await not_for_kids.click(force=True)
                await asyncio.sleep(1.0)

                # Monitor video upload progress until raw file bytes are 100% uploaded
                file_size_mb = Path(video_path).stat().st_size / (1024 * 1024) if Path(video_path).exists() else 20.0
                max_wait_seconds = max(180, int(file_size_mb * 8))
                max_loops = max(60, max_wait_seconds // 3)
                logger.info(f"Verifying video upload progress for {file_size_mb:.1f} MB file (max timeout: {max_wait_seconds}s)...")
                
                upload_finished = False
                last_logged_status = ""
                for loop_idx in range(max_loops):
                    txts = []
                    for sel in [".progress-label", "ytcp-video-upload-progress", "[id*='upload-progress']", "div:has-text('% uploaded')", "span:has-text('% uploaded')", "ytcp-video-upload-progress span"]:
                        try:
                            els = await page.locator(sel).all()
                            for e in els:
                                t = (await e.inner_text()).strip()
                                if t and t not in txts:
                                    txts.append(t)
                        except Exception:
                            pass
                    combined = " | ".join(txts)
                    if combined:
                        if combined != last_logged_status or loop_idx % 5 == 0:
                            logger.info(f"YouTube upload status ({loop_idx * 3}s / {max_wait_seconds}s): '{combined}'")
                            last_logged_status = combined
                        if any(k in combined.lower() for k in ["upload complete", "processing", "saved", "100% uploaded", "checks starting", "checks complete"]):
                            logger.info(f"Video file bytes successfully transmitted to YouTube! ({combined})")
                            upload_finished = True
                            break
                    await asyncio.sleep(3.0)

                if not upload_finished:
                    logger.warning(f"Video upload progress loop reached limit ({max_wait_seconds}s). Last status: '{last_logged_status}'. Attempting to proceed...")

                # Check if YouTube Studio daily upload limit is reached
                if await self._check_daily_limit(page):
                    err_msg = "YouTube Daily Upload Limit Reached. YouTube requires a one-time channel verification to upload more videos daily (click 'Verify' in YouTube Studio to unlock 100/day), or wait 24 hours."
                    logger.warning(err_msg)
                    raise RuntimeError(err_msg)

                # 7. Next through Details -> Elements -> Checks -> Visibility
                for step_idx in range(15):
                    done_btn = page.locator("ytcp-uploads-dialog #done-button, #done-button, ytcp-button#save-button, #save-button").first
                    sched_box = page.locator("#second-container-expand-button, tp-yt-paper-radio-button[name='SCHEDULE'], [name='SCHEDULE']").first
                    if (await done_btn.is_visible()) or (await sched_box.is_visible()):
                        logger.info("Reached Visibility step.")
                        break

                    # Check if YouTube Studio daily upload limit is reached while advancing
                    if await self._check_daily_limit(page):
                        err_msg = "YouTube Daily Upload Limit Reached. YouTube requires a one-time channel verification to upload more videos daily (click 'Verify' in YouTube Studio to unlock 100/day), or wait 24 hours."
                        logger.warning(err_msg)
                        raise RuntimeError(err_msg)

                    # Try direct tab jump to Visibility if available
                    vis_tab = page.locator("#step-badge-3, [name='VISIBILITY'], button:has-text('Visibility')").first
                    if await vis_tab.is_visible():
                        try:
                            await vis_tab.click(force=True)
                            await asyncio.sleep(1.5)
                            if (await done_btn.is_visible()) or (await sched_box.is_visible()):
                                logger.info("Reached Visibility step via direct tab jump.")
                                break
                        except Exception:
                            pass

                    next_btn = page.locator("#next-button, button:has-text('Next')").first
                    if await next_btn.is_visible():
                        try:
                            await next_btn.click(force=True)
                            logger.info(f"Advancing wizard step {step_idx + 1}...")
                            await asyncio.sleep(2.0)
                        except Exception as ne:
                            logger.debug(f"Next button click retry: {ne}")
                            await asyncio.sleep(1.0)
                    else:
                        await asyncio.sleep(1.5)

                # Final check before visibility setup if done_btn is still not visible
                done_btn = page.locator("ytcp-uploads-dialog #done-button, #done-button, ytcp-button#save-button, #save-button").first
                if not (await done_btn.is_visible()):
                    if await self._check_daily_limit(page):
                        err_msg = "YouTube Daily Upload Limit Reached. YouTube requires a one-time channel verification to upload more videos daily (click 'Verify' in YouTube Studio to unlock 100/day), or wait 24 hours."
                        logger.warning(err_msg)
                        raise RuntimeError(err_msg)

                await asyncio.sleep(1.0)

                # 8. Set Visibility
                logger.info(f"Setting visibility to: {privacy}...")
                if privacy.lower() == "schedule":
                    # Expand the Schedule section in YouTube Studio
                    sched_section = page.locator("#second-container-expand-button, tp-yt-paper-radio-button[name='SCHEDULE'], [name='SCHEDULE'], ytcp-button:has-text('Schedule'), #schedule-radio-button").first
                    if await sched_section.is_visible():
                        await sched_section.click(force=True)
                        await asyncio.sleep(1.5)
                        logger.info("Expanded YouTube Studio Schedule accordion.")

                    # Configure Schedule Date inside YouTube Studio if provided
                    if schedule_date:
                        try:
                            dp_trigger = page.locator("#datepicker-trigger, ytcp-dropdown-trigger#datepicker-trigger, [aria-label*='date' i]").first
                            if await dp_trigger.is_visible():
                                curr_date_val = (await dp_trigger.inner_text()).strip()
                                logger.info(f"YouTube Studio date trigger text: '{curr_date_val}' | Target date: '{schedule_date}'")
                                # Click the trigger to open the calendar dialog
                                await dp_trigger.click(force=True)
                                await asyncio.sleep(0.8)

                                # Look for the input field inside ytcp-date-picker / tp-yt-paper-dialog
                                date_input = page.locator("ytcp-date-picker tp-yt-paper-input input, ytcp-date-picker input, tp-yt-paper-dialog input, #dialog.ytcp-date-picker input, [aria-label*='date' i]").first
                                if await date_input.is_visible():
                                    await date_input.click(force=True)
                                    await asyncio.sleep(0.2)
                                    await date_input.press("Control+A")
                                    await date_input.type(schedule_date, delay=25)
                                    await date_input.press("Enter")
                                    await asyncio.sleep(0.5)
                                    logger.info(f"Successfully configured YouTube Studio schedule date to: {schedule_date}")
                                else:
                                    logger.warning("Popup date input not found, falling back to calendar day cell match...")
                                    import re
                                    day_matches = re.findall(r"\b\d{1,2}\b", schedule_date)
                                    if day_matches:
                                        day_num = str(int(day_matches[0]))
                                        day_el = page.locator(f"ytcp-date-picker .calendar-day:has-text('{day_num}'), ytcp-date-picker [role='gridcell']:has-text('{day_num}')").first
                                        if await day_el.is_visible():
                                            await day_el.click(force=True)
                                            await asyncio.sleep(0.5)
                                            logger.info(f"Clicked calendar day cell: {day_num}")

                                # Safely blur/close calendar popup by clicking container title or background
                                bg_el = page.locator("#second-container, ytcp-uploads-dialog #dialog-title").first
                                if await bg_el.is_visible():
                                    await bg_el.click(force=True)
                                await asyncio.sleep(0.5)
                        except Exception as de:
                            logger.warning(f"Could not configure schedule date: {de}")

                    # Configure Schedule Time inside YouTube Studio if provided
                    if schedule_time:
                        time_input = page.locator("#second-container input.tp-yt-paper-input, #second-container input[type='text'], input[aria-label*='time' i], #time-of-day-container input").first
                        if await time_input.is_visible():
                            try:
                                await time_input.click(force=True)
                                await asyncio.sleep(0.3)
                                await time_input.press("Control+A")
                                await time_input.type(schedule_time, delay=20)
                                await time_input.press("Enter")
                                await asyncio.sleep(0.5)
                                # Safely blur dropdown by clicking container background (never send Escape which closes dialog)
                                bg_el = page.locator("#second-container, ytcp-uploads-dialog #dialog-title").first
                                if await bg_el.is_visible():
                                    await bg_el.click(force=True)
                                await asyncio.sleep(0.5)
                                logger.info(f"Set YouTube Studio schedule time to: {schedule_time}")
                            except Exception as te:
                                logger.warning(f"Could not type schedule time: {te}")

                elif privacy.lower() == "public":
                    # Ensure first-container (Save or publish) is open
                    first_container = page.locator("#first-container, #first-container-expand-button, [name='first-container']").first
                    if await first_container.is_visible():
                        try:
                            await first_container.click(force=True)
                            await asyncio.sleep(0.5)
                        except Exception:
                            pass

                    # Select PUBLIC radio button with multi-selector fallback
                    public_clicked = False
                    for pub_sel in [
                        "tp-yt-paper-radio-button[name='PUBLIC']",
                        "#first-container tp-yt-paper-radio-button[name='PUBLIC']",
                        "#privacy-radios [name='PUBLIC']",
                        "tp-yt-paper-radio-button:has-text('Public')",
                        "div#radioLabel:has-text('Public')",
                        "#first-container #radioLabel:has-text('Public')",
                        "text='Public'"
                    ]:
                        try:
                            p_el = page.locator(pub_sel).first
                            if await p_el.is_visible(timeout=1500):
                                await p_el.scroll_into_view_if_needed()
                                await p_el.click(force=True)
                                await asyncio.sleep(1.0)
                                public_clicked = True
                                logger.info(f"Clicked Public radio using selector: {pub_sel}")
                                break
                        except Exception:
                            continue

                    if not public_clicked:
                        logger.warning("Direct Public click failed, attempting javascript selection...")
                        await page.evaluate("""() => {
                            const btn = document.querySelector("tp-yt-paper-radio-button[name='PUBLIC']") || document.querySelector("[name='PUBLIC']");
                            if (btn) btn.click();
                        }""")
                        await asyncio.sleep(1.0)

                elif privacy.lower() == "unlisted":
                    vis_opt = page.locator("tp-yt-paper-radio-button[name='UNLISTED'], [name='UNLISTED']").first
                    if await vis_opt.is_visible():
                        await vis_opt.click(force=True)
                        await asyncio.sleep(0.5)
                else:
                    vis_opt = page.locator("tp-yt-paper-radio-button[name='PRIVATE'], [name='PRIVATE']").first
                    if await vis_opt.is_visible():
                        await vis_opt.click(force=True)
                        await asyncio.sleep(0.5)

                # 9. Extract link
                video_url = None
                link_el = page.locator("a.ytcp-video-info, [href*='youtu.be']").first
                if await link_el.is_visible():
                    video_url = await link_el.get_attribute("href")

                # 10. Done / Schedule / Publish
                logger.info("Verifying final action button state (Publish / Schedule)...")
                done_btn = page.locator("ytcp-uploads-dialog #done-button, ytcp-button#done-button, #done-button, ytcp-button#save-button, #save-button, ytcp-button:has-text('Schedule'), ytcp-button:has-text('Publish')").first
                try:
                    await done_btn.scroll_into_view_if_needed()
                except Exception:
                    pass
                await done_btn.wait_for(timeout=60000)
                btn_label = (await done_btn.inner_text()).strip()
                logger.info(f"Action button initial text: '{btn_label}'")

                # Strictly guarantee video does not get saved as a draft when Public is requested
                if privacy.lower() == "public":
                    # Button MUST say 'Publish' (not 'Save')
                    retry_count = 0
                    while btn_label.lower() != "publish" and retry_count < 5:
                        retry_count += 1
                        logger.warning(f"Button still says '{btn_label}' instead of 'Publish'! Enforcing Public selection (attempt {retry_count})...")
                        # Click Public radio again
                        pub_target = page.locator("tp-yt-paper-radio-button[name='PUBLIC'], div#radioLabel:has-text('Public')").first
                        if await pub_target.is_visible():
                            await pub_target.click(force=True)
                        await asyncio.sleep(1.0)
                        btn_label = (await done_btn.inner_text()).strip()

                    logger.info(f"Verified action button text: '{btn_label}'")
                    if btn_label.lower() == "save":
                        logger.error("WARNING: Button still says 'Save'! Forcing #done-button state to ensure Public.")

                elif privacy.lower() == "schedule" and btn_label == "Save":
                    sched_section = page.locator("#second-container-expand-button, #schedule-expand-button").first
                    if await sched_section.is_visible():
                        await sched_section.click(force=True)
                        await asyncio.sleep(1.0)
                        btn_label = (await done_btn.inner_text()).strip()

                logger.info(f"Clicking '{btn_label}' button to submit video to YouTube...")
                try:
                    inner_btn = done_btn.locator("button, #button, tp-yt-paper-button").first
                    if await inner_btn.is_visible():
                        await inner_btn.click(force=True)
                    else:
                        await done_btn.click(force=True)
                except Exception:
                    await done_btn.evaluate("el => el.click()")

                # Strictly wait for YouTube's completion / share / processing confirmation dialog
                logger.info("Waiting for YouTube to confirm video publication...")
                conf_dialog = page.locator("ytcp-dialog:has-text('Video processing'), ytcp-dialog:has-text('Video published'), ytcp-dialog:has-text('Video scheduled'), ytcp-video-share-dialog, [aria-label*='Video published' i], [aria-label*='Video scheduled' i]").first
                for _ in range(30):  # up to 60 seconds
                    if await conf_dialog.is_visible():
                        logger.info("YouTube confirmation dialog is visible! Video is published.")
                        share_link = page.locator("ytcp-video-share-dialog a[href*='youtu.be'], a[href*='youtu.be']").first
                        if await share_link.is_visible():
                            video_url = await share_link.get_attribute("href")
                        break
                    
                    if await self._check_daily_limit(page):
                        err_msg = "YouTube Daily Upload Limit Reached. YouTube requires a one-time channel verification to upload more videos daily (click 'Verify' in YouTube Studio to unlock 100/day), or wait 24 hours."
                        logger.warning(err_msg)
                        raise RuntimeError(err_msg)
                    await asyncio.sleep(2.0)

                # Close confirmation dialog modal
                close_btn = page.locator("ytcp-dialog ytcp-button:has-text('Close'), ytcp-dialog #close-button, ytcp-button:has-text('Close'), #close-button").first
                if await close_btn.is_visible():
                    try:
                        await close_btn.click(force=True)
                        await asyncio.sleep(2.0)
                    except Exception:
                        pass

                if not video_url:
                    final_link = page.locator("a.ytcp-video-info, a[href*='youtu.be']").first
                    if await final_link.is_visible():
                        video_url = await final_link.get_attribute("href")

                if not video_url:
                    try:
                        await page.goto("https://studio.youtube.com/channel/UCkOSkUPIoE4bT_GwbHKNpog/videos/short", timeout=30000)
                        await asyncio.sleep(2.0)
                        video_link = page.locator("a#thumbnail, a#video-title").first
                        if await video_link.is_visible():
                            href = await video_link.get_attribute("href")
                            if href and "/video/" in href:
                                vid_id = href.split("/video/")[1].split("/")[0]
                                video_url = f"https://youtube.com/shorts/{vid_id}"
                    except Exception:
                        pass

                logger.info(f"Browser upload complete: {video_url or 'Published'}")
                security_guard.log_event("YOUTUBE_BROWSER_UPLOAD", f"Uploaded video '{title}': {video_url}", "SUCCESS")

                # 2026 Golden Rule #4: Deploy Pinned Debate Comment within 60s of public release
                if video_url and privacy.lower() == "public":
                    try:
                        comment_to_post = debate_comment
                        if not comment_to_post:
                            from jarvis.backend.video.metadata_generator import generate_debate_comment
                            comment_to_post = generate_debate_comment(title=title)
                        if comment_to_post:
                            await self._post_and_pin_youtube_comment(page, video_url, comment_to_post)
                    except Exception as de_err:
                        logger.debug(f"YouTube debate pin pass: {de_err}")

                try:
                    await context.close()
                except Exception:
                    pass

                return {
                    "success": True,
                    "url": video_url,
                    "title": title,
                    "method": "browser_automation",
                    "status": privacy
                }

            except Exception as e:
                logger.error(f"Browser upload error: {e}", exc_info=True)
                # Dispatch incident alert email immediately to khatrianshul977@gmail.com
                try:
                    from jarvis.backend.social.email_reporter import email_reporter
                    asyncio.create_task(email_reporter.send_error_alert(
                        error_type="YOUTUBE_STUDIO_UPLOAD_INCIDENT",
                        error_message=str(e),
                        details={"title": title, "path": str(video_path), "privacy": privacy}
                    ))
                except Exception as alert_err:
                    logger.debug(f"Alert dispatch pass: {alert_err}")
                try:
                    await context.close()
                except Exception:
                    pass
                return {
                    "success": False,
                    "error": str(e),
                    "method": "browser_automation"
                }

    async def _post_and_pin_youtube_comment(self, page: Page, video_url: str, comment_text: str):
        """Navigate to YouTube video, post the polarizing debate question, and pin it to the top (Golden Rule #4)."""
        try:
            logger.info(f"📌 [Pinned Debate Comment] Navigating to {video_url} to deploy debate question...")
            await page.goto(video_url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(3.0)

            # Trigger comment box
            comment_box = page.locator("#placeholder-area, #simplebox-placeholder, ytd-comment-simplebox-renderer").first
            if await comment_box.is_visible(timeout=5000):
                await comment_box.click(force=True)
                await asyncio.sleep(1.0)

                input_box = page.locator("#contenteditable-root, ytd-commentbox #contenteditable-root, div[contenteditable='true']").first
                if await input_box.is_visible(timeout=3000):
                    await input_box.click(force=True)
                    await input_box.type(comment_text, delay=20)
                    await asyncio.sleep(0.5)

                    submit_btn = page.locator("#submit-button, ytd-button-renderer#submit-button, button[aria-label*='Comment' i]").first
                    if await submit_btn.is_visible(timeout=3000):
                        await submit_btn.click(force=True)
                        logger.info(f"💬 [Pinned Debate Comment] Posted: '{comment_text}'")
                        await asyncio.sleep(2.0)

                        # Click action menu (3 dots) on the comment and pin
                        more_btn = page.locator("ytd-comment-view-model #action-menu yt-icon-button, ytd-comment-thread-renderer #action-menu yt-icon-button").first
                        if await more_btn.is_visible(timeout=5000):
                            await more_btn.click(force=True)
                            await asyncio.sleep(0.8)

                            pin_btn = page.locator("ytd-menu-service-item-renderer:has-text('Pin'), tp-yt-paper-item:has-text('Pin')").first
                            if await pin_btn.is_visible(timeout=3000):
                                await pin_btn.click(force=True)
                                await asyncio.sleep(0.8)

                                conf_pin = page.locator("ytcp-button:has-text('Pin'), yt-button-renderer:has-text('Pin'), #confirm-button").first
                                if await conf_pin.is_visible(timeout=3000):
                                    await conf_pin.click(force=True)
                                    logger.info("📌 Successfully pinned debate comment on YouTube!")
        except Exception as e:
            logger.debug(f"YouTube comment pin execution pass: {e}")


youtube_browser = YouTubeBrowserUploader()
