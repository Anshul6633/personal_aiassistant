"""Instagram Automated Stealth Authenticator & Session Saver.

Logs in with human-cadence typing, anti-detection flags, and persists authentication
cookies directly to jarvis/browser_profile so Instagram trusts the device indefinitely.
"""

import os
import sys
import time
import random
import asyncio
import logging
from pathlib import Path

# Ensure workspace root is in python path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from playwright.async_api import async_playwright
from jarvis.backend.config.settings import WORKSPACE_ROOT
from jarvis.backend.database.db import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("JARVIS.InstagramLogin")

PROFILE_DIR = WORKSPACE_ROOT / "jarvis" / "browser_profile"


def cleanup_profile_locks():
    """Ensure no stale lockfiles are in browser_profile."""
    for lock_name in ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket"]:
        try:
            (PROFILE_DIR / lock_name).unlink(missing_ok=True)
        except Exception:
            pass


async def human_type(locator, text: str):
    """Type text with randomized human keystroke cadence to prevent biometric bot flagging."""
    for ch in text:
        await locator.press_sequentially(ch)
        delay = random.uniform(0.065, 0.155)
        # Occasional slight pause between words or numbers
        if ch in " ._@1234567890":
            delay += random.uniform(0.05, 0.12)
        await asyncio.sleep(delay)


async def perform_stealth_login(username: str, password: str, max_wait_sec: int = 180) -> dict:
    """Execute human-cadence login with anti-ban stealth mechanisms."""
    logger.info("Initializing stealth login for account: %s", username)
    cleanup_profile_locks()
    await asyncio.sleep(1.0)

    async with async_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(PROFILE_DIR),
            "headless": False,
            "viewport": {"width": 1280, "height": 850},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--start-maximized",
                "--no-first-run",
                "--no-default-browser-check"
            ],
            "ignore_default_args": ["--enable-automation"]
        }

        try:
            context = await p.chromium.launch_persistent_context(**launch_kwargs, channel="chrome")
        except Exception:
            logger.info("Falling back to bundled Chromium engine...")
            context = await p.chromium.launch_persistent_context(**launch_kwargs)

        page = context.pages[0] if context.pages else await context.new_page()

        # Stealth evasion scripts
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.navigator.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)

        try:
            logger.info("Navigating to Instagram Login...")
            await page.goto("https://www.instagram.com/accounts/login/", timeout=45000, wait_until="domcontentloaded")
            await asyncio.sleep(3.0)

            # Check if already logged in from previous session
            if "login" not in page.url and (await page.locator("svg[aria-label='Home'], svg[aria-label='New post']").first.is_visible(timeout=3000)):
                logger.info("🎉 Already authenticated on Instagram!")
                await context.close()
                return {"success": True, "already_logged_in": True, "username": username}

            # Locate username / email / phone input
            user_input = page.locator("input[name='username'], input[name='email'], input[aria-label*='username' i], input[aria-label*='phone' i]").first
            await user_input.wait_for(state="visible", timeout=20000)
            await asyncio.sleep(random.uniform(0.8, 1.6))
            await user_input.click()
            await asyncio.sleep(0.3)

            # Clear and type username with human rhythm
            await user_input.fill("")
            await human_type(user_input, username)
            await asyncio.sleep(random.uniform(0.6, 1.2))

            # Locate password input
            pass_input = page.locator("input[name='password'], input[name='pass'], input[aria-label*='password' i]").first
            await pass_input.click()
            await asyncio.sleep(0.3)
            await pass_input.fill("")
            await human_type(pass_input, password)
            await asyncio.sleep(random.uniform(1.0, 2.0))

            # Click Log in button
            submit_btn = page.locator("button[type='submit'], input[type='submit'], div[role='button']:has-text('Log In'), div[role='button']:has-text('Log in'), button:has-text('Log in')").first
            logger.info("Credentials entered with human typing cadence. Submitting login...")
            await submit_btn.click()

            # Wait and snapshot
            await asyncio.sleep(4.0)
            post_submit_shot = WORKSPACE_ROOT / "jarvis" / "output" / "exports" / "instagram_after_submit.png"
            await page.screenshot(path=str(post_submit_shot))
            logger.info("Post-submit snapshot saved: %s", post_submit_shot)
            logger.info("Current URL: %s | Title: %s", page.url, await page.title())

            # Check for any alerts or errors on page
            for alert_sel in ["div[role='alert']", "#slfErrorAlert", "p[aria-atomic='true']", "span:has-text('incorrect')", "span:has-text('Sorry')"]:
                try:
                    el = page.locator(alert_sel).first
                    if await el.is_visible(timeout=500):
                        alert_txt = await el.inner_text()
                        logger.warning("Instagram Page Alert: %s", alert_txt)
                except Exception:
                    pass

            # Handle 1-time reCAPTCHA / Verification Challenge (Wait up to 10 minutes)
            logger.info("Monitoring for authorization completion or verification checkpoint...")
            logged_in = False
            recaptcha_notified = False

            for step in range(300):  # Wait up to 10 minutes (600 seconds)
                await asyncio.sleep(2.0)
                curr_url = page.url

                # Check if reCAPTCHA or Challenge checkpoint is active
                if "recaptcha" in curr_url or "challenge" in curr_url or "checkpoint" in curr_url:
                    if not recaptcha_notified:
                        logger.info("=" * 60)
                        logger.info("⚠️ INSTAGRAM reCAPTCHA VERIFICATION DETECTED!")
                        logger.info("Please solve the 'I'm not a robot' verification in the opened Chrome window.")
                        logger.info("Waiting for you to complete it on screen (timeout: 10 mins)...")
                        logger.info("=" * 60)
                        recaptcha_notified = True
                    continue

                # Check for Save login info prompt
                save_info_btn = page.locator("button:has-text('Save info'), button:has-text('Save Info'), div[role='button']:has-text('Save info')").first
                if await save_info_btn.is_visible(timeout=1000):
                    logger.info("Saving login info for persistent device trust...")
                    await save_info_btn.click()
                    await asyncio.sleep(2.0)
                    logged_in = True
                    break

                # Check for Not now / notification prompt
                not_now_btn = page.locator("button:has-text('Not Now'), button:has-text('Not now')").first
                if await not_now_btn.is_visible(timeout=1000):
                    logger.info("Dismissing notifications modal...")
                    await not_now_btn.click()
                    await asyncio.sleep(1.5)
                    logged_in = True
                    break

                # Check for home feed or create icon
                if "login" not in curr_url and "recaptcha" not in curr_url and (
                    await page.locator("svg[aria-label='Home'], svg[aria-label='New post'], svg[aria-label='Create']").first.is_visible(timeout=1000)
                ):
                    logged_in = True
                    break

                # Check for incorrect password notice
                err_el = page.locator("#slfErrorAlert, p[aria-atomic='true']").first
                if await err_el.is_visible(timeout=500):
                    err_text = await err_el.inner_text()
                    logger.error("Instagram login error: %s", err_text)
                    await context.close()
                    return {"success": False, "error": err_text}

            if logged_in:
                logger.info("🎉 SUCCESS: Logged in to Instagram as @%s!", username)
                # Ensure cookies write to disk cleanly
                await asyncio.sleep(3.0)
                await context.close()

                # Update database
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT OR REPLACE INTO social_accounts (platform, account_id, account_name, status, last_synced) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                    ("instagram", username, f"@{username}", "CONNECTED")
                )
                conn.commit()
                conn.close()

                return {
                    "success": True,
                    "username": username,
                    "message": f"Successfully signed in to Instagram as @{username}. Session cookies saved to browser_profile."
                }
            else:
                await context.close()
                return {
                    "success": False,
                    "error": "Login session timed out or security verification required."
                }

        except Exception as e:
            logger.error("Login process error: %s", e, exc_info=True)
            try:
                await context.close()
            except Exception:
                pass
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else "clipperwithout"
    pw = sys.argv[2] if len(sys.argv) > 2 else "akhatri@777"
    res = asyncio.run(perform_stealth_login(user, pw))
    print("\nRESULT:", res)
