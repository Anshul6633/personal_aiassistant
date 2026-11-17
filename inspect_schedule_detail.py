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

async def inspect():
    async with async_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(profile_dir),
            "headless": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        }
        context = await p.chromium.launch_persistent_context(**launch_kwargs)
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://studio.youtube.com/channel/UCkOSkUPIoE4bT_GwbHKNpog/content", timeout=60000)
        await asyncio.sleep(2)

        create_btn = page.locator("#create-icon, button:has-text('Create')").first
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

        title_box = page.locator("#textbox[aria-label*='title' i]").first
        await title_box.wait_for(timeout=35000)

        not_kids = page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
        if await not_kids.is_visible():
            await not_kids.click(force=True)
            await asyncio.sleep(0.5)

        next_btn = page.locator("#next-button").first
        for i in range(3):
            await next_btn.click(force=True)
            await asyncio.sleep(1.5)

        await asyncio.sleep(2)

        # Click Schedule section
        sched_section = page.locator("#second-container-expand-button, [aria-label*='Schedule' i]").first
        if await sched_section.is_visible():
            await sched_section.click()
            await asyncio.sleep(1)

        # Inspect all inputs and dropdowns under schedule container
        sched_container = page.locator("#second-container, ytcp-uploads-schedule").first
        print(f"Container HTML:\n{await sched_container.inner_html()[:2000]}", flush=True)

        # Check date trigger and time trigger
        date_el = page.locator("#datepicker-trigger").first
        print(f"\nDate Trigger outer HTML:\n{await date_el.evaluate('el => el.outerHTML')}", flush=True)

        time_el = page.locator("#time-of-day-trigger").first
        print(f"\nTime Trigger outer HTML:\n{await time_el.evaluate('el => el.outerHTML')}", flush=True)

        close_btn = page.locator("#close-button").first
        if await close_btn.is_visible():
            await close_btn.click()
            await asyncio.sleep(1)
            discard_btn = page.locator("ytcp-button:has-text('Discard')").first
            if await discard_btn.is_visible():
                await discard_btn.click()

        await context.close()

if __name__ == "__main__":
    asyncio.run(inspect())

