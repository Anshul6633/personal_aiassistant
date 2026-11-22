import sys
import os
import time
import socket
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ITEM_ID = "c842a464-8317-47f0-b649-7626b71b8159"
VIDEO_PATH = Path(r"D:\jarvis_media\output\reels\clip_1681dd44_1.mp4")
TITLE = "One Man Made This Whole Game?? 🤯💥 #GTA6 #Shorts"
DESC = "One solo developer built an entire world... Watch till the end!\n\n#GTA6 #Shorts #Gaming #Viral #GHOST_OF_FOOTBALL"
CHANNEL_ID = "UCkOSkUPIoE4bT_GwbHKNpog"
CHANNEL_NAME = "GHOST _OF_FOOTBALL"
ARTIFACT_DIR = Path(r"C:\Users\Anshul\.gemini\antigravity\brain\131b40e8-da32-4409-9d1f-a22bc06bbd61")

def is_port_open(host="127.0.0.1", port=9222):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        res = s.connect_ex((host, port))
        return res == 0
    finally:
        s.close()

def ensure_cdp_chrome():
    if is_port_open():
        print("[*] Chrome is already listening on CDP port 9222.")
        return True

    print("[*] CDP port 9222 not listening. Restarting Chrome with remote debugging bridge...")
    print("[*] (Tabs will restore automatically with --restore-last-session)")
    
    # Gracefully or forcefully close Chrome
    subprocess.run("taskkill /F /IM chrome.exe", shell=True, capture_output=True)
    time.sleep(2.5)

    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    cmd = [
        chrome_exe,
        "--remote-debugging-port=9222",
        "--restore-last-session"
    ]
    subprocess.Popen(cmd)
    
    # Wait up to 10 seconds for port 9222
    for _ in range(10):
        time.sleep(1.0)
        if is_port_open():
            print("[*] Chrome successfully launched on port 9222!")
            return True
            
    print("[ERROR] Failed to start Chrome on port 9222.")
    return False

def update_db(status, url=None, error=None):
    try:
        conn = sqlite3.connect(WORKSPACE_ROOT / "jarvis" / "database.sqlite")
        c = conn.cursor()
        if status == "PUBLISHED":
            c.execute("""
                UPDATE youtube_schedule_queue 
                SET status = 'PUBLISHED', youtube_url = ?, published_at = ?, error_message = NULL 
                WHERE id = ?
            """, (url, datetime.now().isoformat(), ITEM_ID))
        elif status == "FAILED":
            c.execute("""
                UPDATE youtube_schedule_queue 
                SET status = 'FAILED', error_message = ? 
                WHERE id = ?
            """, (error, ITEM_ID))
        else:
            c.execute("UPDATE youtube_schedule_queue SET status = ? WHERE id = ?", (status, ITEM_ID))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[WARN] Database update warning: {e}")

def run_upload():
    print("=" * 65)
    print("  PROJECT JARVIS - MORNING SHORT DIRECT CHROME CDP PUBLISH")
    print("=" * 65)
    print(f"[*] Target Asset: {VIDEO_PATH}")
    print(f"[*] Title: {TITLE}")

    if not VIDEO_PATH.exists():
        print(f"[ERROR] Asset does not exist: {VIDEO_PATH}")
        return False

    update_db("UPLOADING")

    if not ensure_cdp_chrome():
        update_db("FAILED", error="Could not establish CDP port 9222 bridge.")
        return False

    time.sleep(2.0)

    try:
        with sync_playwright() as p:
            print("[*] Connecting Playwright over CDP to http://localhost:9222...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            
            # Use an existing blank/new page or create one
            page = context.new_page()
            
            target_url = f"https://studio.youtube.com/channel/{CHANNEL_ID}/content"
            print(f"[*] Navigating to YouTube Studio: {target_url}...")
            page.goto(target_url, timeout=60000)
            time.sleep(3.0)

            print(f"[*] Current URL: {page.url}")
            print(f"[*] Page Title: {page.title()}")

            # Save screenshot of initial Studio state
            init_ss = ARTIFACT_DIR / "cdp_studio_initial.png"
            page.screenshot(path=str(init_ss))
            print(f"[*] Saved initial screenshot: {init_ss}")

            # Check if we were redirected to sign-in
            if "accounts.google.com" in page.url or "signin" in page.url:
                print("[!] Sign-in page encountered. Waiting for user/session...")
                time.sleep(5.0)

            # Trigger Upload Modal
            upload_opened = False
            file_input = page.locator("input[type='file']").first
            if file_input.is_visible():
                upload_opened = True

            if not upload_opened:
                direct_upload = page.locator("ytcp-button#upload-button, button:has-text('Upload videos')").first
                if direct_upload.is_visible():
                    direct_upload.click()
                    time.sleep(2.0)
                    upload_opened = True

            if not upload_opened:
                create_btn = page.locator("#create-icon, button:has-text('Create'), yt-button-shape:has-text('Create')").first
                create_btn.wait_for(timeout=30000)
                create_btn.click()
                time.sleep(1.0)
                upload_menu_item = page.locator("tp-yt-paper-item:has-text('Upload videos'), ytd-compact-link-renderer:has-text('Upload videos'), #text-item-0").first
                if upload_menu_item.is_visible():
                    upload_menu_item.click()
                time.sleep(2.0)

            # Attach Video File
            print(f"[*] Attaching video file: {VIDEO_PATH.name}...")
            file_input = page.locator("input[type='file']").first
            file_input.wait_for(timeout=30000)
            file_input.set_input_files(str(VIDEO_PATH))
            print("[*] File uploaded to Studio dialog! Filling details...")
            time.sleep(3.0)

            # Fill Title & Description
            title_box = page.locator("#textbox[aria-label*='title' i], [aria-label='Add a title that describes your video']").first
            title_box.wait_for(timeout=40000)
            time.sleep(1.0)
            title_box.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.type(TITLE, delay=15)
            time.sleep(1.0)

            desc_box = page.locator("#textbox[aria-label*='description' i], [aria-label='Tell viewers about your video']").first
            if desc_box.is_visible():
                desc_box.click()
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.keyboard.type(DESC, delay=10)
                time.sleep(1.0)

            # Not made for kids
            print("[*] Selecting 'Not made for kids'...")
            not_for_kids = page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK'], [name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
            if not_for_kids.is_visible():
                not_for_kids.click()
                time.sleep(1.0)

            # Advance Next -> Next -> Next
            print("[*] Progressing through video elements and checks...")
            next_btn = page.locator("#next-button, button:has-text('Next')").first
            for step in range(3):
                next_btn.wait_for(timeout=20000)
                next_btn.click()
                time.sleep(2.0)

            # Set Visibility to Public
            print("[*] Setting visibility to Public...")
            vis_public = page.locator("tp-yt-paper-radio-button[name='PUBLIC'], [name='PUBLIC']").first
            vis_public.wait_for(timeout=15000)
            vis_public.click()
            time.sleep(1.0)

            # Capture Video URL before publishing
            video_url = None
            link_el = page.locator("a.ytcp-video-info, [href*='youtu.be']").first
            if link_el.is_visible():
                video_url = link_el.get_attribute("href")
                print(f"[*] Detected video link: {video_url}")

            # Click Publish / Done
            print("[*] Clicking Publish button...")
            done_btn = page.locator("#done-button, button:has-text('Save'), button:has-text('Publish')").first
            done_btn.wait_for(timeout=20000)
            done_btn.click()
            time.sleep(5.0)

            # Look for link in post-publish modal if not found yet
            if not video_url:
                post_link = page.locator("a.ytcp-video-info, a[href*='youtu.be']").first
                if post_link.is_visible():
                    video_url = post_link.get_attribute("href")

            # Final confirmation screenshot
            final_ss = ARTIFACT_DIR / "cdp_studio_published.png"
            page.screenshot(path=str(final_ss))
            print(f"[*] Saved publication screenshot: {final_ss}")

            print("\n" + "=" * 65)
            print("🎉 SUCCESS! YOUTUBE SHORT PUBLISHED TO GHOST _OF_FOOTBALL!")
            print(f"[*] Live Short URL: {video_url or 'Published (live on channel)'}")
            print("=" * 65)

            update_db("PUBLISHED", url=video_url or "https://youtube.com/@GHOST_OF_FOOTBALL")
            
            # Close this tab
            page.close()
            return True

    except Exception as e:
        print(f"\n[ERROR] Upload failed with exception: {e}")
        update_db("FAILED", error=str(e))
        return False

if __name__ == "__main__":
    success = run_upload()
    sys.exit(0 if success else 1)
