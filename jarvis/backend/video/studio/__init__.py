"""JARVIS Embedded Video Studio package."""

from jarvis.backend.video.studio.models import (
    StudioProject,
    StudioTrack,
    StudioClip,
    ClipTransform,
    ClipFilters,
    ClipTextProps,
    ExportRequest,
    AIEditCommand,
)
from jarvis.backend.video.studio.project_manager import ProjectManager as StudioProjectManager, project_manager
from jarvis.backend.video.studio.timeline_engine import TimelineEngine
from jarvis.backend.video.studio.render_engine import StudioRenderEngine
from jarvis.backend.video.studio.ai_editor import AIVideoEditor

__all__ = [
    "StudioProject",
    "StudioTrack",
    "StudioClip",
    "ClipTransform",
    "ClipFilters",
    "ClipTextProps",
    "ExportRequest",
    "AIEditCommand",
    "StudioProjectManager",
    "project_manager",
    "TimelineEngine",
    "StudioRenderEngine",
    "AIVideoEditor",
]
