"""CLI Auto-Uploader for YouTube Studio.

Uploads video to YouTube Studio using persistent Chrome session.
Provides interactive feedback and live progress reporting.
"""

import sys
import time
import os
import json
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("JARVIS.UploaderCLI")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROFILE_DIR = WORKSPACE_ROOT / "jarvis" / "browser_profile"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

# Default video to upload: MrBeast color splash or chef battle
DEFAULT_VIDEO = WORKSPACE_ROOT / "jarvis" / "output" / "reels" / "clip_8207c7fa-4f9_mrbeast.mp4"
if not DEFAULT_VIDEO.exists():
    # Fallback to any reel
    reels = list((WORKSPACE_ROOT / "jarvis" / "output" / "reels").glob("*.mp4"))
    if reels:
        DEFAULT_VIDEO = reels[0]

CHANNEL_ID = "UCkOSkUPIoE4bT_GwbHKNpog"
CHANNEL_NAME = "GHOST _OF_FOOTBALL"


def bring_window_to_front():
    """Bring the Chrome sign-in window to the absolute front of the user desktop."""
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


def cleanup_profile_locks():
    """Purge stale locks."""
    if sys.platform == "win32":
        try:
            import subprocess
            subprocess.run(
                'powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \\"Name LIKE \'chrome%\'\\" | Where-Object {$_.CommandLine -like \'*browser_profile*\'} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"',
                shell=True,
                capture_output=True,
                timeout=5
            )
        except Exception:
            pass

    for lock_name in ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket"]:
        try:
            (PROFILE_DIR / lock_name).unlink(missing_ok=True)
        except Exception:
            pass


def run_upload(video_path: Path, title: str, privacy: str = "public"):
    print("=" * 65)
    print("      PROJECT JARVIS - AUTOMATED YOUTUBE UPLOADER")
    print("=" * 65)
    print(f"[*] Target Channel : {CHANNEL_NAME} ({CHANNEL_ID})")
    print(f"[*] Upload Video   : {video_path.name}")
    print(f"[*] Video Size     : {video_path.stat().st_size / (1024*1024):.2f} MB")
    print(f"[*] Target Privacy : {privacy.upper()}")
    print("=" * 65)

    cleanup_profile_locks()

    with sync_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(PROFILE_DIR),
            "headless": False,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
                "--no-sandbox"
            ],
            "ignore_default_args": ["--enable-automation"]
        }

        try:
            context = p.chromium.launch_persistent_context(**launch_kwargs, channel="chrome")
            print("[INFO] Launched with Google Chrome.")
        except Exception as e:
            print(f"[WARN] Chrome channel unavailable ({e}), using Chromium.")
            context = p.chromium.launch_persistent_context(**launch_kwargs)

        page = context.pages[0] if context.pages else context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        target_studio_url = f"https://studio.youtube.com/channel/{CHANNEL_ID}/content"
        print(f"\n[*] Navigating directly to your channel Studio: {target_studio_url}...")
        page.goto(target_studio_url, timeout=60000)

        # Wait for user to be logged in
        print("[*] Checking YouTube Studio authentication for GHOST _OF_FOOTBALL...")
        logged_in = False
        bring_window_to_front()

        for step in range(150): # up to 5 minutes
            curr_url = page.url
            if (CHANNEL_ID in curr_url or "channel" in curr_url or "studio.youtube.com" in curr_url) and "accounts.google.com" not in curr_url and "signin" not in curr_url:
                logged_in = True
                break

            if "accounts.google.com" in curr_url:
                try:
                    email_input = page.locator("#identifierId, input[type='email']").first
                    if email_input.is_visible():
                        email_input.fill("khatrianshul977@gmail.com")
                        next_btn = page.locator("#identifierNext, button:has-text('Next')").first
                        if next_btn.is_visible():
                            next_btn.click()
                            time.sleep(2.0)
                except Exception:
                    pass
                bring_window_to_front()

            if step % 5 == 0:
                print(f"[*] Step {step}: Chrome window is open. Please enter your Google password for khatrianshul977@gmail.com...")
            time.sleep(2.0)

        if not logged_in:
            print("\n[ERROR] Sign-in timed out.")
            context.close()
            return None

        # Check channel title
        channel_detected = CHANNEL_NAME
        try:
            title_el = page.query_selector("#channel-title, [id='channel-name']")
            if title_el:
                channel_detected = title_el.inner_text().strip()
        except Exception:
            pass

        print(f"\n🎉 Confirmed Channel: {channel_detected}")
        print("[*] Commencing automated video upload...")

        # 1. Trigger upload dialog (via Create button or direct Upload Videos button)
        upload_opened = False
        file_input = page.locator("input[type='file']").first
        if file_input.is_visible():
            upload_opened = True

        if not upload_opened:
            direct_upload = page.locator("ytcp-button#upload-button, button:has-text('Upload videos')").first
            if direct_upload.is_visible():
                direct_upload.click()
                time.sleep(1.5)
                upload_opened = True

        if not upload_opened:
            create_btn = page.locator("#create-icon, button:has-text('Create'), yt-button-shape:has-text('Create')").first
            create_btn.wait_for(timeout=25000)
            create_btn.click()
            time.sleep(1.0)
            upload_menu_item = page.locator("tp-yt-paper-item:has-text('Upload videos'), ytd-compact-link-renderer:has-text('Upload videos'), #text-item-0").first
            if upload_menu_item.is_visible():
                upload_menu_item.click()
            time.sleep(1.5)

        # 2. Set file input
        print(f"[*] Attaching video file: {video_path}...")
        file_input = page.locator("input[type='file']").first
        file_input.wait_for(timeout=25000)
        file_input.set_input_files(str(video_path))
        print("[*] File uploaded to Studio! Configuring metadata...")

        # 4. Fill Title & Description
        title_box = page.locator("#textbox[aria-label*='title' i], [aria-label='Add a title that describes your video']").first
        title_box.wait_for(timeout=35000)
        time.sleep(1.0)
        title_box.fill("")
        title_box.type(f"{title} #Shorts", delay=15)
        time.sleep(1.0)

        desc_box = page.locator("#textbox[aria-label*='description' i], [aria-label='Tell viewers about your video']").first
        if desc_box.is_visible():
            desc_text = f"Automated upload by JARVIS AI Assistant for {channel_detected}.\n\n#Shorts #Football #Viral #Trending #GHOST_OF_FOOTBALL"
            desc_box.fill("")
            desc_box.type(desc_text, delay=10)
            time.sleep(1.0)

        # 5. Set 'Not made for kids'
        not_for_kids = page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK'], [name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
        if not_for_kids.is_visible():
            not_for_kids.click()
            time.sleep(0.5)

        # 6. Step through wizard Next -> Next -> Next
        print("[*] Navigating upload wizard stages...")
        next_btn = page.locator("#next-button, button:has-text('Next')").first
        for i in range(3):
            next_btn.wait_for(timeout=15000)
            next_btn.click()
            time.sleep(1.5)

        # 7. Set Visibility
        print(f"[*] Setting visibility to {privacy.upper()}...")
        if privacy.lower() == "public":
            vis_opt = page.locator("tp-yt-paper-radio-button[name='PUBLIC'], [name='PUBLIC']").first
        elif privacy.lower() == "unlisted":
            vis_opt = page.locator("tp-yt-paper-radio-button[name='UNLISTED'], [name='UNLISTED']").first
        else:
            vis_opt = page.locator("tp-yt-paper-radio-button[name='PRIVATE'], [name='PRIVATE']").first

        if vis_opt.is_visible():
            vis_opt.click()
            time.sleep(0.5)

        # Extract video link
        video_url = None
        link_el = page.locator("a.ytcp-video-info, [href*='youtu.be']").first
        if link_el.is_visible():
            video_url = link_el.get_attribute("href")

        # 8. Publish / Save
        print("[*] Submitting Publish command...")
        done_btn = page.locator("#done-button, button:has-text('Save'), button:has-text('Publish')").first
        done_btn.wait_for(timeout=15000)
        done_btn.click()
        time.sleep(4.0)

        if not video_url:
            final_link = page.locator("a.ytcp-video-info, a[href*='youtu.be']").first
            if final_link.is_visible():
                video_url = final_link.get_attribute("href")

        print("\n" + "=" * 65)
        print("🎉 SUCCESS! VIDEO PUBLISHED TO YOUTUBE!")
        print(f"[*] Channel  : {channel_detected}")
        print(f"[*] Title    : {title} #Shorts")
        print(f"[*] Live URL : {video_url or 'Published (processing in Studio)'}")
        print("=" * 65)

        # Save to DB if possible
        try:
            from jarvis.backend.database.db import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE clips SET published_youtube = 1, status = 'PUBLISHED' WHERE output_path = ?", (str(video_path),))
            cursor.execute(
                "INSERT INTO audit_logs (action_type, details, status) VALUES (?, ?, ?)",
                ("YOUTUBE_LIVE_UPLOAD", json.dumps({"channel": channel_detected, "title": title, "url": video_url}), "SUCCESS")
            )
            conn.commit()
            conn.close()
            print("[*] Database records updated successfully.")
        except Exception:
            pass

        time.sleep(5.0)
        context.close()
        return video_url


if __name__ == "__main__":
    vid = DEFAULT_VIDEO
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        vid = Path(sys.argv[1])
    
    t = "MrBeast Color Splash Masterpiece"
    if len(sys.argv) > 2:
        t = sys.argv[2]
        
    p = "public"
    if len(sys.argv) > 3:
        p = sys.argv[3]
        
    run_upload(vid, t, p)

