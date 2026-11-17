"""
Project-level DaVinci Resolve MCP Tools for Project JARVIS.
Handles project creation, loading, resolution configuration, and saving.
"""

from typing import Dict, Any, List, Optional
from jarvis.backend.mcp.davinci.connection import connection
from jarvis.backend.mcp.davinci.object_registry import registry


def list_projects() -> Dict[str, Any]:
    """List all available projects in current DaVinci Resolve database folder."""
    resolve, status = connection.connect()
    if not resolve:
        return {
            "success": False,
            "error": "DaVinci Resolve is offline.",
            "status": status,
            "projects": []
        }

    try:
        pm = resolve.GetProjectManager()
        if not pm:
            return {"success": False, "error": "Could not access ProjectManager.", "projects": []}

        projects = pm.GetProjectListInCurrentFolder() or []
        return {
            "success": True,
            "projects": projects,
            "count": len(projects)
        }
    except Exception as e:
        return {"success": False, "error": str(e), "projects": []}


def create_project(name: str, vertical_shorts: bool = True) -> Dict[str, Any]:
    """Create a new project in DaVinci Resolve and optionally set vertical 9:16 Shorts aspect ratio."""
    resolve, status = connection.connect()
    if not resolve:
        return {
            "success": False,
            "error": "DaVinci Resolve is offline.",
            "status": status,
            "fallback_hint": "Use JARVIS FCPXML generator to create an interchange timeline."
        }

    try:
        pm = resolve.GetProjectManager()
        if not pm:
            return {"success": False, "error": "Could not access ProjectManager."}

        project = pm.CreateProject(name)
        if not project:
            # Try loading if it already exists
            project = pm.LoadProject(name)

        if not project:
            return {"success": False, "error": f"Failed to create or load project '{name}'."}

        proj_id = registry.register(project, "Project", {"name": name})

        configured = False
        if vertical_shorts:
            project.SetSetting("timelineResolutionWidth", "1080")
            project.SetSetting("timelineResolutionHeight", "1920")
            project.SetSetting("useCustomTimelineSettings", "1")
            configured = True

        return {
            "success": True,
            "project_id": proj_id,
            "name": name,
            "vertical_shorts": configured,
            "message": f"Project '{name}' created and loaded." + (" Configured for 1080x1920 Shorts." if configured else "")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def load_project(name: str) -> Dict[str, Any]:
    """Load an existing project by name."""
    resolve, status = connection.connect()
    if not resolve:
        return {"success": False, "error": "DaVinci Resolve is offline.", "status": status}

    try:
        pm = resolve.GetProjectManager()
        project = pm.LoadProject(name)
        if not project:
            return {"success": False, "error": f"Failed to load project '{name}'. Check if it exists."}

        proj_id = registry.register(project, "Project", {"name": name})
        return {
            "success": True,
            "project_id": proj_id,
            "name": name,
            "message": f"Project '{name}' loaded successfully."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_project() -> Dict[str, Any]:
    """Save the currently active project."""
    resolve, status = connection.connect()
    if not resolve:
        return {"success": False, "error": "DaVinci Resolve is offline.", "status": status}

    try:
        pm = resolve.GetProjectManager()
        saved = pm.SaveProject()
        return {
            "success": bool(saved),
            "message": "Project saved successfully." if saved else "Failed to save project."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def set_resolution(width: int = 1080, height: int = 1920, project_id: Optional[str] = None) -> Dict[str, Any]:
    """Set project timeline resolution (default 1080x1920 for YouTube Shorts / Reels)."""
    project = None
    if project_id:
        project = registry.get(project_id)

    if not project:
        resolve, status = connection.connect()
        if not resolve:
            return {"success": False, "error": "DaVinci Resolve is offline.", "status": status}
        pm = resolve.GetProjectManager()
        project = pm.GetCurrentProject() if pm else None

    if not project:
        return {"success": False, "error": "No active project found."}

    try:
        project.SetSetting("timelineResolutionWidth", str(width))
        project.SetSetting("timelineResolutionHeight", str(height))
        project.SetSetting("useCustomTimelineSettings", "1")
        return {
            "success": True,
            "width": width,
            "height": height,
            "aspect_ratio": f"{width}:{height}",
            "message": f"Project resolution updated to {width}x{height}."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

