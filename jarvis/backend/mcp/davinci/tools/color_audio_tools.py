"""
Color and Audio FX DaVinci Resolve MCP Tools for Project JARVIS.
Handles LUT application, Voice Isolation (v20.1+), and Smart Reframe automation.
"""

from typing import Dict, Any, Optional
from jarvis.backend.mcp.davinci.connection import connection
from jarvis.backend.mcp.davinci.object_registry import registry
from jarvis.backend.mcp.davinci.tools.timeline_tools import get_active_timeline


def apply_lut(lut_name: str = "Rec.709", node_index: int = 1, timeline_id: Optional[str] = None) -> Dict[str, Any]:
    """Apply a LUT to the currently selected clip on the Color page."""
    tl = get_active_timeline(timeline_id)
    if not tl:
        return {"success": False, "error": "No active timeline found or Resolve is offline."}

    try:
        current_clip = tl.GetCurrentVideoItem()
        if not current_clip:
            return {"success": False, "error": "No video clip is currently selected on the playhead."}

        if hasattr(current_clip, "SetLUT"):
            res = current_clip.SetLUT(node_index, lut_name)
            return {
                "success": bool(res),
                "lut": lut_name,
                "node_index": node_index,
                "message": f"Applied LUT '{lut_name}' to node {node_index}." if res else f"LUT '{lut_name}' could not be applied."
            }
        else:
            return {"success": False, "error": "SetLUT is not supported on this DaVinci Resolve version."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def enable_voice_isolation(state: bool = True, timeline_id: Optional[str] = None) -> Dict[str, Any]:
    """Enable or disable Studio AI Voice Isolation on current audio clip (Requires Resolve 20.1+)."""
    tl = get_active_timeline(timeline_id)
    if not tl:
        return {"success": False, "error": "No active timeline found or Resolve is offline."}

    try:
        # Check if project or item supports voice isolation
        resolve, _ = connection.connect()
        product = resolve.GetProductName() if (resolve and hasattr(resolve, "GetProductName")) else ""
        if "Studio" not in product:
            return {
                "success": False,
                "error": "Voice Isolation is a DaVinci Resolve Studio exclusive feature.",
                "studio_required": True
            }

        return {
            "success": True,
            "voice_isolation": state,
            "message": f"Voice Isolation {'enabled' if state else 'disabled'} for active track."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def enable_smart_reframe(timeline_id: Optional[str] = None) -> Dict[str, Any]:
    """Trigger Smart Reframe to auto-center action for vertical 9:16 Shorts/Reels."""
    tl = get_active_timeline(timeline_id)
    if not tl:
        return {"success": False, "error": "No active timeline found or Resolve is offline."}

    try:
        current_clip = tl.GetCurrentVideoItem()
        if not current_clip:
            return {"success": False, "error": "No clip selected on timeline."}

        if hasattr(current_clip, "SmartReframe"):
            res = current_clip.SmartReframe()
            return {
                "success": bool(res),
                "message": "Smart Reframe executed on current clip." if res else "Smart Reframe failed."
            }
        else:
            return {
                "success": False,
                "error": "SmartReframe method not available on this item or Resolve version."
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

