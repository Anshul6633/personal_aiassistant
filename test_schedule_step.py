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

        title_box = page.locator("#textbox[aria-label*='title' i]").first
        await title_box.wait_for(timeout=35000)
        await title_box.fill("")
        await title_box.type("Football Wonder Goal #Shorts", delay=10)

        not_kids = page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
        if await not_kids.is_visible():
            await not_kids.click(force=True)
            await asyncio.sleep(0.5)

        next_btn = page.locator("#next-button").first
        for i in range(3):
            await next_btn.wait_for(timeout=15000)
            await next_btn.click(force=True)
            await asyncio.sleep(1.5)

        await asyncio.sleep(2)

        second_btn = page.locator("#second-container-expand-button").first
        if await second_btn.is_visible():
            await second_btn.click()
            await asyncio.sleep(1.5)

        dp = page.locator("#datepicker-trigger").first
        print(f"Date text: '{await dp.inner_text()}'", flush=True)
        await dp.click()
        await asyncio.sleep(1.5)

        # Check calendar dialog
        cal_dialog = page.locator("ytcp-date-picker dialog, ytcp-date-picker, #dialog.ytcp-date-picker, tp-yt-paper-dialog").first
        print(f"Calendar visible: {await cal_dialog.is_visible()}", flush=True)
        if await cal_dialog.is_visible():
            inputs = await cal_dialog.locator("input").all()
            print(f"Inputs in calendar: {len(inputs)}", flush=True)
            for idx, inp in enumerate(inputs):
                print(f"Cal input {idx}: val='{await inp.input_value()}'", flush=True)

        # Also let's test time input:
        time_input = page.locator("#second-container input.tp-yt-paper-input").first
        print(f"Time input visible: {await time_input.is_visible()}", flush=True)
        if await time_input.is_visible():
            await time_input.click()
            await time_input.press("Control+A")
            await time_input.type("3:00 PM")
            await time_input.press("Enter")
            await asyncio.sleep(1)
            print(f"New Time value: '{await time_input.input_value()}'", flush=True)

        await page.screenshot(path="jarvis/tests/schedule_configured.png")
        print("Saved screenshot to jarvis/tests/schedule_configured.png", flush=True)

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
