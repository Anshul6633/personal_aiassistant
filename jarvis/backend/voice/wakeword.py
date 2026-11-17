"""Wake Word & Voice Activity Detection (VAD) Engine for JARVIS.

Monitors microphone audio input, streams RMS volume levels to the HUD waveform,
and triggers transcription when speech activity is detected.
"""

import time
import math
import asyncio
import logging
import threading
from typing import Callable, Optional, Any
import numpy as np

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except Exception as e:
    HAS_SOUNDDEVICE = False
    sd = None
    logger_init = logging.getLogger("JARVIS.WakeWord")
    logger_init.info(f"sounddevice not active (cloud/container mode): {e}")

from jarvis.backend.core.state import state_manager, AssistantState

logger = logging.getLogger("JARVIS.WakeWord")


class WakeWordListener:
    def __init__(self, sample_rate: int = 16000, chunk_duration_ms: int = 30):
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * (chunk_duration_ms / 1000.0))
        self.is_listening = False
        self._stream: Optional[Any] = None
        self._thread: Optional[threading.Thread] = None
        self.energy_threshold = 0.045
        self.on_speech_detected_callback: Optional[Callable] = None
        self.audio_buffer = []

    def _audio_callback(self, indata, frames, time_info, status):
        """Process incoming microphone audio frames."""
        if not self.is_listening:
            return

        # Calculate Root Mean Square (RMS) volume
        audio_chunk = indata[:, 0]
        rms = np.sqrt(np.mean(audio_chunk**2))
        normalized_level = min(1.0, float(rms * 15.0))

        # Push audio level to state manager for live waveform HUD
        state_manager.state.mic_level = round(normalized_level, 3)

        if rms > self.energy_threshold:
            self.audio_buffer.append(audio_chunk.copy())
        else:
            # Silence detected - if buffer has accumulated speech, trigger callback
            if len(self.audio_buffer) > int(self.sample_rate / self.chunk_size * 0.8):  # At least 0.8s
                speech_data = np.concatenate(self.audio_buffer)
                self.audio_buffer = []
                if self.on_speech_detected_callback:
                    self.on_speech_detected_callback(speech_data)
                else:
                    threading.Thread(target=self._handle_detected_speech, args=(speech_data,), daemon=True).start()
            elif len(self.audio_buffer) > 0 and len(self.audio_buffer) < 5:
                self.audio_buffer = []

    def _handle_detected_speech(self, speech_data: np.ndarray):
        """Default autonomous handler when speech is detected from the microphone."""
        try:
            import soundfile as sf
            from jarvis.backend.config.settings import OUTPUT_DIR
            from jarvis.backend.voice.stt import stt_engine
            from jarvis.backend.agents.buddy import jarvis_buddy
            from jarvis.backend.voice.tts import tts_engine

            audio_dir = OUTPUT_DIR / "audio"
            audio_dir.mkdir(parents=True, exist_ok=True)
            wav_path = str(audio_dir / f"mic_{int(time.time() * 1000)}.wav")
            sf.write(wav_path, speech_data, self.sample_rate)

            # Transcribe audio using faster-whisper
            res = stt_engine.transcribe_file(wav_path)
            raw_text = res.get("text", "").strip()
            if not raw_text or len(raw_text) < 2:
                return

            logger.info(f"Microphone speech recognized: '{raw_text}'")

            # Check for wake words or direct dialogue
            lower = raw_text.lower()
            wake_phrases = ["hey jarvis", "jarvis", "hello jarvis", "hi jarvis", "suno jarvis", "jarvis suno"]
            is_wake = any(w in lower for w in wake_phrases)

            # Strictly ignore ambient noise and chatter that does not address JARVIS
            if not is_wake:
                logger.info(f"Microphone speech without wake word ignored: '{raw_text}'")
                return

            # Instant Siri / Iron Man activation chime earcon
            try:
                import winsound
                winsound.Beep(1200, 50)
                winsound.Beep(1800, 70)
            except Exception:
                pass

            cleaned = raw_text
            for w in wake_phrases:
                cleaned = cleaned.lower().replace(w, "").strip()

            if not cleaned:
                cleaned = "Hello Jarvis, I'm online."

            # Process voice response
            async def process_voice():
                await state_manager.set_status(AssistantState.THINKING, f"Listening to: '{raw_text}'")
                await state_manager.broadcast({
                    "type": "USER_VOICE_PROMPT",
                    "data": {"text": raw_text, "timestamp": time.strftime("%I:%M %p")}
                })
                reply = await jarvis_buddy.generate_response(cleaned)
                await state_manager.set_status(AssistantState.SPEAKING, reply)
                audio_path = await tts_engine.synthesize(reply)
                audio_url = None
                if audio_path:
                    from pathlib import Path
                    audio_url = f"/output/audio/{Path(audio_path).name}"
                    tts_engine.play_audio(audio_path)
                await state_manager.broadcast({
                    "type": "ASSISTANT_REPLY",
                    "data": {
                        "text": reply,
                        "audio_url": audio_url,
                        "timestamp": time.strftime("%I:%M %p")
                    }
                })
                await state_manager.set_status(AssistantState.IDLE, "Systems nominal.")

            if state_manager._loop and state_manager._loop.is_running():
                asyncio.run_coroutine_threadsafe(process_voice(), state_manager._loop)
            else:
                asyncio.run(process_voice())

        except Exception as e:
            logger.error(f"Error handling detected microphone speech: {e}")

    def start_listening(self, callback: Optional[Callable] = None):
        """Start non-blocking microphone stream."""
        if self.is_listening:
            return

        if not HAS_SOUNDDEVICE or sd is None:
            logger.info("Microphone input bypassed in cloud/headless mode.")
            return

        self.on_speech_detected_callback = callback
        self.is_listening = True
        state_manager.state.mic_active = True

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=self.chunk_size,
                callback=self._audio_callback
            )
            self._stream.start()
            logger.info("Microphone listener started successfully.")
        except Exception as e:
            logger.error(f"Failed to start sounddevice microphone input: {e}")
            self.is_listening = False
            state_manager.state.mic_active = False

    def stop_listening(self):
        """Stop microphone stream."""
        self.is_listening = False
        state_manager.state.mic_active = False
        state_manager.state.mic_level = 0.0
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.warning(f"Error stopping audio stream: {e}")
            self._stream = None
        logger.info("Microphone listener stopped.")


wakeword_listener = WakeWordListener()

