import sys
import logging
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DEBUG_UPLOAD")

profile_dir = Path("jarvis/browser_profile").resolve()
for lock in ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket"]:
    try:
        (profile_dir / lock).unlink(missing_ok=True)
    except Exception:
        pass

async def run():
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
        logger.info("Attached video file...")

        title_box = page.locator("#textbox[aria-label*='title' i]").first
        await title_box.wait_for(timeout=35000)
        await title_box.fill("")
        await title_box.type("Epic Goal Duel ⚡ #Shorts", delay=10)
        logger.info("Filled title.")

        # Audience
        not_kids = page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
        await not_kids.scroll_into_view_if_needed()
        await not_kids.click(force=True)
        logger.info("Clicked not made for kids.")
        await asyncio.sleep(1)

        Path("jarvis/tests").mkdir(parents=True, exist_ok=True)
        await page.screenshot(path="jarvis/tests/step1_details.png")

        # Now let's see how next-button behaves
        next_btn = page.locator("#next-button").first
        print(f"next_btn count: {await next_btn.count()}, is_visible: {await next_btn.is_visible()}")
        
        # Click next 1
        await next_btn.click(force=True)
        await asyncio.sleep(2)
        await page.screenshot(path="jarvis/tests/step2_elements.png")
        print("Clicked next 1")

        # Click next 2
        await next_btn.click(force=True)
        await asyncio.sleep(2)
        await page.screenshot(path="jarvis/tests/step3_checks.png")
        print("Clicked next 2")

        # Click next 3
        await next_btn.click(force=True)
        await asyncio.sleep(2)
        await page.screenshot(path="jarvis/tests/step4_visibility.png")
        print("Clicked next 3")

        # Check visibility
        done_btn = page.locator("ytcp-uploads-dialog #done-button").first
        print(f"done_btn is_visible: {await done_btn.is_visible()}, text: '{await done_btn.inner_text()}'")

        # Close
        close_btn = page.locator("#close-button").first
        if await close_btn.is_visible():
            await close_btn.click()
            await asyncio.sleep(1)
            discard_btn = page.locator("ytcp-button:has-text('Discard')").first
            if await discard_btn.is_visible():
                await discard_btn.click()

        await context.close()

if __name__ == "__main__":
    asyncio.run(run())

