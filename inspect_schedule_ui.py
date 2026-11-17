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
        await asyncio.sleep(3)

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
        await title_box.wait_for(timeout=30000)

        not_kids = page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
        if await not_kids.is_visible():
            await not_kids.click(force=True)
            await asyncio.sleep(0.5)

        next_btn = page.locator("#next-button").first
        for i in range(3):
            await next_btn.click(force=True)
            await asyncio.sleep(1.5)

        await asyncio.sleep(2)
        print("[*] Dumping elements on Visibility step...", flush=True)

        # Dump all radio buttons
        radios = await page.locator("tp-yt-paper-radio-button, [role='radio']").all()
        print(f"Total radios found: {len(radios)}", flush=True)
        for idx, r in enumerate(radios):
            name = await r.get_attribute("name")
            rid = await r.get_attribute("id")
            txt = (await r.inner_text()).replace('\n', ' ').strip()
            print(f"Radio {idx}: name='{name}' id='{rid}' text='{txt}'", flush=True)

        # Also search for any element containing text 'Schedule'
        sched_matches = await page.locator("*:has-text('Schedule')").all()
        print(f"Elements containing 'Schedule': {len(sched_matches)}", flush=True)
        for idx, sm in enumerate(sched_matches[:10]):
            tag = await sm.evaluate("el => el.tagName")
            cid = await sm.get_attribute("id")
            ccls = await sm.get_attribute("class")
            print(f"Match {idx}: tag={tag} id={cid} class={ccls}", flush=True)

        # Take screenshot of visibility step
        await page.screenshot(path="jarvis/tests/visibility_step.png")
        print("[*] Saved screenshot to jarvis/tests/visibility_step.png", flush=True)

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
