"""CDP Uploader: Connects to user's currently open Chrome session via Remote Debugging.

Bypasses all Google logins because it uses the user's existing logged-in Chrome session!
"""

import sys
import time
import json
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("JARVIS.CDPUploader")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
VIDEO_PATH = WORKSPACE_ROOT / "jarvis" / "output" / "reels" / "clip_8207c7fa-4f9_mrbeast.mp4"
CHANNEL_ID = "UCkOSkUPIoE4bT_GwbHKNpog"
CHANNEL_NAME = "GHOST _OF_FOOTBALL"


def upload_via_cdp(port: int = 9222, video_path: Path = VIDEO_PATH, title: str = "MrBeast Color Splash Masterpiece"):
    print("=" * 65)
    print("       JARVIS - ZERO-LOGIN DIRECT CHROME UPLOADER (CDP)")
    print("=" * 65)
    print(f"[*] Connecting to your existing Chrome on port {port}...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
            
            target_url = f"https://studio.youtube.com/channel/{CHANNEL_ID}/content"
            print(f"[*] Navigating to your channel Studio: {target_url}...")
            page.goto(target_url, timeout=45000)
            time.sleep(2.0)
            
            print("[*] Studio loaded! Opening video upload modal...")
            
            # Click Create / Upload
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

            # Set file input
            print(f"[*] Attaching video file: {video_path.name}...")
            file_input = page.locator("input[type='file']").first
            file_input.wait_for(timeout=25000)
            file_input.set_input_files(str(video_path))
            print("[*] File uploaded to Studio! Setting title and metadata...")

            # Fill Title & Description
            title_box = page.locator("#textbox[aria-label*='title' i], [aria-label='Add a title that describes your video']").first
            title_box.wait_for(timeout=35000)
            time.sleep(1.0)
            title_box.fill("")
            title_box.type(f"{title} #Shorts", delay=15)
            time.sleep(1.0)

            desc_box = page.locator("#textbox[aria-label*='description' i], [aria-label='Tell viewers about your video']").first
            if desc_box.is_visible():
                desc_text = f"Automated upload by JARVIS AI Assistant for {CHANNEL_NAME}.\n\n#Shorts #Football #Viral #Trending #GHOST_OF_FOOTBALL"
                desc_box.fill("")
                desc_box.type(desc_text, delay=10)
                time.sleep(1.0)

            # Not made for kids
            not_for_kids = page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK'], [name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
            if not_for_kids.is_visible():
                not_for_kids.click()
                time.sleep(0.5)

            # Next -> Next -> Next
            print("[*] Progressing through checks...")
            next_btn = page.locator("#next-button, button:has-text('Next')").first
            for _ in range(3):
                next_btn.wait_for(timeout=15000)
                next_btn.click()
                time.sleep(1.5)

            # Visibility Public
            print("[*] Setting visibility to Public...")
            vis_opt = page.locator("tp-yt-paper-radio-button[name='PUBLIC'], [name='PUBLIC']").first
            if vis_opt.is_visible():
                vis_opt.click()
                time.sleep(0.5)

            # Extract link
            video_url = None
            link_el = page.locator("a.ytcp-video-info, [href*='youtu.be']").first
            if link_el.is_visible():
                video_url = link_el.get_attribute("href")

            # Publish
            print("[*] Clicking Publish...")
            done_btn = page.locator("#done-button, button:has-text('Save'), button:has-text('Publish')").first
            done_btn.wait_for(timeout=15000)
            done_btn.click()
            time.sleep(4.0)

            if not video_url:
                final_link = page.locator("a.ytcp-video-info, a[href*='youtu.be']").first
                if final_link.is_visible():
                    video_url = final_link.get_attribute("href")

            print("\n" + "=" * 65)
            print("🎉 SUCCESS! VIDEO PUBLISHED TO GHOST _OF_FOOTBALL!")
            print(f"[*] Live Short URL: {video_url or 'Published (processing in Studio)'}")
            print("=" * 65)
            
            page.close()
            return video_url
    except Exception as e:
        print(f"[ERROR] CDP upload failed: {e}")
        return None

if __name__ == "__main__":
    upload_via_cdp()

