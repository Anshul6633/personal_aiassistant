import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

profile_dir = Path("jarvis/browser_profile").resolve()
for lock_name in ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket"]:
    try:
        (profile_dir / lock_name).unlink(missing_ok=True)
    except Exception:
        pass

async def test_full_schedule():
    print("[*] Starting Playwright with persistent context...", flush=True)
    async with async_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(profile_dir),
            "headless": False,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox", "--start-maximized"],
            "ignore_default_args": ["--enable-automation"]
        }
        try:
            context = await p.chromium.launch_persistent_context(**launch_kwargs, channel="chrome")
        except Exception:
            context = await p.chromium.launch_persistent_context(**launch_kwargs)

        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        print("[*] Navigating to YouTube Studio Content...", flush=True)
        await page.goto("https://studio.youtube.com/channel/UCkOSkUPIoE4bT_GwbHKNpog/content", timeout=60000)
        await asyncio.sleep(2)

        create_btn = page.locator("#create-icon, button:has-text('Create')").first
        await create_btn.wait_for(timeout=25000)
        await create_btn.click()
        await asyncio.sleep(1)

        upload_menu = page.locator("tp-yt-paper-item:has-text('Upload videos'), #text-item-0").first
        if await upload_menu.is_visible():
            await upload_menu.click()
        await asyncio.sleep(2)

        file_input = page.locator("input[type='file']").first
        await file_input.wait_for(state="attached", timeout=20000)
        test_video = Path("jarvis/tests/sample_podcast.mp4").resolve()
        await file_input.set_input_files(str(test_video))
        print("[*] Attached video...", flush=True)

        title_box = page.locator("#textbox[aria-label*='title' i]").first
        await title_box.wait_for(timeout=35000)
        await title_box.fill("")
        await title_box.type("Haaland vs Mbappe Ultimate Duel ⚡ #Shorts", delay=10)

        not_kids = page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
        if await not_kids.is_visible():
            await not_kids.click(force=True)
            await asyncio.sleep(0.5)

        next_btn = page.locator("#next-button, button:has-text('Next')").first
        for i in range(3):
            await next_btn.wait_for(timeout=15000)
            await next_btn.click()
            await asyncio.sleep(1.5)
            print(f"[*] Clicked next {i+1}", flush=True)

        await asyncio.sleep(1.5)
        print("[*] Arrived at Visibility step!", flush=True)

        sched_section = page.locator("#second-container-expand-button, ytcp-button:has-text('Schedule')").first
        if await sched_section.is_visible():
            await sched_section.click()
            await asyncio.sleep(1.5)
            print("[*] Clicked Schedule section accordion", flush=True)

        link_el = page.locator("a.ytcp-video-info, a[href*='youtu.be']").first
        yt_url = await link_el.get_attribute("href") if await link_el.is_visible() else None
        print(f"[*] Video URL: {yt_url}", flush=True)

        done_btn = page.locator("#done-button").first
        await done_btn.wait_for(state="visible", timeout=15000)
        btn_text = await done_btn.inner_text()
        print(f"[*] Action button label: '{btn_text}'", flush=True)
        await done_btn.click()
        print("[*] Schedule button clicked! Waiting 5s...", flush=True)
        await asyncio.sleep(5.0)

        Path("jarvis/tests").mkdir(parents=True, exist_ok=True)
        await page.screenshot(path="jarvis/tests/youtube_scheduled_success.png")
        print("[*] Saved screenshot to jarvis/tests/youtube_scheduled_success.png", flush=True)

        close_modal = page.locator("#close-button, ytcp-button:has-text('Close')").first
        if await close_modal.is_visible():
            await close_modal.click()
            await asyncio.sleep(1.0)

        await context.close()
        print(f"[*] Successfully scheduled video inside YouTube Studio! Live Link: {yt_url}", flush=True)

if __name__ == "__main__":
    asyncio.run(test_full_schedule())
