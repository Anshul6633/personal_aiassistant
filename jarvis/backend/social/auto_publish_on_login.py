import sys
import os
import time
import shutil
import sqlite3
import tempfile
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROFILE_DIR = WORKSPACE_ROOT / "jarvis" / "browser_profile"

def is_studio_authenticated():
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
        cur.execute("SELECT name FROM cookies WHERE host_key LIKE '%youtube%'")
        names = {r[0] for r in cur.fetchall()}
        conn.close()
        # Look for active YouTube session markers
        return "LOGIN_INFO" in names or "SAPISID" in names or "SID" in names
    except Exception:
        return False
    finally:
        try:
            Path(tmp_db).unlink(missing_ok=True)
        except Exception:
            pass

def launch_native_chrome():
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not Path(chrome_exe).exists():
        chrome_exe = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    
    print(f"[*] Launching Native Google Chrome with profile: {PROFILE_DIR}...")
    cmd = f'start "" "{chrome_exe}" --user-data-dir="{PROFILE_DIR}" "https://studio.youtube.com"'
    subprocess.Popen(cmd, shell=True)

if __name__ == "__main__":
    print("=" * 65)
    print("  JARVIS - YOUTUBE STUDIO SESSION LISTENER & AUTO-PUBLISHER")
    print("=" * 65)
    
    # Clean profile locks
    for lock in ["lockfile", "SingletonLock", "SingletonCookie", "SingletonSocket"]:
        try:
            (PROFILE_DIR / lock).unlink(missing_ok=True)
        except Exception:
            pass

    launch_native_chrome()
    print("[*] Chrome window opened! Complete sign-in to GHOST _OF_FOOTBALL.")
    print("[*] Waiting for active YouTube Studio session (up to 5 minutes)...")
    
    # Wait for session
    authenticated = False
    for i in range(150):
        time.sleep(2.0)
        # Check if Chrome is still running
        if is_studio_authenticated():
            # Wait another 2 seconds for cookies to sync to disk
            time.sleep(2.0)
            print("🎉 Authentication detected in browser profile!")
            authenticated = True
            break
            
    if authenticated:
        print("[*] Triggering automated morning short upload...")
        upload_script = WORKSPACE_ROOT / "jarvis" / "scratch" / "run_morning_short_upload.py"
        subprocess.run([sys.executable, str(upload_script)])
    else:
        print("[!] Timeout waiting for sign-in.")
