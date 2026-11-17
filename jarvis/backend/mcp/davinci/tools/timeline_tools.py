"""
Timeline DaVinci Resolve MCP Tools for Project JARVIS.
Handles timeline creation, track management, markers, and title generators.
"""

from typing import Dict, Any, Optional
from jarvis.backend.mcp.davinci.connection import connection
from jarvis.backend.mcp.davinci.object_registry import registry


def get_active_timeline(timeline_id: Optional[str] = None):
    """Retrieve timeline object by ID or fallback to currently active project timeline."""
    if timeline_id:
        tl = registry.get(timeline_id)
        if tl:
            return tl

    resolve, _ = connection.connect()
    if not resolve:
        return None

    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject() if pm else None
    return proj.GetCurrentTimeline() if proj else None


def create_empty_timeline(name: str = "JARVIS Timeline") -> Dict[str, Any]:
    """Create a new empty timeline in the active project."""
    resolve, status = connection.connect()
    if not resolve:
        return {"success": False, "error": "DaVinci Resolve is offline.", "status": status}

    try:
        pm = resolve.GetProjectManager()
        project = pm.GetCurrentProject() if pm else None
        if not project:
            return {"success": False, "error": "No active project open."}

        mp = project.GetMediaPool()
        timeline = mp.CreateEmptyTimeline(name)
        if not timeline:
            return {"success": False, "error": f"Failed to create empty timeline '{name}'."}

        tl_id = registry.register(timeline, "Timeline", {"name": name})
        return {
            "success": True,
            "timeline_id": tl_id,
            "name": name,
            "message": f"Empty timeline '{name}' created."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_timeline_info(timeline_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve metadata and track counts for active timeline."""
    tl = get_active_timeline(timeline_id)
    if not tl:
        return {"success": False, "error": "No active timeline found or Resolve is offline."}

    try:
        name = tl.GetName()
        start_frame = tl.GetStartFrame()
        end_frame = tl.GetEndFrame()
        video_tracks = tl.GetTrackCount("video")
        audio_tracks = tl.GetTrackCount("audio")
        timecode = tl.GetCurrentTimecode() if hasattr(tl, "GetCurrentTimecode") else ""

        return {
            "success": True,
            "name": name,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "duration_frames": end_frame - start_frame if (start_frame and end_frame) else 0,
            "video_tracks": video_tracks,
            "audio_tracks": audio_tracks,
            "current_timecode": timecode
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def add_track(track_type: str = "video", timeline_id: Optional[str] = None) -> Dict[str, Any]:
    """Add a video, audio, or subtitle track to the timeline."""
    tl = get_active_timeline(timeline_id)
    if not tl:
        return {"success": False, "error": "No active timeline found or Resolve is offline."}

    clean_type = track_type.lower().strip()
    if clean_type not in ["video", "audio", "subtitle"]:
        return {"success": False, "error": "track_type must be 'video', 'audio', or 'subtitle'."}

    try:
        success = tl.AddTrack(clean_type)
        return {
            "success": bool(success),
            "track_type": clean_type,
            "message": f"Added new {clean_type} track to timeline '{tl.GetName()}'." if success else f"Failed to add {clean_type} track."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def add_marker(
    frame: int,
    color: str = "Blue",
    name: str = "JARVIS Marker",
    note: str = "",
    duration: int = 1,
    timeline_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add a chapter or note marker at a specific frame on the timeline."""
    tl = get_active_timeline(timeline_id)
    if not tl:
        return {"success": False, "error": "No active timeline found or Resolve is offline."}

    valid_colors = ["Blue", "Cyan", "Green", "Yellow", "Red", "Pink", "Purple", "Fuchsia", "Rose", "Lavender", "Sky", "Mint", "Lemon", "Sand", "Cocoa", "White"]
    marker_color = color.capitalize() if color.capitalize() in valid_colors else "Blue"

    try:
        success = tl.AddMarker(frame, marker_color, name, note, duration)
        return {
            "success": bool(success),
            "frame": frame,
            "color": marker_color,
            "name": name,
            "message": f"Marker '{name}' added at frame {frame}." if success else f"Failed to add marker at frame {frame}."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

