"""AI Viral Voiceover & Follower-Gaining Hook Engine.

Injects high-converting, retention-boosting AI voiceovers into YouTube Shorts and Instagram Reels:
1. 0.0s Climax Hook Voiceovers: Halts scrolling within 1.5s (e.g., 'Wait for the ending... you won't believe what happened!').
2. Mid-Video Retention Bridges: Keeps viewers engaged through the 5-second drop-off zone.
3. Follower & Share CTAs (Sends-Per-Reach Multipliers): Triggers direct shares and follows (e.g., 'Send this to that friend who drives like this!').
4. Audio Ducking: Seamlessly reduces background game/streamer audio by -7dB while the voiceover speaks.
"""

import os
import random
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from jarvis.backend.config.settings import settings, OUTPUT_DIR
from jarvis.backend.config.storage_router import storage_router
from jarvis.backend.voice.tts import tts_engine

logger = logging.getLogger("JARVIS.ViralVoiceover")

VOICEOVER_DIR = storage_router.get_output_dir("audio") / "voiceovers"
VOICEOVER_DIR.mkdir(parents=True, exist_ok=True)

# Curated Viral Voiceover Hook Presets
VIRAL_HOOKS = {
    "en": [
        "Wait for the ending... you won't believe what happened!",
        "Bro thought he was safe until THIS happened!",
        "Watch till the end... the biggest rage quit in gaming history!",
        "Is this the cleanest play ever, or pure luck?",
        "He had absolutely NO idea what was behind him!",
        "Wait for it... wait for it... oh my god!",
        "Never celebrate too early... watch what happens!",
        "This is why you never turn your back in this game!"
    ],
    "hi": [
        "Wait karo end ke liye... aage jo hua tum yakeen nahi karoge!",
        "Bhai ye kya ho gaya?! Aage dekho pura shock ho jaoge!",
        "End tak dekhna... aisi gaming pehle kabhi nahi dekhi hogi!",
        "Bro ne socha bach gaya... lekin aage kya hua dekho!",
        "Ye banda completely pagal ho gaya!",
        "Comment karke batao ye pro move tha ya pure luck!"
    ]
}

# Curated Follower & Sends-Per-Reach CTA Presets
VIRAL_CTAS = {
    "en": [
        "Send this to that friend who always plays like this!",
        "Hit follow right now if you want Part 2!",
        "Tag that friend who needs to see this right now!",
        "Subscribe right now or this happens to your gaming setup!",
        "Drop a comment below: Did he cook, or get cooked?"
    ],
    "hi": [
        "Apne us dost ko share karo jo aise game khelta hai!",
        "Follow karo abhi ke abhi... Part 2 ke liye!",
        "Subscribe karo warna tumhara agla game crash ho jayega!",
        "Comment karke batao... ye pro tha ya noobda?"
    ]
}


class ViralVoiceoverEngine:
    def __init__(self):
        self.ffmpeg = settings.FFMPEG_PATH
        self.ffprobe = settings.FFPROBE_PATH

    def get_audio_duration(self, audio_path: str) -> float:
        """Probe exact duration in seconds of synthesized audio."""
        try:
            cmd = [
                self.ffprobe,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path)
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(res.stdout.strip())
        except Exception as e:
            logger.warning(f"Failed to probe audio duration for {audio_path}: {e}")
            return 2.5

    async def generate_voiceover_audio(
        self,
        text: Optional[str] = None,
        voiceover_type: str = "hook",  # 'hook' or 'cta'
        language: str = "en"
    ) -> Dict[str, Any]:
        """Synthesize high-energy viral voiceover audio file."""
        if not text:
            if voiceover_type == "hook":
                text = random.choice(VIRAL_HOOKS.get(language, VIRAL_HOOKS["en"]))
            else:
                text = random.choice(VIRAL_CTAS.get(language, VIRAL_CTAS["en"]))

        import time
        filename = f"vo_{voiceover_type}_{int(time.time() * 1000)}.mp3"
        out_path = VOICEOVER_DIR / filename

        audio_file = await tts_engine.synthesize(text, output_filename=str(out_path.name))
        if not audio_file or not Path(audio_file).exists():
            return {"success": False, "error": "TTS synthesis failed"}

        duration = self.get_audio_duration(audio_file)
        return {
            "success": True,
            "text": text,
            "audio_path": str(audio_file),
            "duration": duration,
            "type": voiceover_type,
            "language": language
        }

    def generate_voiceover_sync(
        self,
        text: Optional[str] = None,
        voiceover_type: str = "hook",
        language: str = "en"
    ) -> Dict[str, Any]:
        """Synchronous wrapper for generating viral voiceovers inside video rendering threads."""
        try:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(lambda: asyncio.run(self.generate_voiceover_audio(text, voiceover_type, language)))
                return future.result(timeout=15.0)
        except Exception as e:
            logger.warning(f"Voiceover sync generation failed: {e}")
            return {"success": False, "error": str(e)}

    def overlay_voiceover_on_video(
        self,
        video_path: str,
        voiceover_audio_path: str,
        output_path: str,
        start_time: float = 0.0,
        duck_level_db: float = -7.0
    ) -> Dict[str, Any]:
        """Overlay synthesized voiceover onto a video with smart audio ducking.
        
        Ducks original video audio by `duck_level_db` while the voiceover is active,
        ensuring the hook or CTA is crystal clear and high-converting.
        """
        vo_path = Path(voiceover_audio_path)
        v_path = Path(video_path)

        if not vo_path.exists() or not v_path.exists():
            return {"success": False, "error": "Input video or audio does not exist"}

        vo_duration = self.get_audio_duration(str(vo_path))
        end_time = start_time + vo_duration

        # Audio filtergraph:
        # [0:a] volume ducked between start_time and end_time, then mixed with [1:a] delayed to start_time
        filter_complex = (
            f"[0:a]volume=enable='between(t,{start_time:.2f},{end_time:.2f})':volume='{duck_level_db}dB':eval=frame[ducked];"
            f"[1:a]adelay={int(start_time * 1000)}|{int(start_time * 1000)}[vo_delayed];"
            f"[ducked][vo_delayed]amix=inputs=2:duration=first:dropout_transition=1[outa]"
        )

        cmd = [
            self.ffmpeg,
            "-y",
            "-i", str(v_path),
            "-i", str(vo_path),
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[outa]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "256k",
            str(output_path)
        ]

        try:
            logger.info(f"🎙️ Applying viral voiceover overlay: {vo_path.name} at {start_time:.1f}s onto {v_path.name}")
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
            return {
                "success": True,
                "output_video": str(output_path),
                "voiceover_duration": vo_duration,
                "start_time": start_time
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg voiceover overlay failed: {e.stderr.decode('utf-8', errors='ignore') if e.stderr else e}")
            return {"success": False, "error": str(e)}


viral_voiceover_engine = ViralVoiceoverEngine()
