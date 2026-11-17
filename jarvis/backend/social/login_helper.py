"""Interactive Google / YouTube Studio Login Window.

Runs in a visible Chrome / Chromium browser window with anti-detection enabled.
Persists authentication cookies and tokens to jarvis/browser_profile.
"""

import sys
import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("JARVIS.LoginHelper")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROFILE_DIR = WORKSPACE_ROOT / "jarvis" / "browser_profile"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)


def check_auth_cookies_present():
    """Quick check if authentication cookies have been written."""
    import sqlite3
    import shutil
    import tempfile

    cookies_db = PROFILE_DIR / "Default" / "Network" / "Cookies"
    if not cookies_db.exists():
        cookies_db = PROFILE_DIR / "Default" / "Cookies"
    if not cookies_db.exists():
        return False

    tmp_db = tempfile.mktemp(suffix=".sqlite")
    try:
        shutil.copy2(cookies_db, tmp_db)
        conn = sqlite3.connect(tmp_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM cookies WHERE host_key LIKE '%youtube%' OR host_key LIKE '%google%'")
        names = {r[0] for r in cur.fetchall()}
        conn.close()
        return any(c in names for c in ["LOGIN_INFO", "SSID", "SAPISID", "SID", "APISID", "__Secure-3PSID"])
    except Exception:
        return False
    finally:
        try:
            Path(tmp_db).unlink(missing_ok=True)
        except Exception:
            pass


def cleanup_profile_locks():
    """Terminate any lingering Chrome processes using this profile and clear lockfiles."""
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


def run_login():
    print("=" * 65)
    print("      PROJECT JARVIS - YOUTUBE STUDIO AUTHENTICATION")
    print("=" * 65)
    print(f"[*] Persistent profile: {PROFILE_DIR}")
    print("[*] Ensuring profile is free of locks...")
    cleanup_profile_locks()
    print("[*] Launching browser window... Please sign into your Google Account.")
    print("=" * 65)

    with sync_playwright() as p:
        # Prefer installed Google Chrome for seamless Google trust, fallback to Chromium
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
            logger.info(f"Chrome channel unavailable ({e}), falling back to bundled Chromium.")
            context = p.chromium.launch_persistent_context(**launch_kwargs)
            print("[INFO] Launched with Chromium.")

        page = context.pages[0] if context.pages else context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        try:
            page.goto("https://studio.youtube.com", timeout=45000)
        except Exception as e:
            print(f"[WARN] Initial page load notice: {e}")

        print("\n[INFO] Browser window is active!")
        print("[INFO] Complete your sign-in inside the browser window.")
        print("[INFO] Waiting for YouTube Studio dashboard to open (timeout: 10 minutes)...\n")

        # Poll every 2 seconds
        logged_in = False
        channel_name = "Your Channel"

        for step in range(300): # 10 minutes maximum
            time.sleep(2.0)

            # Check if browser was closed by user
            try:
                if not context.pages:
                    print("\n[*] Browser was closed.")
                    break
            except Exception:
                break

            try:
                curr_url = page.url
            except Exception:
                continue

            # Check if reached studio dashboard or cookies written
            is_studio_url = "studio.youtube.com" in curr_url and "accounts.google.com" not in curr_url and "signin" not in curr_url
            has_cookies = (step % 5 == 0) and check_auth_cookies_present()

            if is_studio_url or ("channel" in curr_url and "studio.youtube.com" in curr_url) or has_cookies:
                try:
                    title_el = page.query_selector("#channel-title, [id='channel-name']")
                    if title_el:
                        channel_name = title_el.inner_text().strip()
                except Exception:
                    pass

                logged_in = True
                print("\n" + "=" * 65)
                print(f"🎉 SUCCESS! Logged into YouTube Studio: {channel_name}")
                print("Session cookies and credentials saved to jarvis/browser_profile.")
                print("Closing in 4 seconds...")
                print("=" * 65)
                time.sleep(4.0)
                break

        try:
            context.close()
        except Exception:
            pass

        print("[*] Authentication session complete.")
        if logged_in:
            print("[OK] You can now return to the JARVIS dashboard and upload Shorts!")
        else:
            print("[NOTICE] Sign-in was not completed or window was closed.")


if __name__ == "__main__":
    run_login()
