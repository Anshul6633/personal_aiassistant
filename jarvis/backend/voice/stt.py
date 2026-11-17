"""Speech-to-Text (STT) and Subtitle Generation Engine using faster-whisper.

Runs locally with GPU (CUDA) acceleration and automatic CPU fallback.
Generates word-level timestamps, segment boundaries, SRT, and VTT subtitles.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure HF Mirror endpoint to ensure reliable model downloads on Windows
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

try:
    from faster_whisper import WhisperModel
    HAS_WHISPER = True
except Exception as e:
    WhisperModel = None
    HAS_WHISPER = False
    logger_init = logging.getLogger("JARVIS.STT")
    logger_init.info(f"faster-whisper optional library not loaded: {e}")

from jarvis.backend.config.settings import settings

logger = logging.getLogger("JARVIS.STT")


class SpeechToTextEngine:
    def __init__(self):
        self.model_size = settings.WHISPER_MODEL_SIZE  # e.g. "small" or "base"
        self._model: Optional[Any] = None
        self.device = "cuda" if settings.WHISPER_DEVICE == "cuda" else "cpu"
        self.compute_type = settings.WHISPER_COMPUTE_TYPE

    def get_model(self) -> WhisperModel:
        """Lazy loader for WhisperModel to conserve VRAM until needed."""
        if self._model is None:
            try:
                logger.info(f"Loading faster-whisper model '{self.model_size}' on {self.device}...")
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type="float16" if self.device == "cuda" else "int8"
                )
            except Exception as e:
                logger.warning(f"CUDA faster-whisper loading failed ({e}). Falling back to CPU...")
                self.device = "cpu"
                self._model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8"
                )
        return self._model

    def transcribe_file(self, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe an audio or video file with word-level timestamps."""
        try:
            model = self.get_model()
            segments, info = model.transcribe(
                audio_path,
                language=language,
                word_timestamps=True,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            raw_segs = list(segments)
        except Exception as e:
            logger.warning(f"Whisper transcription failed on {self.device} ({e}). Falling back to CPU int8...")
            self.device = "cpu"
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8"
            )
            segments, info = self._model.transcribe(
                audio_path,
                language=language,
                word_timestamps=True,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            raw_segs = list(segments)

        segment_list = []
        all_words = []
        full_text = []

        for seg in raw_segs:
            seg_dict = {
                "id": seg.id,
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
                "words": []
            }
            if seg.words:
                for w in seg.words:
                    word_obj = {
                        "word": w.word.strip(),
                        "start": round(w.start, 2),
                        "end": round(w.end, 2),
                        "probability": round(w.probability, 2)
                    }
                    seg_dict["words"].append(word_obj)
                    all_words.append(word_obj)

            segment_list.append(seg_dict)
            full_text.append(seg.text.strip())

        return {
            "language": info.language,
            "language_probability": round(info.language_probability, 2),
            "duration": round(info.duration, 2),
            "text": " ".join(full_text),
            "segments": segment_list,
            "words": all_words
        }

    def generate_srt(self, segments: List[Dict[str, Any]], output_path: str) -> str:
        """Format segments into standard SRT subtitle format."""
        def format_time(seconds: float) -> str:
            millis = int((seconds - int(seconds)) * 1000)
            mins, secs = divmod(int(seconds), 60)
            hours, mins = divmod(mins, 60)
            return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

        lines = []
        for i, seg in enumerate(segments, 1):
            start = format_time(seg["start"])
            end = format_time(seg["end"])
            lines.append(f"{i}\n{start} --> {end}\n{seg['text']}\n")

        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    def generate_vtt(self, segments: List[Dict[str, Any]], output_path: str) -> str:
        """Format segments into WebVTT subtitle format."""
        def format_time(seconds: float) -> str:
            millis = int((seconds - int(seconds)) * 1000)
            mins, secs = divmod(int(seconds), 60)
            hours, mins = divmod(mins, 60)
            return f"{hours:02d}:{mins:02d}:{secs:02d}.{millis:03d}"

        lines = ["WEBVTT\n"]
        for i, seg in enumerate(segments, 1):
            start = format_time(seg["start"])
            end = format_time(seg["end"])
            lines.append(f"{i}\n{start} --> {end}\n{seg['text']}\n")

        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path


stt_engine = SpeechToTextEngine()
