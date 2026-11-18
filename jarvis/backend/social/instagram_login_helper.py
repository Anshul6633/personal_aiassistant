"""Interactive Instagram Login Window & Session Saver.

Runs in a visible Chrome / Chromium browser window with anti-detection enabled.
Persists authentication cookies and tokens to jarvis/browser_profile_instagram.
"""

import sys
import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("JARVIS.InstagramLoginHelper")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROFILE_DIR = WORKSPACE_ROOT / "jarvis" / "browser_profile_instagram"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)


def check_auth_cookies_present():
    """Quick check if Instagram authentication cookies have been written."""
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
        cur.execute("SELECT name FROM cookies WHERE host_key LIKE '%instagram.com%'")
        names = {r[0] for r in cur.fetchall()}
        conn.close()
        return "sessionid" in names and "ds_user_id" in names
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
                'powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \\"Name LIKE \'chrome%\'\\" | Where-Object {$_.CommandLine -like \'*browser_profile_instagram*\'} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"',
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
    print("      PROJECT JARVIS - INSTAGRAM AUTHENTICATION")
    print("=" * 65)
    print(f"[*] Persistent profile: {PROFILE_DIR}")
    print("[*] Ensuring profile is free of locks...")
    cleanup_profile_locks()
    print("[*] Launching browser window... Please sign into your Instagram Account.")
    print("=" * 65)

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
            logger.info(f"Chrome channel unavailable ({e}), falling back to bundled Chromium.")
            context = p.chromium.launch_persistent_context(**launch_kwargs)

        page = context.pages[0] if context.pages else context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        page.goto("https://www.instagram.com/accounts/login/")

        # Pre-fill credentials if inputs exist to save time
        try:
            page.wait_for_selector("input[name='username']", timeout=10000)
            page.fill("input[name='username']", "clipperwithout")
            page.fill("input[name='password']", "Akhatri@777")
        except Exception:
            pass

        print("[*] Waiting for user to complete Instagram authentication...")
        for _ in range(300):  # 10 minutes
            time.sleep(2)
            if check_auth_cookies_present():
                print("[SUCCESS] 🎉 Instagram authentication detected! Saving session...")
                # Update DB
                try:
                    from jarvis.backend.database.db import get_db_connection
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT OR REPLACE INTO social_accounts (platform, account_id, account_name, status, last_synced) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                        ("instagram", "clipperwithout", "@clipperwithout", "CONNECTED")
                    )
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
                time.sleep(3)
                context.close()
                return True

        context.close()
        return False


if __name__ == "__main__":
    success = run_login()
    sys.exit(0 if success else 1)
