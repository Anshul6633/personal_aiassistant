"""High-CTR 16:9 Long-Form YouTube Thumbnail Designer.

Engineered for 2026 YouTube Recommendation Algorithms:
- 1920x1080 Full HD Canvas with 16:9 aspect ratio.
- High-intensity Split-Action Composition: Streamer reaction on the left, gameplay clutch on the right.
- Zero Aspect Distortion: Dynamic crop-to-fill ensures 9:16 vertical sources seamlessly fill 16:9 panels.
- Laser Energy Divider: Neon electric cyan dividing beam with multi-layer glow down the center.
- 3D Impact Typography: 110pt yellow headline with 8px solid black stroke and 3D multi-layer shadow.
- Zero-Tofu Box Typography: Strictly sanitizes input text to eliminate missing emoji glyph boxes.
- Graphic Badges: Built-in vector-style red live dot + game tag, and cyan 4K 60FPS UNCUT pill.
- Cinematic Contrast & Saturation (+22% Contrast, +28% Saturation, +30% Sharpness).
"""

import os
import re
import math
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from jarvis.backend.config.settings import WORKSPACE_ROOT, OUTPUT_DIR

THUMBS_DIR = OUTPUT_DIR / "thumbnails"
THUMBS_DIR.mkdir(parents=True, exist_ok=True)


class LongformThumbnailDesigner:
    def __init__(self):
        self.font_impact = r"C:\Windows\Fonts\impact.ttf"
        self.font_arial_bd = r"C:\Windows\Fonts\arialbd.ttf"
        self.font_segoe = r"C:\Windows\Fonts\segoeuib.ttf"

    def _get_font(self, size: int, prefer_impact: bool = True) -> ImageFont.FreeTypeFont:
        """Load Impact or Arial Bold font."""
        candidates = [self.font_impact, self.font_arial_bd, self.font_segoe] if prefer_impact else [self.font_arial_bd, self.font_segoe]
        for c in candidates:
            if os.path.exists(c):
                try:
                    return ImageFont.truetype(c, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    @staticmethod
    def clean_text_for_font(text: str) -> str:
        """Sanitize text to guarantee crisp rendering without tofu box replacement glyphs."""
        if not text:
            return ""
        text = text.replace("•", "-").replace("·", "-").replace("🔥", "").replace("😱", "").replace("💀", "").replace("⚡", "").replace("🔴", "").replace("🚨", "").replace("🤯", "")
        # Strip all remaining non-ASCII characters
        clean = re.sub(r"[^\x20-\x7E]", "", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    @staticmethod
    def crop_to_fill(img: Image.Image, target_w: int, target_h: int, focus_y: float = 0.35) -> Image.Image:
        """Crop and resize an image to completely fill target dimensions with aspect ratio preserved."""
        iw, ih = img.size
        target_aspect = target_w / target_h
        current_aspect = iw / ih

        if current_aspect > target_aspect:
            new_w = int(ih * target_aspect)
            left = (iw - new_w) // 2
            crop_box = (left, 0, left + new_w, ih)
        else:
            new_h = int(iw / target_aspect)
            top = int(max(0, min(ih - new_h, (ih - new_h) * focus_y)))
            crop_box = (0, top, iw, top + new_h)

        cropped = img.crop(crop_box)
        return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

    def create_viral_thumbnail(
        self,
        base_frame_path: str,
        headline_text: str = "HE BROKE HIS SETUP?!",
        sub_text: str = "SPEED x TYPICAL GAMER",
        badge_text: str = "GTA 6",
        output_path: Optional[str] = None,
        secondary_frame_path: Optional[str] = None
    ) -> str:
        """Generate a studio-quality, high-CTR 1920x1080 thumbnail for YouTube long-form videos."""
        w, h = 1920, 1080
        out_file = Path(output_path) if output_path else (THUMBS_DIR / f"thumb_longform_{random.randint(1000, 9999)}.jpg")

        if not os.path.exists(base_frame_path):
            raise FileNotFoundError(f"Base frame not found: {base_frame_path}")

        canvas = Image.new("RGB", (w, h), (15, 15, 25))

        # 1. Image Composition (Split-Screen or Full-Frame Depth)
        if secondary_frame_path and os.path.exists(secondary_frame_path):
            with Image.open(base_frame_path) as b_img:
                b_rgb = b_img.convert("RGB")
                left_panel = self.crop_to_fill(b_rgb, 960, 1080, focus_y=0.25)
                canvas.paste(left_panel, (0, 0))

            with Image.open(secondary_frame_path) as s_img:
                s_rgb = s_img.convert("RGB")
                right_panel = self.crop_to_fill(s_rgb, 960, 1080, focus_y=0.45)
                canvas.paste(right_panel, (960, 0))

            # Neon laser dividing beam in the center
            draw_div = ImageDraw.Draw(canvas)
            for i in range(18, 0, -2):
                cyan_glow = (0, 240, 255)
                draw_div.line([(960 - i, 0), (960 - i, h)], fill=cyan_glow, width=1)
                draw_div.line([(960 + i, 0), (960 + i, h)], fill=cyan_glow, width=1)
            draw_div.line([(960, 0), (960, h)], fill=(255, 255, 255), width=4)
        else:
            with Image.open(base_frame_path) as b_img:
                b_rgb = b_img.convert("RGB")
                # 100% Full-bleed edge-to-edge 1920x1080 canvas (ZERO blurred sidebars)
                full_hero = self.crop_to_fill(b_rgb, w, h, focus_y=0.40)
                canvas.paste(full_hero, (0, 0))

        # 2. Viral Color & Contrast Grading (+22% Contrast, +28% Saturation, +30% Sharpness)
        canvas = ImageEnhance.Contrast(canvas).enhance(1.22)
        canvas = ImageEnhance.Color(canvas).enhance(1.28)
        canvas = ImageEnhance.Sharpness(canvas).enhance(1.30)

        # 3. Soft Bottom Gradient Darkness via Alpha Composite (ensures text readability while keeping background visible)
        grad_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(grad_overlay)
        for y_step in range(680, 1080, 4):
            alpha = int(((y_step - 680) / 400.0) ** 1.5 * 190)
            g_draw.line([(0, y_step), (w, y_step)], fill=(0, 0, 0, alpha), width=4)
        canvas = Image.alpha_composite(canvas.convert("RGBA"), grad_overlay).convert("RGB")
        draw = ImageDraw.Draw(canvas)

        # 4. Top Badges
        # Top-Left: Category Badge with glowing red dot
        badge_font = self._get_font(36, prefer_impact=True)
        clean_badge = self.clean_text_for_font(badge_text).upper() or "GTA 6"
        b_bbox = draw.textbbox((0, 0), clean_badge, font=badge_font)
        bw = b_bbox[2] - b_bbox[0] + 68
        bh = b_bbox[3] - b_bbox[1] + 20
        bx, by = 50, 45
        draw.rounded_rectangle([bx + 4, by + 4, bx + bw + 4, by + bh + 4], radius=10, fill=(0, 0, 0, 180))
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=10, fill=(220, 20, 20), outline=(255, 120, 120), width=3)
        dot_r = 8
        dot_cx = bx + 22
        dot_cy = by + (bh // 2)
        draw.ellipse([dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r], fill=(255, 255, 255))
        draw.text((bx + 44, by + 8), clean_badge, font=badge_font, fill=(255, 255, 255))

        # Top-Right: Quality Badge (4K 60FPS - UNCUT)
        q_font = self._get_font(34, prefer_impact=True)
        q_text = "4K 60FPS - UNCUT"
        q_bbox = draw.textbbox((0, 0), q_text, font=q_font)
        qw = q_bbox[2] - q_bbox[0] + 36
        qh = q_bbox[3] - q_bbox[1] + 18
        qx = w - qw - 50
        qy = 45
        draw.rounded_rectangle([qx + 4, qy + 4, qx + qw + 4, qy + qh + 4], radius=10, fill=(0, 0, 0, 180))
        draw.rounded_rectangle([qx, qy, qx + qw, qy + qh], radius=10, fill=(15, 20, 35), outline=(0, 240, 255), width=3)
        draw.text((qx + 18, qy + 8), q_text, font=q_font, fill=(0, 240, 255))

        # 5. Main 3D Viral Headline (Impact 110pt, Neon Yellow with thick stroke & shadow)
        clean_headline = self.clean_text_for_font(headline_text).upper().strip()
        main_font = self._get_font(110, prefer_impact=True)
        t_bbox = draw.textbbox((0, 0), clean_headline, font=main_font)
        tw = t_bbox[2] - t_bbox[0]
        th = t_bbox[3] - t_bbox[1]

        tx = (w - tw) // 2
        ty = h - th - 175

        pill_pad_x = 45
        pill_pad_y = 22
        draw.rounded_rectangle(
            [tx - pill_pad_x + 6, ty - pill_pad_y + 6, tx + tw + pill_pad_x + 6, ty + th + pill_pad_y + 6],
            radius=18,
            fill=(0, 0, 0, 230)
        )
        draw.rounded_rectangle(
            [tx - pill_pad_x, ty - pill_pad_y, tx + tw + pill_pad_x, ty + th + pill_pad_y],
            radius=18,
            fill=(10, 12, 22, 245),
            outline=(255, 220, 0),
            width=4
        )

        # Multi-layer 3D Shadow
        for s_off in range(12, 3, -1):
            draw.text((tx + s_off, ty + s_off), clean_headline, font=main_font, fill=(0, 0, 0))

        # 8px Solid Black Stroke
        for dx in range(-8, 9):
            for dy in range(-8, 9):
                if dx * dx + dy * dy <= 64:
                    draw.text((tx + dx, ty + dy), clean_headline, font=main_font, fill=(0, 0, 0))

        # Neon Yellow Fill
        draw.text((tx, ty), clean_headline, font=main_font, fill=(255, 235, 10))

        # 6. Secondary Sub-Headline / Streamer Duo Banner
        if sub_text:
            clean_sub = self.clean_text_for_font(sub_text).upper().strip()
            sub_font = self._get_font(52, prefer_impact=True)
            s_bbox = draw.textbbox((0, 0), clean_sub, font=sub_font)
            sw = s_bbox[2] - s_bbox[0]
            sh = s_bbox[3] - s_bbox[1]
            sx = (w - sw) // 2
            sy = ty + th + pill_pad_y + 20

            draw.rounded_rectangle(
                [sx - 26 + 4, sy - 10 + 4, sx + sw + 26 + 4, sy + sh + 12 + 4],
                radius=10,
                fill=(0, 0, 0, 200)
            )
            draw.rounded_rectangle(
                [sx - 26, sy - 10, sx + sw + 26, sy + sh + 12],
                radius=10,
                fill=(18, 24, 45, 240),
                outline=(0, 240, 255),
                width=3
            )
            for dx in [-3, -2, -1, 0, 1, 2, 3]:
                for dy in [-3, -2, -1, 0, 1, 2, 3]:
                    draw.text((sx + dx, sy + dy), clean_sub, font=sub_font, fill=(0, 0, 0))
            draw.text((sx, sy), clean_sub, font=sub_font, fill=(0, 240, 255))

        # Save with maximum JPEG quality (quality=96, subsampling=0)
        canvas.save(str(out_file), "JPEG", quality=96, subsampling=0)
        return str(out_file)


longform_thumbnail_designer = LongformThumbnailDesigner()
