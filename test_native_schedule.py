import sys
import logging
import asyncio
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
from jarvis.backend.social.youtube_browser import youtube_browser

async def main():
    print("[*] Testing native YouTube Studio schedule upload...", flush=True)
    test_video = Path("jarvis/tests/sample_podcast.mp4").resolve()
    res = await youtube_browser.upload_video(
        video_path=str(test_video),
        title="Epic Goal Moments 🔥 #Shorts",
        description="Best football edits from GHOST _OF_FOOTBALL.\n\n#Shorts #Football #Viral",
        privacy="schedule",
        schedule_time="3:00 AM",
        schedule_date="Nov 9, 2026",
        headless=False
    )
    print(f"[*] Result: {res}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())

