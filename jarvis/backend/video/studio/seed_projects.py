"""Seed Default Presets and Demo Projects for JARVIS Video Studio."""

import os
import time
from pathlib import Path
from jarvis.backend.video.studio.project_manager import ProjectManager
from jarvis.backend.video.studio.models import (
    StudioProject, StudioTrack, StudioClip, ClipTransform, ClipFilters, ClipTextProps
)
from jarvis.backend.config.settings import WORKSPACE_ROOT, OUTPUT_DIR

pm = ProjectManager()

def seed_default_studio_projects():
    # Check available video files
    reels_dir = OUTPUT_DIR / "reels"
    
    mrbeast_video = reels_dir / "clip_8207c7fa-4f9_mrbeast.mp4"
    if not mrbeast_video.exists():
        candidates = list(reels_dir.glob("*.mp4"))
        if candidates:
            mrbeast_video = candidates[0]
            
    cyber_video = reels_dir / "clip_8207c7fa-4f9_cyberpunk.mp4"
    if not cyber_video.exists():
        candidates = list(reels_dir.glob("*.mp4"))
        if candidates:
            cyber_video = candidates[-1]

    cinema_video = reels_dir / "clip_5f17a17f-84c_cinematic.mp4"
    if not cinema_video.exists():
        candidates = list(reels_dir.glob("*.mp4"))
        if candidates:
            cinema_video = candidates[0]

    # Project 1: Viral Instagram Reel (9:16)
    p1 = StudioProject(
        id="ig_reel_01",
        name="🔥 Viral Instagram Reel (9:16)",
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        fps=30,
        duration=15.0,
        tracks=pm.create_default_tracks(),
        clips=[
            StudioClip(
                id="c1_vid",
                track_id="V1",
                name="Prime Football Highlight",
                source_type="video",
                source_file=str(mrbeast_video),
                source_url=f"/output/reels/{mrbeast_video.name}",
                start_time=0.0,
                duration=15.0,
                in_point=0.0,
                out_point=15.0,
                speed=1.0,
                volume=1.0,
                transform=ClipTransform(),
                filters=ClipFilters(
                    brightness=0.08,
                    contrast=1.30,
                    saturation=1.35,
                    temperature=10.0,
                    tint=-5.0,
                    preset_name="Clarendon (Instagram)",
                    lift=-0.04,
                    gamma=1.08,
                    gain=1.12
                )
            ),
            StudioClip(
                id="c1_sub1",
                track_id="T1",
                name="Subtitle: MrBeast Yellow",
                source_type="text",
                start_time=0.5,
                duration=4.5,
                in_point=0.0,
                out_point=4.5,
                transform=ClipTransform(position_y=0.28),
                filters=ClipFilters(),
                text_props=ClipTextProps(
                    text="HE REALLY DID THAT?! 🔥",
                    font="Impact",
                    font_size=64,
                    color="#FFFF00",
                    highlight_color="#00FFFF",
                    outline_color="#000000",
                    outline_width=5,
                    alignment="center",
                    is_subtitle=True,
                    karaoke_mode=True
                )
            ),
            StudioClip(
                id="c1_sub2",
                track_id="T1",
                name="Subtitle: Hormozi Box",
                source_type="text",
                start_time=5.0,
                duration=5.0,
                in_point=0.0,
                out_point=5.0,
                transform=ClipTransform(position_y=0.28),
                filters=ClipFilters(),
                text_props=ClipTextProps(
                    text="ABSOLUTE GOAT MOMENT 👑",
                    font="Arial Black",
                    font_size=58,
                    color="#FFFFFF",
                    highlight_color="#FFFF00",
                    outline_color="#000000",
                    outline_width=2,
                    bg_color="#DC2626",
                    alignment="center",
                    is_subtitle=True
                )
            ),
            StudioClip(
                id="c1_stk1",
                track_id="T1",
                name="Sticker: Crown",
                source_type="sticker",
                start_time=1.0,
                duration=4.0,
                in_point=0.0,
                out_point=4.0,
                transform=ClipTransform(scale_x=1.8, scale_y=1.8, position_y=-0.35),
                filters=ClipFilters(),
                text_props=ClipTextProps(
                    text="👑",
                    font="Arial",
                    font_size=80,
                    color="#FFFFFF",
                    highlight_color="#FFFF00",
                    outline_color="#000000",
                    outline_width=0,
                    alignment="center",
                    is_subtitle=False,
                    sticker_emoji="👑",
                    animation="bounce"
                )
            ),
            StudioClip(
                id="c1_stk2",
                track_id="T1",
                name="Sticker: Fire",
                source_type="sticker",
                start_time=5.5,
                duration=4.0,
                in_point=0.0,
                out_point=4.0,
                transform=ClipTransform(scale_x=1.8, scale_y=1.8, position_y=-0.35),
                filters=ClipFilters(),
                text_props=ClipTextProps(
                    text="🔥",
                    font="Arial",
                    font_size=80,
                    color="#FFFFFF",
                    highlight_color="#FFFF00",
                    outline_color="#000000",
                    outline_width=0,
                    alignment="center",
                    is_subtitle=False,
                    sticker_emoji="🔥",
                    animation="pulse"
                )
            ),
            StudioClip(
                id="c1_sfx1",
                track_id="A1",
                name="SFX: Vine Boom",
                source_type="audio",
                start_time=0.5,
                duration=1.2,
                in_point=0.0,
                out_point=1.2,
                volume=1.0,
                transform=ClipTransform(),
                filters=ClipFilters()
            ),
            StudioClip(
                id="c1_sfx2",
                track_id="A1",
                name="SFX: Whoosh",
                source_type="audio",
                start_time=5.0,
                duration=0.4,
                in_point=0.0,
                out_point=0.4,
                volume=1.0,
                transform=ClipTransform(),
                filters=ClipFilters()
            )
        ]
    )
    pm.save_project(p1)

    # Project 2: Cyberpunk TikTok Master (9:16)
    p2 = StudioProject(
        id="cyber_tiktok_02",
        name="⚡ Cyberpunk Neon TikTok (9:16)",
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        fps=30,
        duration=12.0,
        tracks=pm.create_default_tracks(),
        clips=[
            StudioClip(
                id="c2_vid",
                track_id="V1",
                name="Cyberpunk High Energy Cut",
                source_type="video",
                source_file=str(cyber_video),
                source_url=f"/output/reels/{cyber_video.name}",
                start_time=0.0,
                duration=12.0,
                in_point=0.0,
                out_point=12.0,
                speed=1.0,
                volume=1.0,
                transform=ClipTransform(),
                filters=ClipFilters(
                    brightness=0.05,
                    contrast=1.35,
                    saturation=1.60,
                    temperature=-20.0,
                    tint=25.0,
                    vignette=0.20,
                    preset_name="Cyberpunk Neon",
                    lift=-0.05,
                    gamma=1.10,
                    gain=1.20
                )
            ),
            StudioClip(
                id="c2_sub",
                track_id="T1",
                name="Subtitle: Cyberpunk Neon",
                source_type="text",
                start_time=0.0,
                duration=6.0,
                in_point=0.0,
                out_point=6.0,
                transform=ClipTransform(position_y=0.25),
                filters=ClipFilters(),
                text_props=ClipTextProps(
                    text="GLITCH THE MATRIX ⚡",
                    font="Impact",
                    font_size=66,
                    color="#00FFFF",
                    highlight_color="#EC4899",
                    outline_color="#000000",
                    outline_width=4,
                    alignment="center",
                    is_subtitle=True
                )
            ),
            StudioClip(
                id="c2_stk",
                track_id="T1",
                name="Sticker: Lightning",
                source_type="sticker",
                start_time=0.5,
                duration=5.0,
                in_point=0.0,
                out_point=5.0,
                transform=ClipTransform(scale_x=2.0, scale_y=2.0, position_y=-0.3),
                filters=ClipFilters(),
                text_props=ClipTextProps(
                    text="⚡",
                    font="Arial",
                    font_size=88,
                    color="#FFFFFF",
                    highlight_color="#FFFF00",
                    outline_color="#000000",
                    outline_width=0,
                    alignment="center",
                    sticker_emoji="⚡",
                    animation="pulse"
                )
            )
        ]
    )
    pm.save_project(p2)

    # Project 3: DaVinci Cinematic 4K Showcase (16:9)
    p3 = StudioProject(
        id="davinci_cinema_03",
        name="🎬 DaVinci Cinematic 4K (16:9)",
        aspect_ratio="16:9",
        width=1920,
        height=1080,
        fps=30,
        duration=20.0,
        tracks=pm.create_default_tracks(),
        clips=[
            StudioClip(
                id="c3_vid",
                track_id="V1",
                name="Hollywood 35mm Graded Cut",
                source_type="video",
                source_file=str(cinema_video),
                source_url=f"/output/reels/{cinema_video.name}",
                start_time=0.0,
                duration=20.0,
                in_point=0.0,
                out_point=20.0,
                speed=1.0,
                volume=1.0,
                transform=ClipTransform(),
                filters=ClipFilters(
                    brightness=-0.02,
                    contrast=1.30,
                    saturation=1.25,
                    temperature=25.0,
                    tint=-15.0,
                    vignette=0.30,
                    preset_name="Teal & Orange (DaVinci)",
                    lift=-0.08,
                    gamma=1.05,
                    gain=1.15
                )
            ),
            StudioClip(
                id="c3_sub",
                track_id="T1",
                name="Title: Golden Serif",
                source_type="text",
                start_time=1.0,
                duration=6.0,
                in_point=0.0,
                out_point=6.0,
                transform=ClipTransform(position_y=0.32),
                filters=ClipFilters(),
                text_props=ClipTextProps(
                    text="CINEMATIC MASTERPIECE",
                    font="Georgia",
                    font_size=52,
                    color="#F59E0B",
                    highlight_color="#FDE68A",
                    outline_color="#000000",
                    outline_width=2,
                    alignment="center",
                    is_subtitle=True
                )
            )
        ]
    )
    pm.save_project(p3)

    print("Successfully seeded 3 rich preset studio projects!")

if __name__ == "__main__":
    seed_default_studio_projects()
