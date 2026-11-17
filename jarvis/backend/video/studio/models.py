"""Data models for JARVIS Professional Video Studio."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
import time


class ClipTransform(BaseModel):
    scale_x: float = 1.0
    scale_y: float = 1.0
    position_x: float = 0.0  # Normalized offset (-1.0 to 1.0)
    position_y: float = 0.0
    rotation: float = 0.0    # Degrees
    flip_h: bool = False
    flip_v: bool = False
    opacity: float = 1.0


class ClipFilters(BaseModel):
    brightness: float = 0.0   # -1.0 to 1.0 (0 default)
    contrast: float = 1.0     # 0.0 to 3.0 (1 default)
    saturation: float = 1.0   # 0.0 to 3.0 (1 default)
    temperature: float = 0.0  # Warmth (-100 to 100)
    tint: float = 0.0         # Green/Magenta (-100 to 100)
    blur: float = 0.0         # 0.0 to 20.0
    sharpen: float = 0.0      # 0.0 to 5.0
    vignette: float = 0.0     # 0.0 to 1.0
    color_splash: bool = False  # Sin City / Subject color isolation (character colorful, background black & white)
    color_splash_x: float = 0.5  # Focus center X (0.0 to 1.0)
    color_splash_y: float = 0.5  # Focus center Y (0.0 to 1.0)
    color_splash_radius: float = 0.35  # Subject radius
    preset_name: Optional[str] = None
    lift: float = 0.0         # DaVinci Shadows Offset (-0.5 to 0.5)
    gamma: float = 1.0        # DaVinci Midtones Exposure (0.5 to 2.0)
    gain: float = 1.0         # DaVinci Highlights Level (0.5 to 2.0)
    transition: Optional[str] = None  # CapCut transition ("cross_dissolve", "zoom_in", "zoom_out", "flash_white", "glitch", "wipe_left")


class ClipTextProps(BaseModel):
    text: str = ""
    font: str = "Arial"
    font_size: int = 56
    color: str = "#FFFFFF"
    highlight_color: str = "#FFFF00"
    outline_color: str = "#000000"
    outline_width: int = 3
    bg_color: Optional[str] = None
    alignment: str = "center"  # "left", "center", "right"
    is_subtitle: bool = False
    karaoke_mode: bool = False


class StudioClip(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    track_id: str
    name: str
    source_type: str = "video"  # "video", "audio", "image", "text", "subtitle"
    source_file: Optional[str] = None
    source_url: Optional[str] = None
    start_time: float = 0.0     # Position on timeline (seconds)
    duration: float = 5.0       # Duration on timeline (seconds)
    in_point: float = 0.0       # Media source start trim (seconds)
    out_point: float = 5.0      # Media source end trim (seconds)
    speed: float = 1.0          # Playback speed (0.25 to 4.0)
    volume: float = 1.0         # 0.0 to 2.0
    fade_in: float = 0.0        # Seconds
    fade_out: float = 0.0       # Seconds
    transform: ClipTransform = Field(default_factory=ClipTransform)
    filters: ClipFilters = Field(default_factory=ClipFilters)
    text_props: Optional[ClipTextProps] = None


class StudioTrack(BaseModel):
    id: str
    name: str
    type: str  # "video", "audio", "text", "subtitle", "image"
    locked: bool = False
    muted: bool = False
    visible: bool = True
    volume: float = 1.0
    order: int = 0


class StudioProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Untitled Project"
    aspect_ratio: str = "16:9"  # "16:9", "9:16", "1:1"
    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration: float = 60.0
    tracks: List[StudioTrack] = []
    clips: List[StudioClip] = []
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    thumbnail_url: Optional[str] = None


class ExportRequest(BaseModel):
    project_id: str
    resolution: str = "1080p"      # "720p", "1080p", "1440p", "4K"
    aspect_ratio: str = "16:9"     # "16:9", "9:16", "1:1"
    codec: str = "h264"            # "h264", "hevc"
    fps: int = 30
    bitrate_kbps: int = 8000
    export_audio_only: bool = False


class AIEditCommand(BaseModel):
    project_id: str
    command: str
    selected_clip_id: Optional[str] = None
    playhead_time: Optional[float] = 0.0

