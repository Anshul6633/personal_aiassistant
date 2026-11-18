"""Smart High-CTR Thumbnail & Cover Extraction Engine.

Researched & engineered for 2026 YouTube Shorts & Instagram Reels algorithms:
- Samples candidate frames across key narrative inflection points (hook, action, climax).
- Multi-factor computer vision scoring: Edge Energy (sharpness), Dynamic Contrast,
  Luminance Balance, Color Vibrancy, and Hook Title Banner visibility.
- Applies viral visual enhancement (+18% contrast, +20% saturation, +25% sharpness)
  so covers pop against dark-mode mobile feeds and explore grids.
"""

import os
import shutil
import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image, ImageEnhance, ImageFilter, ImageStat

from jarvis.backend.config.settings import WORKSPACE_ROOT, OUTPUT_DIR

logger = logging.getLogger("JARVIS.SmartThumbnailGenerator")

THUMBS_DIR = OUTPUT_DIR / "thumbnails"
THUMBS_DIR.mkdir(parents=True, exist_ok=True)


class SmartThumbnailGenerator:
    """Intelligent thumbnail generator optimized for maximum CTR on vertical video platforms."""

    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg = ffmpeg_path or shutil.which("ffmpeg") or "ffmpeg"

    def get_video_duration(self, video_path: str) -> float:
        """Probe video duration via ffprobe or default to 20.0s."""
        ffprobe = shutil.which("ffprobe") or "ffprobe"
        cmd = [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(res.stdout.strip())
        except Exception:
            return 20.0

    def compute_frame_score(self, img: Image.Image) -> Tuple[float, Dict[str, float]]:
        """Score an individual candidate frame based on viral visual CTR signals.
        
        Metrics:
        1. Sharpness / Edge Energy (35%): Filters motion blur & camera shake.
        2. Luminance Balance (25%): Penalizes dark/murky (<50) and blown-out (>220) frames.
        3. Dynamic Contrast (20%): Standard deviation of luminance.
        4. Color Vibrancy (10%): Mean saturation in HSV space.
        5. Hook / Banner Presence (10%): Edge energy in the top 25% hook banner zone.
        """
        w, h = img.size
        gray = img.convert("L")
        stat_gray = ImageStat.Stat(gray)

        # 1. Edge Energy / Sharpness via Edge Filter
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edges)
        edge_mean = edge_stat.mean[0]  # 0 to 255. High = crisp details
        sharpness_score = min(edge_mean * 5.0, 100.0)

        # 2. Luminance balance (Ideal mean: 75 to 165)
        mean_lum = stat_gray.mean[0]
        if 75 <= mean_lum <= 165:
            lum_score = 100.0
        elif mean_lum < 75:
            # Penalize dark frames heavily
            lum_score = max(0.0, 100.0 - (75 - mean_lum) * 2.2)
        else:
            # Penalize overexposed frames
            lum_score = max(0.0, 100.0 - (mean_lum - 165) * 2.0)

        # 3. Dynamic Contrast (stddev of luminance)
        std_lum = stat_gray.stddev[0]
        contrast_score = min((std_lum / 64.0) * 100.0, 100.0)

        # 4. Color Vibrancy (Saturation in HSV)
        hsv = img.convert("HSV")
        _, s, _ = hsv.split()
        sat_mean = ImageStat.Stat(s).mean[0]
        vibrancy_score = min((sat_mean / 120.0) * 100.0, 100.0)

        # 5. Top Hook Banner Zone Check (top 22% of height)
        top_crop = gray.crop((0, 0, w, int(h * 0.22)))
        top_edges = top_crop.filter(ImageFilter.FIND_EDGES)
        top_edge_mean = ImageStat.Stat(top_edges).mean[0]
        banner_score = min(top_edge_mean * 6.0, 100.0)

        # Composite Weighted Total Score (0 - 100)
        total_score = (
            sharpness_score * 0.35 +
            lum_score * 0.25 +
            contrast_score * 0.20 +
            vibrancy_score * 0.10 +
            banner_score * 0.10
        )

        metrics = {
            "total": round(total_score, 2),
            "sharpness": round(sharpness_score, 1),
            "luminance": round(lum_score, 1),
            "contrast": round(contrast_score, 1),
            "vibrancy": round(vibrancy_score, 1),
            "banner": round(banner_score, 1),
            "mean_lum": round(mean_lum, 1)
        }
        return total_score, metrics

    def apply_viral_enhancements(self, img: Image.Image) -> Image.Image:
        """Apply color pop, contrast boost, and sharpness unsharp mask for mobile screens."""
        # 1. Boost dynamic contrast by 18%
        enh_con = ImageEnhance.Contrast(img)
        enhanced = enh_con.enhance(1.18)

        # 2. Boost color vibrancy / saturation by 20%
        enh_col = ImageEnhance.Color(enhanced)
        enhanced = enh_col.enhance(1.20)

        # 3. Boost sharpness and detail by 25%
        enh_shp = ImageEnhance.Sharpness(enhanced)
        enhanced = enh_shp.enhance(1.25)

        return enhanced

    def extract_smart_thumbnail(
        self,
        video_path: str,
        output_thumb_path: Optional[str] = None,
        candidate_timestamps: Optional[List[float]] = None
    ) -> str:
        """Extract the most visually appealing, high-CTR frame and apply viral polish.
        
        Args:
            video_path: Path to vertical 9:16 MP4 video.
            output_thumb_path: Where to save final enhanced JPEG. If None, auto-names in THUMBS_DIR.
            candidate_timestamps: Optional custom timestamp list to evaluate.
            
        Returns:
            Path string to saved thumbnail.
        """
        video_file = Path(video_path)
        if not video_file.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if not output_thumb_path:
            output_thumb_path = str(THUMBS_DIR / f"{video_file.stem}_thumb.jpg")

        duration = self.get_video_duration(video_path)

        # High-CTR candidate timeline sampling
        if not candidate_timestamps:
            # We sample:
            # - 0.6s & 1.2s: Hook banner fully visible + streamer reaction
            # - 2.5s: Hook climax
            # - 4.5s: First action beat
            # - 0.25 * duration: Quarter mark
            # - 0.50 * duration: Midpoint
            # - 0.70 * duration: Climax
            raw_candidates = [0.6, 1.2, 2.5, 4.5, duration * 0.25, duration * 0.50, duration * 0.70]
            candidate_timestamps = [t for t in raw_candidates if 0.1 <= t < duration - 0.5]

        if not candidate_timestamps:
            candidate_timestamps = [max(0.5, duration / 2.0)]

        temp_dir = video_file.parent / f"_thumb_tmp_{video_file.stem}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        best_score = -1.0
        best_img: Optional[Image.Image] = None
        best_time = candidate_timestamps[0]
        best_metrics: Dict[str, Any] = {}

        try:
            for idx, ts in enumerate(candidate_timestamps):
                tmp_frame = temp_dir / f"frame_{idx:02d}.jpg"
                cmd = [
                    self.ffmpeg,
                    "-y",
                    "-ss", f"{ts:.2f}",
                    "-i", str(video_file),
                    "-vframes", "1",
                    "-q:v", "2",
                    str(tmp_frame)
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                if tmp_frame.exists() and tmp_frame.stat().st_size > 1000:
                    try:
                        with Image.open(tmp_frame) as frame_img:
                            img_copy = frame_img.convert("RGB")
                            score, metrics = self.compute_frame_score(img_copy)
                            logger.debug(f"Frame @ {ts:.2f}s score: {score:.1f} | {metrics}")
                            if score > best_score:
                                best_score = score
                                best_time = ts
                                best_metrics = metrics
                                best_img = img_copy.copy()
                    except Exception as err:
                        logger.warning(f"Error evaluating candidate frame {tmp_frame}: {err}")

            if best_img is None:
                # Emergency fallback: extract midpoint directly
                mid_time = str(max(0.5, duration / 2.0))
                cmd = [
                    self.ffmpeg,
                    "-y",
                    "-ss", mid_time,
                    "-i", str(video_file),
                    "-vframes", "1",
                    "-q:v", "2",
                    output_thumb_path
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info(f"Fallback thumbnail generated at {mid_time}s for {video_file.name}")
                return output_thumb_path

            # Apply viral visual polish to the best selected frame
            enhanced_img = self.apply_viral_enhancements(best_img)

            # Ensure parent output directory exists
            Path(output_thumb_path).parent.mkdir(parents=True, exist_ok=True)

            # Save with high-fidelity JPEG compression
            enhanced_img.save(output_thumb_path, "JPEG", quality=95, subsampling=0)
            logger.info(
                f"Generated Smart Thumbnail for {video_file.name} @ {best_time:.2f}s | "
                f"Score: {best_score:.1f} (Sharpness: {best_metrics.get('sharpness')}, "
                f"Contrast: {best_metrics.get('contrast')}, Vibrancy: {best_metrics.get('vibrancy')}) -> {output_thumb_path}"
            )
            return output_thumb_path

        finally:
            # Clean up temporary frame directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass


# Global singleton instance
smart_thumbnail_generator = SmartThumbnailGenerator()
