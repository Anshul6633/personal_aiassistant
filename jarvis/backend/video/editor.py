"""Automated Video Editing, 9:16 Vertical Reframing, Subtitling & Audio Normalization.

Uses FFmpeg to create vertical YouTube Shorts & Instagram Reels with:
- 1080x1920 9:16 aspect ratio with blurred background stack or smart crop
- 6 Visual Subtitle Presets (Podcast, Motivational, Educational, Gaming, News, Cinematic)
- Dynamic karaoke-style keyword color highlighting (CapCut / Hormozi style)
- Intelligent pause trimming (silence removal)
- EBU R128 broadcast audio normalization
- High-res thumbnail generation
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.backend.config.settings import settings, OUTPUT_DIR

logger = logging.getLogger("JARVIS.Editor")

REELS_DIR = OUTPUT_DIR / "reels"
SHORTS_DIR = OUTPUT_DIR / "shorts"
THUMBS_DIR = OUTPUT_DIR / "thumbnails"
SUBS_DIR = OUTPUT_DIR / "subtitles"

# Keywords that trigger dynamic visual pop highlights in subtitles
EMPHASIS_KEYWORDS = {
    "secret", "mistake", "never", "always", "truth", "why", "stop", "ai",
    "money", "billion", "million", "crazy", "huge", "biggest", "rule",
    "future", "power", "warning", "free", "danger", "lesson", "win", "lose",
    # Gaming & Hindi Viral Triggers
    "gta", "gta6", "carry", "carryminati", "bhai", "yaar", "kya", "dekho",
    "kill", "police", "gun", "car", "headshot", "noob", "pro", "hack",
    "insane", "omg", "lol", "op", "epic", "bhaiya", "legend", "ps5", "game",
    "crore", "lakh", "loot", "dead", "fight", "escape", "run"
}

# The Visual Subtitle Presets (Format: Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, MarginV)
STYLE_PRESETS = {
    "podcast": {
        "name": "Hormozi Viral Pop",
        "tag": "Trending",
        "font": "Arial",
        "size": 72,
        "primary": "&H0000FFFF",  # Neon Yellow
        "secondary": "&H00FFFFFF",
        "outline_col": "&H00000000", # Black
        "back_col": "&H80000000",
        "bold": -1,
        "outline": 6,
        "shadow": 3,
        "margin_v": 540,
        "highlight_col": "&H0039FF14",  # Neon Lime
        "sample": "MAKE A MILLION TODAY",
        "desc": "Bold yellow dialogue with punchy neon lime keyword pops and thick black outline."
    },
    "mrbeast": {
        "name": "MrBeast High Impact",
        "tag": "High Energy",
        "font": "Impact",
        "size": 78,
        "primary": "&H00FFFF00",  # Electric Cyan
        "secondary": "&H0000FFFF",
        "outline_col": "&H00000000", # Heavy Black Outline
        "back_col": "&H00000000",
        "bold": -1,
        "outline": 8,
        "shadow": 4,
        "margin_v": 520,
        "highlight_col": "&H0000FFFF",  # Blazing Yellow
        "sample": "WIN $100,000 NOW!",
        "desc": "Oversized bold impact font in electric cyan with blazing yellow highlights and 8px stroke."
    },
    "cyberpunk": {
        "name": "Cyberpunk Neon",
        "tag": "Futuristic",
        "font": "Impact",
        "size": 72,
        "primary": "&H00FFFF00",  # Neon Aqua
        "secondary": "&H00FF00FF",
        "outline_col": "&H00FF00FF", # Hot Magenta Outline
        "back_col": "&H80100020",
        "bold": -1,
        "outline": 6,
        "shadow": 4,
        "margin_v": 540,
        "highlight_col": "&H0039FF14",  # Neon Lime
        "sample": "THE FUTURE IS HERE",
        "desc": "Futuristic neon cyan font glowing against a hot magenta stroke with lime accents."
    },
    "flame": {
        "name": "Arcade Flame",
        "tag": "Gaming",
        "font": "Impact",
        "size": 82,
        "primary": "&H00FFFFFF",  # Crisp Brilliant White for 100% legibility
        "secondary": "&H0000FFFF",
        "outline_col": "&H00000000", # Heavy Jet Black Outline
        "back_col": "&H00000000",
        "bold": -1,
        "outline": 8,
        "shadow": 4,
        "margin_v": 560,
        "highlight_col": "&H0000FFFF",  # Blazing Electric Yellow
        "sample": "SMASH IT OR LOSE IT",
        "desc": "High-intensity oversized Impact font in brilliant white with burning yellow keyword pops and 8px stroke."
    },
    "motivational": {
        "name": "Regal Gold",
        "tag": "Luxury",
        "font": "Georgia",
        "size": 66,
        "primary": "&H0024BFFB",  # Regal Gold
        "secondary": "&H00FFFFFF",
        "outline_col": "&H00000000",
        "back_col": "&HA0000000",
        "bold": -1,
        "outline": 5,
        "shadow": 4,
        "margin_v": 560,
        "highlight_col": "&H0000FFFF",  # Amber Yellow
        "sample": "MASTER YOUR MINDSET",
        "desc": "Elegant Georgia serif typography with luxury gold leaf and warm amber emphasis."
    },
    "educational": {
        "name": "Clean Modern",
        "tag": "Tutorial",
        "font": "Segoe UI",
        "size": 64,
        "primary": "&H00FFFFFF",  # Clean White
        "secondary": "&H00FFFF00", # Cyan
        "outline_col": "&H00000000",
        "back_col": "&H60000000",
        "bold": -1,
        "outline": 5,
        "shadow": 2,
        "margin_v": 520,
        "highlight_col": "&H00FFFF00",  # Electric Cyan
        "sample": "HOW THIS ACTUALLY WORKS",
        "desc": "Minimal tech and tutorial layout with pure white sans-serif and vibrant cyan cues."
    },
    "news": {
        "name": "Breaking News",
        "tag": "Broadcast",
        "font": "Arial",
        "size": 60,
        "primary": "&H00FFFFFF",  # Pure White
        "secondary": "&H00CCCCCC",
        "outline_col": "&H00000000",
        "back_col": "&H9000008B", # Dark Crimson Box
        "bold": -1,
        "outline": 4,
        "shadow": 2,
        "margin_v": 400,
        "highlight_col": "&H0000D7FF",  # Gold
        "sample": "BREAKING: SPECIAL REPORT",
        "desc": "Authoritative broadcast chyron bar with high-contrast text on crimson backing."
    },
    "cinematic": {
        "name": "Minimal Aesthetic",
        "tag": "Cinema",
        "font": "Helvetica",
        "size": 56,
        "primary": "&H00E2E8F0",  # Platinum
        "secondary": "&H0094A3B8",
        "outline_col": "&H00000000",
        "back_col": "&H40000000",
        "bold": 0,
        "outline": 3,
        "shadow": 2,
        "margin_v": 500,
        "highlight_col": "&H00FFFFFF",  # Pure White
        "sample": "a quiet observation",
        "desc": "Understated film festival aesthetic with subtle platinum typography and low opacity."
    }
}


class VideoEditor:
    def __init__(self):
        self.ffmpeg = settings.FFMPEG_PATH
        self.ffprobe = settings.FFPROBE_PATH

    def generate_ass_subtitles(
        self,
        words: List[Dict[str, Any]],
        clip_start: float,
        clip_end: float,
        output_ass_path: str,
        style: str = "podcast",
        crop_mode: Optional[str] = None
    ) -> str:
        """Generate styled Advanced SubStation Alpha (.ass) subtitles with keyword highlights and preset styling."""
        preset = STYLE_PRESETS.get(style.lower(), STYLE_PRESETS["podcast"]).copy()

        # Adapt subtitle vertical position dynamically based on layout structure
        margin_v = preset.get("margin_v", 540)
        if crop_mode in ("reversed_split", "reversed", "gameplay_top"):
            margin_v = 820  # Position in lower center of top gameplay section
        elif crop_mode in ("pip_cam", "pip_reaction", "pip"):
            margin_v = 580  # Position in lower third of full vertical action
        elif crop_mode in ("split_cam", "gaming", "streamer_face", "facecam"):
            margin_v = 540  # Centered over bottom gameplay section

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{preset['font']},{preset['size']},{preset['primary']},{preset['secondary']},{preset['outline_col']},{preset['back_col']},{preset['bold']},0,0,0,100,100,0,0,1,{preset['outline']},{preset['shadow']},2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        def format_ass_time(sec: float) -> str:
            rel_sec = max(0.0, sec - clip_start)
            hrs = int(rel_sec // 3600)
            mins = int((rel_sec % 3600) // 60)
            s = int(rel_sec % 60)
            cs = int((rel_sec - int(rel_sec)) * 100)
            return f"{hrs}:{mins:02d}:{s:02d}.{cs:02d}"

        clip_words = [w for w in words if w["start"] >= clip_start and w["end"] <= clip_end]
        if not clip_words:
            with open(output_ass_path, "w", encoding="utf-8") as f:
                f.write(header)
            return output_ass_path

        events = []
        chunk_size = 2  # Modern punchy 2-word cadence for max short-form retention
        highlight_color = preset.get("highlight_col", "&H0000FFFF")

        for i in range(0, len(clip_words), chunk_size):
            chunk = clip_words[i:i + chunk_size]
            t_start = format_ass_time(chunk[0]["start"])
            t_end = format_ass_time(chunk[-1]["end"])

            # Format words with keyword color override tags & energetic bounce animation
            chunk_tokens = []
            for w in chunk:
                raw_w = w["word"].strip()
                clean_w = raw_w.lower().strip(".,!?:;\"'()[]")
                if clean_w in EMPHASIS_KEYWORDS:
                    # Apply luminous keyword highlight with bold emphasis
                    chunk_tokens.append(f"{{\\c{highlight_color}&\\b1}}{raw_w.upper()}{{\\c{preset['primary']}&\\b{preset.get('bold', -1)}}}")
                else:
                    chunk_tokens.append(raw_w.upper())

            # Hormozi/CapCut signature pop animation (114% scale on entrance popping to 100% in 75ms)
            phrase = "{\\fscx114\\fscy114\\t(0,75,\\fscx100\\fscy100)}" + " ".join(chunk_tokens)
            events.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{phrase}")

        content = header + "\n".join(events)
        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_ass_path

    def render_vertical_clip(
        self,
        source_video: str,
        start_time: float,
        end_time: float,
        output_name: str,
        subtitles_ass: Optional[str] = None,
        trim_silence: bool = False,
        crop_mode: str = "fill"
    ) -> Dict[str, str]:
        """Cut video, re-frame to 1080x1920 (9:16), burn subtitles, and normalize audio.

        Args:
            crop_mode: 'fill' (full 9:16 edge-to-edge frame, NO background bars) or
                       'blur' (centered 16:9 box with blurred mirror background).
        """
        duration = end_time - start_time
        out_mp4 = str(REELS_DIR / f"{output_name}.mp4")
        out_thumb = str(THUMBS_DIR / f"{output_name}_thumb.jpg")

        if crop_mode == "blur":
            filter_complex = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,boxblur=25:5[bg];"
                "[0:v]scale=1080:-1:flags=lanczos,unsharp=3:3:0.6:3:3:0.0[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2[base]"
            )
        elif crop_mode in ("pip_cam", "pip_reaction", "pip"):
            # Structure B: Full 9:16 Action Gameplay with Floating Reaction Cam Badge
            filter_complex = (
                "[0:v]crop=608:1080:656:0,scale=1080:1920:flags=lanczos,unsharp=3:3:0.6:3:3:0.0[bg];"
                "[0:v]crop=370:250:15:435,scale=400:270:flags=lanczos,unsharp=5:5:0.8:5:5:0.0,drawbox=x=0:y=0:w=400:h=270:color=cyan@0.85:t=4[pip];"
                "[bg][pip]overlay=x=40:y=80[base]"
            )
        elif crop_mode in ("reversed_split", "reversed", "gameplay_top"):
            # Structure C: Gameplay Hero Top (60%) + Streamer Reaction Cam Bottom (40%)
            filter_complex = (
                "[0:v]crop=1300:1080:550:0,scale=1080:1180:flags=lanczos,unsharp=3:3:0.6:3:3:0.0[game];"
                "[0:v]crop=370:250:15:435,scale=1080:740:flags=lanczos,unsharp=5:5:0.8:5:5:0.0[cam];"
                "[game][cam]vstack[vst];"
                "[vst]drawbox=x=0:y=1178:w=1080:h=4:color=magenta@0.85:t=fill[base]"
            )
        elif crop_mode in ("split_cam", "gaming", "streamer_face", "facecam"):
            # Structure A: Streamer Facecam Top (40%) + Gameplay Action Bottom (60%)
            filter_complex = (
                "[0:v]crop=370:250:15:435,scale=1080:740:flags=lanczos,unsharp=5:5:0.8:5:5:0.0[cam];"
                "[0:v]crop=1300:1080:550:0,scale=1080:1180:flags=lanczos,unsharp=3:3:0.6:3:3:0.0[game];"
                "[cam][game]vstack[vst];"
                "[vst]drawbox=x=0:y=738:w=1080:h=4:color=cyan@0.85:t=fill[base]"
            )
        else:
            # Full 9:16 edge-to-edge frame fill (NO background bars, 100% immersive) with Lanczos + Unsharp
            filter_complex = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,unsharp=3:3:0.6:3:3:0.0[base]"

        final_video_label = "[base]"
        if subtitles_ass and Path(subtitles_ass).exists():
            escaped_sub = str(Path(subtitles_ass).resolve()).replace("\\", "/").replace(":", "\\:")
            filter_complex += f";[base]ass='{escaped_sub}'[outv]"
            final_video_label = "[outv]"

        audio_filter = "loudnorm=I=-16:TP=-1.5:LRA=11"
        if trim_silence:
            audio_filter = "silenceremove=stop_periods=-1:stop_duration=1.2:stop_threshold=-35dB," + audio_filter

        cmd = [
            self.ffmpeg,
            "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", source_video,
            "-filter_complex", filter_complex,
            "-map", final_video_label,
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "17",
            "-maxrate", "14M",
            "-bufsize", "28M",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "256k",
            "-af", audio_filter,
            out_mp4
        ]

        logger.info(f"Rendering vertical clip {output_name} ({duration}s)...")
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.error(f"FFmpeg render error: {res.stderr}")
            # Fallback direct crop
            simple_cmd = [
                self.ffmpeg, "-y",
                "-ss", str(start_time),
                "-t", str(duration),
                "-i", source_video,
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac",
                out_mp4
            ]
            subprocess.run(simple_cmd, check=True)

        # Generate thumbnail at midpoint
        thumb_time = str(duration / 2.0)
        thumb_cmd = [
            self.ffmpeg,
            "-y",
            "-ss", thumb_time,
            "-i", out_mp4,
            "-vframes", "1",
            "-q:v", "2",
            out_thumb
        ]
        subprocess.run(thumb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return {
            "video_path": out_mp4,
            "thumbnail_path": out_thumb,
            "duration": duration
        }

    def restyle_ass_file(
        self,
        input_ass_path: str,
        output_ass_path: str,
        new_style: str
    ) -> str:
        """Restyle an existing .ass subtitle file with a new preset."""
        import re
        preset = STYLE_PRESETS.get(new_style.lower(), STYLE_PRESETS["podcast"])
        new_style_line = (
            f"Style: Default,{preset['font']},{preset['size']},{preset['primary']},"
            f"{preset['secondary']},{preset['outline_col']},{preset['back_col']},"
            f"{preset['bold']},0,0,0,100,100,0,0,1,{preset['outline']},{preset['shadow']},"
            f"2,60,60,{preset['margin_v']},1"
        )
        highlight_color = preset.get("highlight_col", "&H0000FFFF")
        primary_color = preset.get("primary", "&H00FFFFFF")

        if not Path(input_ass_path).exists():
            raise FileNotFoundError(f"Source subtitle not found: {input_ass_path}")

        with open(input_ass_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            if line.startswith("Style: Default,"):
                new_lines.append(new_style_line + "\n")
            elif line.startswith("Dialogue:"):
                # Replace highlight color tags {\c&H...&}(WORD){\c&H...&}
                sub_line = re.sub(
                    r"\{\\c&H[0-9a-fA-F]+&\}(.*?)\{\\c&H[0-9a-fA-F]+&\}",
                    lambda m: f"{{\\c{highlight_color}&}}{m.group(1)}{{\\c{primary_color}&}}",
                    line
                )
                new_lines.append(sub_line)
            else:
                new_lines.append(line)

        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return output_ass_path

    @staticmethod
    def get_caption_styles() -> List[Dict[str, Any]]:
        """Return full catalog of visual caption styles with preview metadata."""
        catalog = []
        for sid, p in STYLE_PRESETS.items():
            def ass_to_hex(ass_col: str) -> str:
                clean = ass_col.replace("&H", "").replace("&", "").zfill(8)
                bb = clean[2:4]
                gg = clean[4:6]
                rr = clean[6:8]
                return f"#{rr}{gg}{bb}"

            catalog.append({
                "id": sid,
                "name": p.get("name", sid.capitalize()),
                "tag": p.get("tag", "Popular"),
                "font": p.get("font", "Arial"),
                "primary_color": ass_to_hex(p["primary"]),
                "highlight_color": ass_to_hex(p.get("highlight_col", "&H0000FFFF")),
                "outline_color": ass_to_hex(p.get("outline_col", "&H00000000")),
                "sample": p.get("sample", "MAKE IT VIRAL"),
                "desc": p.get("desc", ""),
                "size": p.get("size", 68)
            })
        return catalog


video_editor = VideoEditor()
