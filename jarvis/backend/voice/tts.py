"""Dual-Engine Text-to-Speech (TTS) Engine for JARVIS.

Supports:
1. edge-tts: Ultra-natural Paul Bettany/JARVIS-style neural voices (Zero cost, no API key).
2. pyttsx3: 100% offline fallback using Windows SAPI5 voice engine.
"""

import os
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional
import edge_tts
try:
    import pyttsx3
    HAS_PYTTSX3 = True
except Exception as e:
    HAS_PYTTSX3 = False
    pyttsx3 = None
from jarvis.backend.config.settings import OUTPUT_DIR, settings

logger = logging.getLogger("JARVIS.TTS")

AUDIO_OUT_DIR = OUTPUT_DIR / "audio"
AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)


import re

import threading

_sapi_lock = threading.Lock()

def clean_speech_text(text: str) -> str:
    """Clean markdown artifacts and formatting symbols so spoken voice sounds natural."""
    if not text:
        return ""
    # Remove markdown symbols, bold, italics, headers, code backticks
    cleaned = re.sub(r'[*_~`#]', '', text)
    # Replace markdown links [text](url) with just text
    cleaned = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', cleaned)
    # Remove bullet points
    cleaned = re.sub(r'^\s*[-+*]\s+', '', cleaned, flags=re.MULTILINE)
    # Collapse excess spaces/newlines
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


class TextToSpeechEngine:
    def __init__(self):
        self.default_voice = settings.DEFAULT_VOICE  # en-US-ChristopherNeural
        self.hindi_voice = settings.HINDI_VOICE      # hi-IN-MadhurNeural
        self.marathi_voice = "mr-IN-AarohiNeural"
        self._is_speaking = False
        self._current_task: Optional[asyncio.Task] = None
        self._playback_process: Optional[subprocess.Popen] = None
        self._edge_tts_offline_until: float = 0.0
        self.offline_mode: bool = True  # Native Windows SAPI5 voice for instant <0.1s synthesis & zero cost

    def play_audio(self, audio_path: str, block: bool = False):
        """Play synthesized audio file locally on the computer's speakers."""
        if not audio_path or not Path(audio_path).exists():
            return

        self._is_speaking = True
        ffplay = settings.FFPLAY_PATH
        cmd = [ffplay, "-nodisp", "-autoexit", "-loglevel", "quiet", str(audio_path)]
        try:
            if block:
                subprocess.run(cmd, check=True)
                self._is_speaking = False
            else:
                self._playback_process = subprocess.Popen(cmd)
        except Exception as e:
            logger.warning(f"ffplay local playback failed: {e}")
            self._is_speaking = False

    def stop_speaking(self):
        """Immediately interrupt and abort any in-progress speech playback."""
        self._is_speaking = False
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
        if self._playback_process:
            try:
                self._playback_process.terminate()
            except Exception:
                pass
            self._playback_process = None
        logger.info("Speech playback interrupted by user/barge-in.")

    def detect_language(self, text: str) -> str:
        """Heuristic check for Devanagari script (Hindi/Marathi)."""
        has_devanagari = any('\u0900' <= char <= '\u097F' for char in text)
        return "hi" if has_devanagari else "en"

    def select_voice(self, text: str) -> str:
        lang = self.detect_language(text)
        if lang == "hi":
            return self.hindi_voice
        return self.default_voice

    async def synthesize(self, text: str, output_filename: Optional[str] = None) -> Optional[str]:
        """Synthesize text to MP3 using edge-tts with automatic pyttsx3 fallback.
        
        Returns the local file path to the audio file.
        """
        if not text or not text.strip():
            return None

        spoken_text = clean_speech_text(text)
        if not spoken_text:
            return None

        if not output_filename:
            import time
            output_filename = f"speech_{int(time.time() * 1000)}.mp3"

        out_path = AUDIO_OUT_DIR / output_filename
        voice = self.select_voice(spoken_text)

        import time
        wav_path = out_path.with_suffix(".wav")

        def _synthesize_offline():
            with _sapi_lock:
                co_init = False
                try:
                    import pythoncom
                    import win32com.client
                    pythoncom.CoInitialize()
                    co_init = True
                    voice_obj = win32com.client.Dispatch("SAPI.SpVoice")
                    stream = win32com.client.Dispatch("SAPI.SpFileStream")
                    # 3 = SSFMCreateForWrite
                    stream.Open(str(wav_path), 3)
                    voice_obj.Rate = 1
                    voice_obj.Volume = 95
                    voice_obj.AudioOutputStream = stream
                    voice_obj.Speak(spoken_text)
                    stream.Close()
                    del voice_obj, stream
                    return str(wav_path)
                except Exception as ex:
                    logger.error(f"Native SAPI synthesis error: {ex}")
                    try:
                        eng = pyttsx3.init()
                        eng.save_to_file(spoken_text, str(wav_path))
                        eng.runAndWait()
                        del eng
                        return str(wav_path)
                    except Exception as ex2:
                        logger.error(f"pyttsx3 fallback error: {ex2}")
                        return None
                finally:
                    if co_init:
                        try:
                            import pythoncom
                            pythoncom.CoUninitialize()
                        except Exception:
                            pass

        # Zero paid API cost & 100% offline reliability:
        if self.offline_mode or time.time() < self._edge_tts_offline_until:
            try:
                return await asyncio.wait_for(asyncio.to_thread(_synthesize_offline), timeout=12.0)
            except Exception as e:
                logger.error(f"Offline TTS timeout or failure: {e}")
                return None

        try:
            # Try edge-tts for high-fidelity neural voice with strict 2.5s timeout
            communicate = edge_tts.Communicate(
                text=spoken_text,
                voice=voice,
                rate=settings.TTS_RATE,
                pitch=settings.TTS_PITCH
            )
            await asyncio.wait_for(communicate.save(str(out_path)), timeout=2.5)
            return str(out_path)
        except Exception as e:
            # Backoff edge-tts for 24 hours so subsequent speech is instant and 100% offline
            self._edge_tts_offline_until = time.time() + 86400
            logger.info(f"edge-tts unavailable ({e}); switching to instant offline speech")
            try:
                return await asyncio.wait_for(asyncio.to_thread(_synthesize_offline), timeout=8.0)
            except Exception as e2:
                logger.error(f"Fallback offline TTS failed: {e2}")
                return None


tts_engine = TextToSpeechEngine()

